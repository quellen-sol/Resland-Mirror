"""PDF resume parsing — normalizes pdfminer's layout tree into the
`shared.pdfdoc` IR and exposes the same four document views the agent gets
for docx (`doc_parsers/docx.py`): raw text, block sequence, whitespace map,
column counts. `capture_format_profile_pdf` in shared.docgen reads the same
IR to build the resume's FormatProfile."""

import io
from collections import Counter
from typing import Any

from shared.pdfdoc import (
    PdfDoc,
    PdfLine,
    PdfPage,
    PdfStyle,
    column_gutter,
    page_columns,
)

_BOLD_WORDS = ("bold", "black", "heavy", "demi")
_ITALIC_WORDS = ("italic", "oblique", "slanted")
# A rule has to span a third of the page to count as a section divider —
# short strokes (underlines, box edges) stay invisible.
_RULE_MIN_WIDTH_FRAC = 0.3
_RULE_MAX_THICKNESS_PT = 2.0

# A drawn bullet marker (small circle/square) is this big at most.
_DOT_MAX_PT = 6.0
# ...and sits this close, horizontally, to the text it marks.
_DOT_GAP_MAX_PT = 18.0
# Fragments sharing a visual row join into one line; gaps under this get a
# single space, wider gaps get four — so a right-floated date reads as a
# gap, not as inline text.
_ROW_JOIN_GAP_PT = 14.0

# pdfminer.layout, bound lazily: the IR and the view helpers below work
# without the extraction dependency, so a missing/broken install surfaces
# as a parse-time error instead of failing every module that imports this
# one (the agent builder, the runner, and their tests).
_pm_layout = None


def _layout():
    global _pm_layout
    if _pm_layout is None:
        import pdfminer.layout

        _pm_layout = pdfminer.layout
    return _pm_layout


def _strip_subset_prefix(name: str) -> str:
    # Embedded subset fonts look like "ABCDEF+Inter-Bold".
    if len(name) > 7 and name[:6].isupper() and name[6] == "+":
        return name[7:]
    return name


def _font_flags(font_name: str) -> tuple[bool, bool]:
    lower = font_name.lower()
    bold = any(w in lower for w in _BOLD_WORDS)
    italic = any(w in lower for w in _ITALIC_WORDS)
    return bold, italic


def _font_family(font_name: str) -> str:
    """"Inter-Bold" → "Inter"; falls back to the whole name when the style
    isn't separated out (fonts like "Helvetica Neue" keep their full name)."""
    name = _strip_subset_prefix(font_name)
    for sep in ("-", ","):
        if sep in name:
            base = name.split(sep, 1)[0].strip()
            if base:
                return base
    return name


def _color_hex(ncolor: Any) -> str | None:
    """PDF nonstroking color → "RRGGBB". Near-black counts as the default —
    the renderer falls back to black just like Word does."""
    try:
        if isinstance(ncolor, (int, float)):
            rgb = (ncolor,) * 3
        else:
            rgb = tuple(ncolor)[:3]
        vals = [int(round(min(max(float(c), 0.0), 1.0) * 255)) for c in rgb]
    except (TypeError, ValueError):
        return None
    if len(vals) < 3 or all(v < 40 for v in vals):
        return None
    return "".join(f"{v:02X}" for v in vals[:3])


def _iter_text_lines(container):
    lt = _layout()
    for item in container:
        if isinstance(item, lt.LTTextLine):
            yield item
        elif isinstance(item, (lt.LTTextContainer, lt.LTFigure)):
            # pdfminer groups a figure's text into LTTextBoxes only when
            # LAParams.all_texts is set (parse_pdf does); headers, right-
            # floated dates, and contact blocks commonly live in figures.
            yield from _iter_text_lines(item)


def _iter_dots(container):
    """Tiny filled shapes (~3pt circles) — how bullet glyphs are typically
    drawn in generated PDFs. They sit just left of a list line's text."""
    lt = _layout()
    for item in container:
        if isinstance(item, lt.LTFigure):
            yield from _iter_dots(item)
        elif isinstance(item, lt.LTCurve):
            # LTCurve covers LTLine and LTRect too — keep only dot-sized
            # shapes (rules are wide, photo frames are big).
            if (
                item.x1 - item.x0 <= _DOT_MAX_PT
                and item.y1 - item.y0 <= _DOT_MAX_PT
            ):
                yield item


