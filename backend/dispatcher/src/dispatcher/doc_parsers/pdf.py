"""PDF resume parsing — normalizes pdfminer's layout tree into the
`shared.pdfdoc` IR and exposes the same four document views the agent gets
for docx (`doc_parsers/docx.py`): raw text, block sequence, whitespace map,
column counts. `capture_format_profile_pdf` in shared.docgen reads the same
IR to build the resume's FormatProfile."""

import bisect
import io
import re
from collections import Counter
from typing import Any

from shared.pdfdoc import (
    PdfDoc,
    PdfLine,
    PdfPage,
    PdfRun,
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

# A drawn bullet marker is a small, roughly square shape (a ~3pt circle or
# square) — icons are bigger or oddly proportioned, specks are smaller.
_DOT_MIN_PT = 1.0
_DOT_MAX_PT = 6.0
_DOT_MAX_ASPECT = 1.5
# ...and sits this close, horizontally, to the text it marks.
_DOT_GAP_MAX_PT = 18.0
# Bullets of one list share an x position (within this) and follow each
# other down the page; a dot this many line heights below the previous one
# starts a new list.
_DOT_SAME_X_PT = 2.0
_DOT_LIST_GAP_LINES = 4.0
# A lone dot (a one-bullet list) counts only before sentence-length text;
# a lone icon sits beside a short field ("Denver, CO").
_LONE_BULLET_CHARS = 30
# Fragments sharing a visual row join into one line; gaps under this get a
# single space, wider gaps get four — so a right-floated date reads as a
# gap, not as inline text.
_ROW_JOIN_GAP_PT = 14.0
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE = re.compile(r"^\+?[\d\s().\-/]{7,}$")
_URL = re.compile(
    r"^(?:https?://|www\.)\S+$|^[\w.-]+\.(?:com|io|dev|me|org|net|co|app|ai|xyz)(?:/\S*)?$",
    re.IGNORECASE,
)
_LEADING_LABEL = re.compile(r"^[A-Za-z][A-Za-z ]{0,15}:\s*")
# WinAnsiEncoding maps unused codes (e.g. 127, which some generators emit
# for "•") to the bullet; pdfminer leaves them as "(cid:127)".
_WINANSI_BULLET_CID = "(cid:127)"

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
    # "ProximaNova-RegularIt", "SourceSans-BoldIt": the style suffix ends
    # in "It" instead of spelling out "Italic".
    style = re.split(r"[-,]", lower)[-1] if re.search(r"[-,]", lower) else ""
    italic = any(w in lower for w in _ITALIC_WORDS) or style.endswith("it")
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
        vals = [round(min(max(float(c), 0.0), 1.0) * 255) for c in rgb]
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


def _dot_glyph(item) -> str | None:
    """The list marker a small shape stands for, or None when the shape
    isn't dot-like (lines, slivers, icons bigger than a bullet)."""
    lt = _layout()
    if isinstance(item, lt.LTLine):
        return None
    w, h = item.x1 - item.x0, item.y1 - item.y0
    if not (_DOT_MIN_PT <= w <= _DOT_MAX_PT and _DOT_MIN_PT <= h <= _DOT_MAX_PT):
        return None
    if max(w, h) / min(w, h) > _DOT_MAX_ASPECT:
        return None
    path = getattr(item, "original_path", None) or []
    straight = isinstance(item, lt.LTRect) or (
        bool(path) and all(seg[0] in ("m", "l", "h") for seg in path)
    )
    if getattr(item, "fill", True):
        return "▪" if straight else "•"
    if getattr(item, "stroke", False):
        # Outline-only shapes: hollow bullets.
        return "□" if straight else "○"
    return None



def _iter_dots(container):
    """Small dot-like shapes — how bullet glyphs are typically drawn in
    generated PDFs — as (shape, glyph) pairs."""
    lt = _layout()
    for item in container:
        if isinstance(item, lt.LTFigure):
            yield from _iter_dots(item)
        elif isinstance(item, lt.LTCurve):
            glyph = _dot_glyph(item)
            if glyph is not None:
                yield item, glyph



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


def _char_key(char) -> tuple:
    return (
        _strip_subset_prefix(char.fontname),
        round(char.size, 1),
        _color_hex(getattr(char.graphicstate, "ncolor", None)),
    )



def _key_style(key: tuple | None) -> PdfStyle:
    if key is None:
        return PdfStyle()
    font_name, size, color = key
    bold, italic = _font_flags(font_name)
    return PdfStyle(
        font_name=_font_family(font_name),
        size_pt=size,
        bold=bold,
        italic=italic,
        color=color,
    )



def _pieces(item) -> list[list]:
    """An LTTextLine's text split into same-style stretches:
    [text, style key, x0, visible glyph count]. Inserted spaces join the
    stretch before them; outer whitespace is stripped like the line text."""
    lt = _layout()
    pieces: list[list] = []
    for child in item:
        text = child.get_text()
        if text == _WINANSI_BULLET_CID:
            text = "•"
        if isinstance(child, lt.LTChar) and text.strip():
            key = _char_key(child)
            if pieces and pieces[-1][1] == key:
                pieces[-1][0] += text
                pieces[-1][3] += 1
            else:
                pieces.append([text, key, child.x0, 1])
        elif pieces:
            pieces[-1][0] += text
    if pieces:
        pieces[0][0] = pieces[0][0].lstrip()
        pieces[-1][0] = pieces[-1][0].rstrip()
    return pieces



class _Frag:
    """One extracted text fragment (an LTTextLine), in top-down coords."""

    __slots__ = ("bottom", "pieces", "text", "top", "x0", "x1")

    def __init__(self, item, page_height: float):
        self.x0 = item.x0
        self.x1 = item.x1
        self.top = page_height - item.y1
        self.bottom = page_height - item.y0
        self.pieces = _pieces(item)
        self.text = "".join(p[0] for p in self.pieces)

    @property
    def empty(self) -> bool:
        return not self.text.strip()

    @property
    def cy(self) -> float:
        return (self.top + self.bottom) / 2

    @property
    def height(self) -> float:
        return self.bottom - self.top

    def prefix(self, glyph: str, x0: float) -> None:
        self.text = f"{glyph} {self.text}"
        if self.pieces:
            self.pieces[0][0] = f"{glyph} {self.pieces[0][0]}"
        self.x0 = min(self.x0, x0)



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


# ---------- drawn bullets ----------


class _Dot:
    __slots__ = ("cy", "frag", "glyph", "page", "x0", "x1")

    def __init__(self, item, glyph: str, page_height: float, page: int):
        self.x0 = item.x0
        self.x1 = item.x1
        self.cy = page_height - (item.y0 + item.y1) / 2
        self.glyph = glyph
        self.page = page
        self.frag: _Frag | None = None



def _contact_like(text: str) -> bool:
    """An email, phone number, or bare URL/handle — what icons sit next to
    in a contact block, never what a bullet list holds."""
    body = _LEADING_LABEL.sub("", text.strip())
    if _EMAIL.search(body):
        return True
    if _PHONE.match(body) and sum(c.isdigit() for c in body) >= 7:
        return True
    return bool(_URL.match(body))



def _match_dots(dots: list[_Dot], frags: list[_Frag]) -> None:
    """Pair each dot with the fragment that starts just right of it on the
    same visual line — at most one dot per fragment, the closest wins."""
    by_cy = sorted(frags, key=lambda f: f.cy)
    centers = [f.cy for f in by_cy]
    reach = max((f.height for f in frags), default=0.0)
    best: dict[int, tuple[float, _Dot]] = {}
    for dot in dots:
        lo = bisect.bisect_left(centers, dot.cy - reach)
        hi = bisect.bisect_right(centers, dot.cy + reach)
        choice: tuple[float, _Frag] | None = None
        for frag in by_cy[lo:hi]:
            gap = frag.x0 - dot.x1
            if gap < -1 or gap > _DOT_GAP_MAX_PT:
                continue
            if abs(dot.cy - frag.cy) > max(2.0, frag.height * 0.35):
                continue
            if choice is None or gap < choice[0]:
                choice = (gap, frag)
        if choice is None:
            continue
        gap, frag = choice
        held = best.get(id(frag))
        if held is None or gap < held[0]:
            if held is not None:
                held[1].frag = None
            dot.frag = frag
            best[id(frag)] = (gap, dot)



def _attach_bullets(dots: list[_Dot]) -> None:
    """Turn drawn bullet dots into glyph prefixes ("• ", "▪ ", "○ ") — the
    pdf analogue of a literal list marker in docx text. Icons beside contact lines look
    exactly like bullets geometrically, so a dot only counts when it marks
    a list: its run of same-x dots down the page holds at least two lines
    that are mostly not contact info (email/phone/link), or — a one-item
    list — it marks a sentence-length line. Contact-info lines never get a
    bullet."""
    matched = sorted(
        (d for d in dots if d.frag is not None), key=lambda d: d.x0
    )
    groups: list[list[_Dot]] = []
    for dot in matched:
        if groups and dot.x0 - groups[-1][0].x0 <= _DOT_SAME_X_PT:
            groups[-1].append(dot)
        else:
            groups.append([dot])
    for group in groups:
        group.sort(key=lambda d: (d.page, d.cy))
        clusters: list[list[_Dot]] = []
        for dot in group:
            prev = clusters[-1][-1] if clusters else None
            if (
                prev is not None
                and prev.page == dot.page
                and dot.cy - prev.cy
                <= _DOT_LIST_GAP_LINES * max(prev.frag.height, dot.frag.height)
            ):
                clusters[-1].append(dot)
            else:
                clusters.append([dot])
        for cluster in clusters:
            if len(cluster) < 2 and len(cluster[0].frag.text) < _LONE_BULLET_CHARS:
                continue
            contact = sum(_contact_like(d.frag.text) for d in cluster)
            if contact * 2 >= len(cluster):
                continue
            for dot in cluster:
                if not _contact_like(dot.frag.text):
                    dot.frag.prefix(dot.glyph, dot.x0)



def _merge_row(page_number: int, frags: list[_Frag]) -> PdfLine | None:
    """Join a row's fragments left-to-right into one PdfLine — the pdf
    analogue of a docx paragraph whose runs span the line."""
    frags = [f for f in sorted(frags, key=lambda f: f.x0) if not f.empty]
    if not frags:
        return None
    runs: list[list] = []
    glyphs: Counter = Counter()
    prev_x1: float | None = None
    for frag in frags:
        if prev_x1 is not None and runs:
            gap = frag.x0 - prev_x1
            runs[-1][0] += "    " if gap >= _ROW_JOIN_GAP_PT else " "
        for i, (text, key, x0, count) in enumerate(frag.pieces):
            glyphs[key] += count
            # Fragment boundaries stay run boundaries so each run keeps
            # its own x position.
            if i and runs and runs[-1][1] == key:
                runs[-1][0] += text
            else:
                runs.append([text, key, frag.x0 if i == 0 else x0])
        prev_x1 = frag.x1
    dominant = glyphs.most_common(1)[0][0] if glyphs else None
    return PdfLine(
        text="".join(run[0] for run in runs),
        page=page_number,
        x0=round(min(f.x0 for f in frags), 1),
        x1=round(max(f.x1 for f in frags), 1),
        top=round(min(f.top for f in frags), 1),
        bottom=round(max(f.bottom for f in frags), 1),
        style=_key_style(dominant),
        runs=[
            PdfRun(text=text, style=_key_style(key), x0=round(x0, 1))
            for text, key, x0 in runs
        ],
    )



def parse_pdf(file_data: bytes) -> PdfDoc:
    from pdfminer.high_level import extract_pages

    lt = _layout()
    doc = PdfDoc()
    staged: list[tuple[PdfPage, list[_Frag]]] = []
    dots: list[_Dot] = []
    for page_layout in extract_pages(
        io.BytesIO(file_data), laparams=lt.LAParams(all_texts=True)
    ):
        page = PdfPage(
            number=len(staged), width=page_layout.width, height=page_layout.height
        )
        frags = [
            frag
            for frag in (
                _Frag(item, page.height) for item in _iter_text_lines(page_layout)
            )
            if not frag.empty
        ]
        page_dots = [
            _Dot(item, glyph, page.height, page.number)
            for item, glyph in _iter_dots(page_layout)
        ]
        _match_dots(page_dots, frags)
        dots.extend(page_dots)
        min_width = page.width * _RULE_MIN_WIDTH_FRAC
        page.hrules = sorted(
            round(page.height - (rule.y0 + rule.y1) / 2, 1)
            for rule in _iter_rules(page_layout, min_width)
        )
        staged.append((page, frags))
    # Bullet lists are recognized document-wide (a list continued on the
    # next page shares its x with the first page's).
    _attach_bullets(dots)
    for page, frags in staged:
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
