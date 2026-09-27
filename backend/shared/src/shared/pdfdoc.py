"""Intermediate representation of a parsed PDF resume.

Producer: dispatcher's `doc_parsers/pdf.py` (pdfminer-based) normalizes raw
PDF layout into these dataclasses. Consumers: the resume-parse agent's views
(raw text, block sequence, whitespace map, column counts) and
`docgen.capture_format_profile_pdf`, which turns this layout into the same
`FormatProfile` the docx capturer produces.
"""

from dataclasses import dataclass, field


@dataclass
class PdfStyle:
    """Dominant character style of a line — resolved like the docx
    capturer's run/style merge, except every value is concrete because
    PDFs carry no inherited styles."""

    font_name: str | None = None  # subset-embedded prefix ("ABCDEF+") stripped
    size_pt: float | None = None
    bold: bool = False
    italic: bool = False
    color: str | None = None  # "RRGGBB", None when near-black/default


@dataclass
class PdfLine:
    """One visually-contiguous text line. `top`/`bottom` are distances from
    the page's top edge in points (PDF origin is bottom-left; these are
    already flipped for top-down reasoning)."""

    text: str
    page: int  # 0-based page index
    x0: float  # left edge, pt from page left
    x1: float  # right edge
    top: float  # pt below page top
    bottom: float  # pt below page top (top + line height)
    style: PdfStyle
    gap_before_pt: float = 0.0  # vertical gap above this line on the same page
    ends_page: bool = False

    @property
    def empty(self) -> bool:
        return not self.text.strip()


@dataclass
class PdfPage:
    number: int
    width: float
    height: float
    lines: list[PdfLine] = field(default_factory=list)
    # `top` positions of detected horizontal rules (divider lines under
    # section headers are common in resumes) — they aren't text lines.
    hrules: list[float] = field(default_factory=list)


@dataclass
class PdfDoc:
    pages: list[PdfPage] = field(default_factory=list)

    @property
    def lines(self) -> list[PdfLine]:
        """All lines across pages in document order — the pdf analogue of
        `doc.paragraphs` for layout-driven capture."""
        return [line for page in self.pages for line in page.lines]


def column_gutter(lines: list[PdfLine]) -> float | None:
    """x position of a real second column's left edge, or None when the
    lines form a single-column page. A second column exists when a
    substantial group of lines starts right of where the bulk of lines end —
    a gutter of white space no text crosses. Right-aligned dates share the
    main column's right edge, so they don't count as a column, and neither
    does a localized two-column grid (e.g. a skills block) on an otherwise
    single-column page — both columns must run for a real vertical stretch."""
    non_empty = [line for line in lines if not line.empty]
    if len(non_empty) < 6:
        return None
    lefts = sorted(line.x0 for line in non_empty)
    gutter = lefts[int(len(lefts) * 0.75)]
    left_col = [line for line in non_empty if line.x1 <= gutter - 12]
    right_col = [line for line in non_empty if line.x0 >= gutter - 4]
    if len(left_col) < max(3, len(non_empty) * 0.25) or len(right_col) < max(
        3, len(non_empty) * 0.25
    ):
        return None
    span = max(line.bottom for line in non_empty) - min(
        line.top for line in non_empty
    )
    for col in (left_col, right_col):
        col_span = max(line.bottom for line in col) - min(
            line.top for line in col
        )
        if span > 0 and col_span < span * 0.35:
            return None
    return gutter


def page_columns(page: PdfPage) -> int:
    """Estimated text-column count for a page (see column_gutter)."""
    return 2 if column_gutter(page.lines) is not None else 1