def _iter_rules(container, min_width: float):
    lt = _layout()
    for item in container:
        if isinstance(item, lt.LTFigure):
            yield from _iter_rules(item, min_width)
        elif isinstance(item, lt.LTCurve):
            # LTCurve covers LTLine and LTRect — a wide, flat shape is a
            # divider rule regardless of how it was stroked/filled.
            wide = item.x1 - item.x0 >= min_width
            thin = item.y1 - item.y0 <= _RULE_MAX_THICKNESS_PT
            if wide and thin:
                yield item


def _line_text(line) -> str:
    return "".join(child.get_text() for child in line).strip()


def _line_chars(line) -> list:
    lt = _layout()
    return [c for c in line if isinstance(c, lt.LTChar)]


def _chars_style(chars) -> PdfStyle:
    """Dominant character style — the char style covering the most
    visible glyphs wins."""
    counter: Counter = Counter()
    for char in chars:
        if not char.get_text().strip():
            continue
        color = _color_hex(getattr(char.graphicstate, "ncolor", None))
        key = (
            _strip_subset_prefix(char.fontname),
            round(char.size, 1),
            color,
        )
        counter[key] += 1
    if not counter:
        return PdfStyle()
    (font_name, size, color), _ = counter.most_common(1)[0]
    bold, italic = _font_flags(font_name)
    return PdfStyle(
        font_name=_font_family(font_name),
        size_pt=size,
        bold=bold,
        italic=italic,
        color=color,
    )


class _Frag:
    """One extracted text fragment (an LTTextLine), in top-down coords."""

    __slots__ = ("x0", "x1", "top", "bottom", "text", "chars")

    def __init__(self, item, page_height: float):
        self.x0 = item.x0
        self.x1 = item.x1
        self.top = page_height - item.y1
        self.bottom = page_height - item.y0
        self.text = _line_text(item)
        self.chars = _line_chars(item)

    @property
    def empty(self) -> bool:
        return not self.text.strip()

    @property
    def cy(self) -> float:
        return (self.top + self.bottom) / 2

    @property
    def height(self) -> float:
        return self.bottom - self.top


def _row_rows(frags: list[_Frag]) -> list[list[_Frag]]:
    """Group fragments that share a visual row — a title and its
    right-floated dates, a label and its value — first-fit against each
    row's running center. Fragments arrive sorted by center, so rows whose
    center is already further above than any row could reach are retired
    instead of rescanned."""
    rows: list[list[_Frag]] = []
    centers: list[float] = []
    heights: list[float] = []
    if not frags:
        return rows
    # Upper bound of the per-pair tolerance below.
    reach = max(2.5, max(max(f.height for f in frags), 1.0) * 0.45)
    start = 0
    for frag in sorted(frags, key=lambda f: (f.cy, f.x0)):
        while start < len(rows) and centers[start] < frag.cy - reach:
            start += 1
        for i in range(start, len(rows)):
            h = max(heights[i], frag.height, 1.0)
            if abs(frag.cy - centers[i]) <= max(2.5, h * 0.45):
                rows[i].append(frag)
                n = len(rows[i])
                centers[i] = (centers[i] * (n - 1) + frag.cy) / n
                heights[i] = max(heights[i], frag.height)
                break
        else:
            rows.append([frag])
            centers.append(frag.cy)
            heights.append(frag.height)
    return rows


def _attach_dot(frag: _Frag, dots: list[tuple[float, float, float]]) -> None:
    """A bullet dot just left of the text becomes the line's '• ' glyph
    prefix — the pdf analogue of a literal list marker in docx text.
    `dots` are (x0, x1, cy) triples in top-down coords."""
    for dot in dots:
        if (
            dot[1] <= frag.x0 + 1
            and frag.x0 - dot[1] <= _DOT_GAP_MAX_PT
            and abs(dot[2] - frag.cy) <= 3.0
        ):
            frag.text = "• " + frag.text
            frag.x0 = min(frag.x0, dot[0])
            dots.remove(dot)
            return


def _merge_row(page_number: int, frags: list[_Frag]) -> PdfLine | None:
    """Join a row's fragments left-to-right into one PdfLine — the pdf
    analogue of a docx paragraph whose runs span the line."""
    frags = [f for f in sorted(frags, key=lambda f: f.x0) if not f.empty]
    if not frags:
        return None
    parts: list[str] = []
    chars: list = []
    prev_x1: float | None = None
    for frag in frags:
        if prev_x1 is not None:
            gap = frag.x0 - prev_x1
            parts.append("    " if gap >= _ROW_JOIN_GAP_PT else " ")
        parts.append(frag.text)
        chars.extend(frag.chars)
        prev_x1 = frag.x1
    return PdfLine(
        text="".join(parts).strip(),
        page=page_number,
        x0=round(min(f.x0 for f in frags), 1),
        x1=round(max(f.x1 for f in frags), 1),
        top=round(min(f.top for f in frags), 1),
        bottom=round(max(f.bottom for f in frags), 1),
        style=_chars_style(chars),
    )


