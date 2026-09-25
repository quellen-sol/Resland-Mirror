"""PDF resume parsing — normalizes pdfminer's layout tree into the
`shared.pdfdoc` IR and exposes the same four document views the agent gets
for docx (`doc_parsers/docx.py`): raw text, block sequence, whitespace map,
column counts. `capture_format_profile_pdf` in shared.docgen reads the same
IR to build the resume's FormatProfile."""

import io
from collections import Counter
from typing import Any

from shared.pdfdoc import PdfDoc, PdfLine, PdfPage, PdfStyle, page_columns

_BOLD_WORDS = ("bold", "black", "heavy", "demi")
_ITALIC_WORDS = ("italic", "oblique", "slanted")
# A rule has to span a third of the page to count as a section divider —
# short strokes (underlines, box edges) stay invisible.
_RULE_MIN_WIDTH_FRAC = 0.3
_RULE_MAX_THICKNESS_PT = 2.0

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
        elif isinstance(item, lt.LTTextContainer):
            yield from _iter_text_lines(item)


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


def _line_style(line) -> PdfStyle:
    """Dominant character style of the line — the char style covering the
    most visible glyphs wins."""
    lt = _layout()
    counter: Counter = Counter()
    for child in line:
        if isinstance(child, lt.LTChar) and child.get_text().strip():
            color = _color_hex(getattr(child.graphicstate, "ncolor", None))
            key = (
                _strip_subset_prefix(child.fontname),
                round(child.size, 1),
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


def parse_pdf(file_data: bytes) -> PdfDoc:
    from pdfminer.high_level import extract_pages

    lt = _layout()
    doc = PdfDoc()
    for page_layout in extract_pages(io.BytesIO(file_data), laparams=lt.LAParams()):
        page = PdfPage(
            number=len(doc.pages), width=page_layout.width, height=page_layout.height
        )
        for item in _iter_text_lines(page_layout):
            top = page.height - item.y1
            page.lines.append(
                PdfLine(
                    text=_line_text(item),
                    page=page.number,
                    x0=round(item.x0, 1),
                    x1=round(item.x1, 1),
                    top=round(top, 1),
                    bottom=round(top + (item.y1 - item.y0), 1),
                    style=_line_style(item),
                )
            )
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