def parse_pdf(file_data: bytes) -> PdfDoc:
    from pdfminer.high_level import extract_pages

    lt = _layout()
    doc = PdfDoc()
    for page_layout in extract_pages(
        io.BytesIO(file_data), laparams=lt.LAParams(all_texts=True)
    ):
        page = PdfPage(
            number=len(doc.pages), width=page_layout.width, height=page_layout.height
        )
        frags = [
            _Frag(item, page.height)
            for item in _iter_text_lines(page_layout)
        ]
        dots = [
            (
                d.x0,
                d.x1,
                page.height - (d.y0 + d.y1) / 2,
            )
            for d in _iter_dots(page_layout)
        ]
        for frag in frags:
            if not frag.empty:
                _attach_dot(frag, dots)
        # Merge fragments that share a visual row. On a genuine two-column
        # page the columns stay separate; everywhere else a title and its
        # right-floated dates (or a label and its value) read as one line.
        gutter = column_gutter(list(frags))
        merged: list[PdfLine] = []
        for row in _row_rows(frags):
            if gutter is None:
                line = _merge_row(page.number, row)
                if line is not None:
                    merged.append(line)
                continue
            left = [f for f in row if (f.x0 + f.x1) / 2 < gutter]
            right = [f for f in row if (f.x0 + f.x1) / 2 >= gutter]
            for band in (left, right):
                line = _merge_row(page.number, band) if band else None
                if line is not None:
                    merged.append(line)
        if gutter is None:
            page.lines = sorted(merged, key=lambda l: (l.top, l.x0))
        else:
            # Column-major order keeps each column's sections contiguous.
            page.lines = [
                *sorted(
                    (l for l in merged if (l.x0 + l.x1) / 2 < gutter),
                    key=lambda l: (l.top, l.x0),
                ),
                *sorted(
                    (l for l in merged if (l.x0 + l.x1) / 2 >= gutter),
                    key=lambda l: (l.top, l.x0),
                ),
            ]
        prev: PdfLine | None = None
        for line in page.lines:
            if prev is not None:
                line.gap_before_pt = max(0.0, round(line.top - prev.bottom, 1))
            prev = line
        if page.lines:
            page.lines[-1].ends_page = True
        min_width = page.width * _RULE_MIN_WIDTH_FRAC
        page.hrules = sorted(
            round(page.height - (rule.y0 + rule.y1) / 2, 1)
            for rule in _iter_rules(page_layout, min_width)
        )
        doc.pages.append(page)
    return doc


def raw_text(doc: PdfDoc) -> str:
    return "\n".join(line.text for line in doc.lines)


def block_sequence(doc: PdfDoc) -> list[dict[str, Any]]:
    """Document blocks in layout order: text lines (with font/size/weight —
    the pdf analogue of docx style names), horizontal rules, and page ends
    flagged on the last line of each page."""
    blocks = []
    for page in doc.pages:
        rules = list(page.hrules)
        for line in page.lines:
            while rules and rules[0] <= line.top:
                rules.pop(0)
                blocks.append({"type": "rule", "page": page.number})
            blocks.append(
                {
                    "type": "line",
                    "page": page.number,
                    "text": line.text,
                    "font_name": line.style.font_name,
                    "size_pt": line.style.size_pt,
                    "bold": line.style.bold,
                    "italic": line.style.italic,
                    "ends_page": line.ends_page,
                }
            )
        for _ in rules:
            blocks.append({"type": "rule", "page": page.number})
    return blocks


def whitespace_map(doc: PdfDoc) -> list[dict[str, Any]]:
    """Per line index, in document order: whether it's empty and the vertical
    gap above it in points. Large gaps mark the visual boundaries between
    resume sections."""
    return [
        {
            "index": i,
            "page": line.page,
            "empty": line.empty,
            "gap_before_pt": line.gap_before_pt,
        }
        for i, line in enumerate(doc.lines)
    ]


def column_counts(doc: PdfDoc) -> list[int]:
    """Number of text columns per page. A value greater than 1 means the page
    uses a multi-column layout (common in resumes with sidebars)."""
    return [page_columns(page) for page in doc.pages]
