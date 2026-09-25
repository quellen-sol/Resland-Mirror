"""Resume docx regeneration.

Two halves, both pure python:

- capture: `capture_format_profile(doc, profile)` inspects the user's
  uploaded document plus the already-parsed profile and produces a
  JSON-serializable `FormatProfile` — fonts, sizes, spacing, margins,
  section order/titles, bullet style. Stored in the database, it's what
  makes a generated resume look like the user's own layout.

- render: `render_docx(content, format)` rebuilds a .docx from a
  canonical `ResumeContent` (built from the base profile, or later from a
  tailor run) through a `FormatProfile`.

Nothing here knows where content came from: a docx capturer today, a pdf
capturer later (#10) feeds the same FormatProfile and renderer.
"""

import hashlib
import io
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from docx import Document
from docx.document import Document as _Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.text.paragraph import Paragraph

from .pdfdoc import PdfDoc, PdfLine, page_columns

FORMAT_PROFILE_VERSION = 1

# Roles a FormatProfile carries a style for. `dates`/`contact` reuse
# `entry_sub`/`body` styles when not captured.
ROLE_NAME = "name"
ROLE_CONTACT = "contact"
ROLE_SECTION_HEADER = "section_header"
ROLE_ENTRY_TITLE = "entry_title"
ROLE_ENTRY_SUB = "entry_sub"
ROLE_BODY = "body"
ROLE_BULLET = "bullet"
ALL_ROLES = (
    ROLE_NAME,
    ROLE_CONTACT,
    ROLE_SECTION_HEADER,
    ROLE_ENTRY_TITLE,
    ROLE_ENTRY_SUB,
    ROLE_BODY,
    ROLE_BULLET,
)

# Logical sections a resume can have, in model order.
SECTION_SUMMARY = "summary"
SECTION_EXPERIENCE = "experience"
SECTION_SKILLS = "skills"
SECTION_EDUCATION = "education"
SECTION_PROJECTS = "projects"
ALL_SECTIONS = (
    SECTION_SUMMARY,
    SECTION_EXPERIENCE,
    SECTION_SKILLS,
    SECTION_EDUCATION,
    SECTION_PROJECTS,
)

DEFAULT_SECTION_TITLES = {
    SECTION_SUMMARY: "SUMMARY",
    SECTION_EXPERIENCE: "EXPERIENCE",
    SECTION_SKILLS: "SKILLS",
    SECTION_EDUCATION: "EDUCATION",
    SECTION_PROJECTS: "PROJECTS",
}

SKILLS_LAYOUT_GROUPED = "grouped"
SKILLS_LAYOUT_FLAT = "flat"

_ALIGNMENTS = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


@dataclass
class RoleStyle:
    font_name: str | None = None
    size_pt: float | None = None
    bold: bool = False
    italic: bool = False
    color: str | None = None  # "RRGGBB"
    alignment: str | None = None  # left|center|right|justify
    space_before_pt: float = 0.0
    space_after_pt: float = 0.0
    line_spacing: float | None = None


@dataclass
class FormatProfile:
    version: int = FORMAT_PROFILE_VERSION
    page_margins_in: dict[str, float] = field(
        default_factory=lambda: {"top": 1.0, "right": 1.0, "bottom": 1.0, "left": 1.0}
    )
    columns: int = 1
    contact_separator: str = "|"
    dates_on_title_line: bool = True
    bullet_glyph: str | None = "•"
    bullet_left_indent_in: float | None = None
    skills_layout: str = SKILLS_LAYOUT_FLAT
    section_order: list[str] = field(default_factory=lambda: list(ALL_SECTIONS))
    section_titles: dict[str, str] = field(
        default_factory=lambda: dict(DEFAULT_SECTION_TITLES)
    )
    roles: dict[str, RoleStyle] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "FormatProfile":
        data = dict(data)
        data["roles"] = {
            role: RoleStyle(**style) for role, style in data.get("roles", {}).items()
        }
        return FormatProfile(**data)

    @staticmethod
    def from_json(payload: str) -> "FormatProfile":
        return FormatProfile.from_dict(json.loads(payload))

    def role(self, name: str) -> RoleStyle:
        return self.roles.get(name) or RoleStyle()


# Canonical content — the shape every resume source (base profile today,
# tailor run / pdf later) is normalized into before rendering.


@dataclass
class ResumeHeader:
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: list[str] = field(default_factory=list)


@dataclass
class ResumeExperience:
    company: str
    title: str
    start_date: str
    end_date: str | None
    bullets: list[str] = field(default_factory=list)


@dataclass
class ResumeSkillGroup:
    category: str | None
    skills: list[str]


@dataclass
class ResumeEducation:
    institution: str
    degree: str
    field_of_study: str
    start_date: str
    end_date: str | None
    description: str | None = None


@dataclass
class ResumeProject:
    name: str
    link: str | None
    description: str | None
    start_date: str
    end_date: str | None


@dataclass
class ResumeContent:
    header: ResumeHeader = field(default_factory=ResumeHeader)
    summary: str | None = None
    experiences: list[ResumeExperience] = field(default_factory=list)
    skill_groups: list[ResumeSkillGroup] = field(default_factory=list)
    education: list[ResumeEducation] = field(default_factory=list)
    projects: list[ResumeProject] = field(default_factory=list)
    # What produced this content, e.g. "base" or "tailor_run:<id>" —
    # participates in the staleness hash.
    source: str = "base"


def content_source_hash(content: ResumeContent, template: str = "original") -> str:
    """Stable hash of what the generated docx depends on. Recomputed at
    export time; a mismatch with the stored hash means regenerate."""
    payload = json.dumps(
        {
            "template": template,
            "format_version": FORMAT_PROFILE_VERSION,
            "content": asdict(content),
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def default_format_profile() -> FormatProfile:
    return FormatProfile(
        roles={
            ROLE_NAME: RoleStyle(font_name="Calibri", size_pt=22, bold=True),
            ROLE_CONTACT: RoleStyle(font_name="Calibri", size_pt=10),
            ROLE_SECTION_HEADER: RoleStyle(
                font_name="Calibri", size_pt=12, bold=True, space_before_pt=10
            ),
            ROLE_ENTRY_TITLE: RoleStyle(font_name="Calibri", size_pt=11, bold=True),
            ROLE_ENTRY_SUB: RoleStyle(font_name="Calibri", size_pt=10, italic=True),
            ROLE_BODY: RoleStyle(font_name="Calibri", size_pt=11),
            ROLE_BULLET: RoleStyle(font_name="Calibri", size_pt=11),
        }
    )


# ---------- capture ----------


def _norm(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def _pt_or_zero(value) -> float:
    return round(value.pt, 1) if value is not None else 0.0


def _first_text_run(para: Paragraph):
    for run in para.runs:
        if run.text.strip():
            return run
    return para.runs[0] if para.runs else None


def _para_style(para: Paragraph) -> RoleStyle:
    """Resolve a paragraph's effective look: direct run props fall back to
    the paragraph style. Unknown values stay None — the renderer then falls
    back to the document default like Word does."""
    run = _first_text_run(para)
    style = para.style
    style_font = style.font if style is not None else None

    def _pick(run_val, style_val):
        return run_val if run_val is not None else style_val

    font_name = _pick(run.font.name if run else None, getattr(style_font, "name", None))
    size = _pick(run.font.size if run else None, getattr(style_font, "size", None))
    bold = _pick(run.font.bold if run else None, getattr(style_font, "bold", None))
    italic = _pick(
        run.font.italic if run else None, getattr(style_font, "italic", None)
    )
    color_rgb = _pick(
        run.font.color.rgb if run and run.font.color is not None else None,
        getattr(getattr(style_font, "color", None), "rgb", None),
    )

    alignment = para.alignment
    if alignment is None and style is not None:
        alignment = getattr(style, "alignment", None)

    pf = para.paragraph_format
    return RoleStyle(
        font_name=font_name,
        size_pt=round(size.pt, 1) if size is not None else None,
        bold=bool(bold) if bold is not None else False,
        italic=bool(italic) if italic is not None else False,
        color=str(color_rgb) if color_rgb is not None else None,
        alignment=alignment.name.lower() if alignment is not None else None,
        space_before_pt=_pt_or_zero(pf.space_before),
        space_after_pt=_pt_or_zero(pf.space_after),
        line_spacing=pf.line_spacing if isinstance(pf.line_spacing, float) else None,
    )


def _match_idx(paras: list[Paragraph], needle: str | None) -> int | None:
    """First paragraph whose text contains `needle` (normalized)."""
    target = _norm(needle)
    if not target:
        return None
    for i, para in enumerate(paras):
        if target in _norm(para.text):
            return i
    return None


def _match_any_idx(paras: list[Paragraph], needles: list[str | None]) -> int | None:
    hits = [_match_idx(paras, n) for n in needles if n]
    hits = [h for h in hits if h is not None]
    return min(hits) if hits else None


def _section_header_idx(
    paras: list[Paragraph], content_idx: int, claimed: set[int]
) -> int | None:
    """Nearest short, non-empty paragraph right above a section's first
    matched content — treated as that section's header line."""
    j = content_idx - 1
    while j >= 0 and content_idx - j <= 6:
        text = paras[j].text.strip()
        if text and len(text) <= 48 and j not in claimed:
            return j
        if text:
            # Hit another section's content — stop looking.
            return None
        j -= 1
    return None


def capture_format_profile(doc: _Document, profile: Any) -> FormatProfile:
    """Inspect the source document and produce a FormatProfile. `profile`
    is the parsed resume (duck-typed like the parser's UserDocxProfile):
    its values locate which paragraphs carry each role, so capture works
    on layout instead of text guesses."""
    paras = list(doc.paragraphs)
    roles: dict[str, RoleStyle] = {}
    section_titles: dict[str, str] = {}

    basic = profile.basic_info
    name_idx = _match_idx(paras, basic.name)
    if name_idx is None:
        name_idx = next((i for i, p in enumerate(paras) if p.text.strip()), None)
    contact_idx = _match_any_idx(paras, [basic.email, basic.phone])

    # First content paragraph per section — used for header detection,
    # section order, and role capture.
    summary_idx = _match_idx(paras, (profile.summary or "")[:48])
    exp_idx = [
        i
        for i in (
            _match_idx(paras, e.position) or _match_idx(paras, e.company)
            for e in profile.experience
        )
        if i is not None
    ]
    skill_idx = [
        i
        for i in (
            _match_idx(paras, s)
            for cat in profile.skills
            for s in cat.skills[:2]
        )
        if i is not None
    ]
    edu_idx = [
        i
        for i in (
            _match_idx(paras, e.institution) or _match_idx(paras, e.degree)
            for e in profile.education
        )
        if i is not None
    ]
    proj_idx = [
        i
        for i in (_match_idx(paras, p.name) for p in profile.projects)
        if i is not None
    ]
    bullet_idx = [
        i
        for i in (
            _match_idx(paras, b.text[:48])
            for e in profile.experience
            for b in e.bullets[:2]
        )
        if i is not None
    ]

    section_first: dict[str, int] = {}
    if summary_idx is not None:
        section_first[SECTION_SUMMARY] = summary_idx
    if exp_idx:
        section_first[SECTION_EXPERIENCE] = min(exp_idx)
    if skill_idx:
        section_first[SECTION_SKILLS] = min(skill_idx)
    if edu_idx:
        section_first[SECTION_EDUCATION] = min(edu_idx)
    if proj_idx:
        section_first[SECTION_PROJECTS] = min(proj_idx)

    # Headers: nearest short line above each section's first content para.
    claimed = {i for i in [name_idx, contact_idx] if i is not None}
    for idxs in (exp_idx, skill_idx, edu_idx, proj_idx, bullet_idx):
        claimed.update(idxs)
    for section, first in section_first.items():
        header_idx = _section_header_idx(paras, first, claimed)
        if header_idx is None:
            continue
        claimed.add(header_idx)
        section_titles[section] = paras[header_idx].text.strip()
        if ROLE_SECTION_HEADER not in roles:
            roles[ROLE_SECTION_HEADER] = _para_style(paras[header_idx])

    section_order = [
        s for s, _ in sorted(section_first.items(), key=lambda kv: kv[1])
    ]
    for section in ALL_SECTIONS:
        if section not in section_order:
            section_order.append(section)
    for section, title in DEFAULT_SECTION_TITLES.items():
        section_titles.setdefault(section, title)

    # Dates on the title line vs their own line — decides entry layout.
    first_exp = profile.experience[0] if profile.experience else None
    dates_on_title_line = True
    if first_exp is not None:
        exp_para_idx = _match_any_idx(
            paras, [first_exp.position, first_exp.company]
        )
        exp_para = paras[exp_para_idx].text if exp_para_idx is not None else ""
        date_bits = _norm(first_exp.start_date)
        dates_on_title_line = bool(
            date_bits and date_bits.split()[0] in _norm(exp_para)
        )

    # Bullet glyph/indent from the first matched bullet paragraph.
    bullet_glyph = None
    bullet_indent_in = None
    if bullet_idx:
        bullet_para = paras[bullet_idx[0]]
        text = bullet_para.text.lstrip()
        literal = re.match(r"^([•·\-\*►‣▪●○])\s", text)
        numpr = bullet_para._p.find(qn("w:pPr"))
        has_numbering = (
            numpr is not None and numpr.find(qn("w:numPr")) is not None
        )
        style_name = bullet_para.style.name if bullet_para.style else ""
        if literal:
            bullet_glyph = literal.group(1)
        elif has_numbering or "list" in style_name.lower():
            bullet_glyph = "•"
        indent = bullet_para.paragraph_format.left_indent
        bullet_indent_in = round(indent.inches, 2) if indent is not None else None

    # Contact separator between the header fields.
    separator = "|"
    if contact_idx is not None:
        contact_text = paras[contact_idx].text
        for candidate in ("|", "•", "·", "-"):
            if f" {candidate} " in contact_text:
                separator = candidate
                break

    # Roles from matched paragraphs (first hit wins per role).
    if name_idx is not None:
        roles.setdefault(ROLE_NAME, _para_style(paras[name_idx]))
    if contact_idx is not None:
        roles.setdefault(ROLE_CONTACT, _para_style(paras[contact_idx]))
    if exp_idx:
        roles.setdefault(ROLE_ENTRY_TITLE, _para_style(paras[exp_idx[0]]))
    if summary_idx is not None:
        roles.setdefault(ROLE_BODY, _para_style(paras[summary_idx]))
    elif edu_idx:
        roles.setdefault(ROLE_BODY, _para_style(paras[edu_idx[0]]))
    if edu_idx:
        roles.setdefault(ROLE_ENTRY_SUB, _para_style(paras[edu_idx[0]]))
    if bullet_idx:
        roles.setdefault(ROLE_BULLET, _para_style(paras[bullet_idx[0]]))

    # Page setup from the first section.
    margins = {"top": 1.0, "right": 1.0, "bottom": 1.0, "left": 1.0}
    columns = 1
    if doc.sections:
        s = doc.sections[0]
        margins = {
            "top": round(s.top_margin.inches, 2),
            "right": round(s.right_margin.inches, 2),
            "bottom": round(s.bottom_margin.inches, 2),
            "left": round(s.left_margin.inches, 2),
        }
        cols = s._sectPr.find(qn("w:cols"))
        num = cols.get(qn("w:num")) if cols is not None else None
        columns = int(num) if num else 1

    skills_layout = (
        SKILLS_LAYOUT_GROUPED if len(profile.skills) > 1 else SKILLS_LAYOUT_FLAT
    )

    captured = FormatProfile(
        page_margins_in=margins,
        columns=columns,
        contact_separator=separator,
        dates_on_title_line=dates_on_title_line,
        bullet_glyph=bullet_glyph,
        bullet_left_indent_in=bullet_indent_in,
        skills_layout=skills_layout,
        section_order=section_order,
        section_titles=section_titles,
        roles=roles,
    )
    # Any role the doc didn't reveal falls back to the generic defaults so
    # rendering never produces an unstyled paragraph.
    defaults = default_format_profile()
    for role in ALL_ROLES:
        captured.roles.setdefault(role, defaults.roles[role])
    return captured


# ---------- pdf capture ----------
#
# Same pipeline as capture_format_profile, fed by the pdf IR
# (shared.pdfdoc) instead of a python-docx document: lines play the role of
# paragraphs, geometry replaces declared styles/spacing. Wrapped bullets may
# not match their (longer) profile text against single lines — they just
# degrade to defaults like any unmatched docx paragraph does.


def _pdf_content_edges(doc: PdfDoc) -> tuple[float, float]:
    lines = [line for line in doc.lines if not line.empty]
    if not lines:
        return 0.0, 612.0
    return min(line.x0 for line in lines), max(line.x1 for line in lines)


def _pdf_alignment(line: PdfLine, left: float, right: float) -> str | None:
    """Infer alignment from where the line sits in the content column —
    PDFs carry no declared alignment. Plain left is the default → None."""
    width = line.x1 - line.x0
    if width <= 0:
        return None
    center_x = (left + right) / 2
    mid = (line.x0 + line.x1) / 2
    if abs(mid - center_x) <= 12 and width < (right - left) * 0.6:
        return "center"
    if line.x1 >= right - 6 and line.x0 > left + 36:
        return "right"
    return None


def _pdf_line_style(line: PdfLine, left: float, right: float) -> RoleStyle:
    style = line.style
    return RoleStyle(
        font_name=style.font_name,
        size_pt=style.size_pt,
        bold=style.bold,
        italic=style.italic,
        color=style.color,
        alignment=_pdf_alignment(line, left, right),
        # The measured gap above the line is the pdf's effective "space
        # before" — spacing after is indistinguishable, keep zero.
        space_before_pt=line.gap_before_pt,
    )


def _pdf_margins(page, lines) -> dict[str, float]:
    """Content bbox → page margins in inches, clamped to sane values."""
    non_empty = [line for line in lines if not line.empty]
    if page is None or not non_empty:
        return {"top": 1.0, "right": 1.0, "bottom": 1.0, "left": 1.0}

    def _in(pt: float) -> float:
        return round(min(max(pt / 72.0, 0.25), 2.5), 2)

    return {
        "top": _in(min(line.top for line in non_empty)),
        "right": _in(page.width - max(line.x1 for line in non_empty)),
        "bottom": _in(page.height - max(line.bottom for line in non_empty)),
        "left": _in(min(line.x0 for line in non_empty)),
    }


def capture_format_profile_pdf(doc: PdfDoc, profile: Any) -> FormatProfile:
    """PDF analogue of capture_format_profile: locate the profile's content
    in the pdf's line layout and record fonts, spacing, margins, columns,
    section order/titles, and bullet style into a FormatProfile — what makes
    a regenerated resume look like the user's own layout."""
    lines = doc.lines
    roles: dict[str, RoleStyle] = {}
    section_titles: dict[str, str] = {}
    left, right = _pdf_content_edges(doc)

    def _style(line: PdfLine) -> RoleStyle:
        return _pdf_line_style(line, left, right)

    basic = profile.basic_info
    name_idx = _match_idx(lines, basic.name)
    if name_idx is None:
        name_idx = next((i for i, line in enumerate(lines) if not line.empty), None)
    contact_idx = _match_any_idx(lines, [basic.email, basic.phone])

    # First content line per section — used for header detection, section
    # order, and role capture.
    summary_idx = _match_idx(lines, (profile.summary or "")[:48])
    exp_idx = [
        i
        for i in (
            _match_idx(lines, e.position) or _match_idx(lines, e.company)
            for e in profile.experience
        )
        if i is not None
    ]
    skill_idx = [
        i
        for i in (
            _match_idx(lines, s)
            for cat in profile.skills
            for s in cat.skills[:2]
        )
        if i is not None
    ]
    edu_idx = [
        i
        for i in (
            _match_idx(lines, e.institution) or _match_idx(lines, e.degree)
            for e in profile.education
        )
        if i is not None
    ]
    proj_idx = [
        i
        for i in (_match_idx(lines, p.name) for p in profile.projects)
        if i is not None
    ]
    bullet_idx = [
        i
        for i in (
            _match_idx(lines, b.text[:48])
            for e in profile.experience
            for b in e.bullets[:2]
        )
        if i is not None
    ]

    section_first: dict[str, int] = {}
    if summary_idx is not None:
        section_first[SECTION_SUMMARY] = summary_idx
    if exp_idx:
        section_first[SECTION_EXPERIENCE] = min(exp_idx)
    if skill_idx:
        section_first[SECTION_SKILLS] = min(skill_idx)
    if edu_idx:
        section_first[SECTION_EDUCATION] = min(edu_idx)
    if proj_idx:
        section_first[SECTION_PROJECTS] = min(proj_idx)

    # Headers: nearest short line above each section's first content line.
    claimed = {i for i in [name_idx, contact_idx] if i is not None}
    for idxs in (exp_idx, skill_idx, edu_idx, proj_idx, bullet_idx):
        claimed.update(idxs)
    for section, first in section_first.items():
        header_idx = _section_header_idx(lines, first, claimed)
        if header_idx is None:
            continue
        claimed.add(header_idx)
        section_titles[section] = lines[header_idx].text.strip()
        if ROLE_SECTION_HEADER not in roles:
            roles[ROLE_SECTION_HEADER] = _style(lines[header_idx])

    section_order = [
        s for s, _ in sorted(section_first.items(), key=lambda kv: kv[1])
    ]
    for section in ALL_SECTIONS:
        if section not in section_order:
            section_order.append(section)
    for section, title in DEFAULT_SECTION_TITLES.items():
        section_titles.setdefault(section, title)

    # Dates on the title line vs their own line — decides entry layout.
    first_exp = profile.experience[0] if profile.experience else None
    dates_on_title_line = True
    if first_exp is not None:
        exp_line_idx = _match_any_idx(
            lines, [first_exp.position, first_exp.company]
        )
        exp_line = lines[exp_line_idx].text if exp_line_idx is not None else ""
        date_bits = _norm(first_exp.start_date)
        dates_on_title_line = bool(
            date_bits and date_bits.split()[0] in _norm(exp_line)
        )

    # Bullet glyph/indent from the first matched bullet line. PDFs only
    # carry literal glyphs — no list numbering to fall back on.
    bullet_glyph = None
    bullet_indent_in = None
    if bullet_idx:
        bullet_line = lines[bullet_idx[0]]
        literal = re.match(
            r"^([•·\-\*►‣▪●○–])\s", bullet_line.text.lstrip()
        )
        if literal:
            bullet_glyph = literal.group(1)
        if exp_idx:
            indent_pt = bullet_line.x0 - lines[exp_idx[0]].x0
            if indent_pt > 4:
                bullet_indent_in = round(indent_pt / 72.0, 2)

    # Contact separator between the header fields.
    separator = "|"
    if contact_idx is not None:
        contact_text = lines[contact_idx].text
        for candidate in ("|", "•", "·", "-"):
            if f" {candidate} " in contact_text:
                separator = candidate
                break

    # Roles from matched lines (first hit wins per role).
    if name_idx is not None:
        roles.setdefault(ROLE_NAME, _style(lines[name_idx]))
    if contact_idx is not None:
        roles.setdefault(ROLE_CONTACT, _style(lines[contact_idx]))
    if exp_idx:
        roles.setdefault(ROLE_ENTRY_TITLE, _style(lines[exp_idx[0]]))
    if summary_idx is not None:
        roles.setdefault(ROLE_BODY, _style(lines[summary_idx]))
    elif edu_idx:
        roles.setdefault(ROLE_BODY, _style(lines[edu_idx[0]]))
    if edu_idx:
        roles.setdefault(ROLE_ENTRY_SUB, _style(lines[edu_idx[0]]))
    if bullet_idx:
        roles.setdefault(ROLE_BULLET, _style(lines[bullet_idx[0]]))

    # Page setup from the first page.
    page = doc.pages[0] if doc.pages else None
    margins = _pdf_margins(page, lines)
    columns = page_columns(page) if page is not None else 1

    skills_layout = (
        SKILLS_LAYOUT_GROUPED if len(profile.skills) > 1 else SKILLS_LAYOUT_FLAT
    )

    captured = FormatProfile(
        page_margins_in=margins,
        columns=columns,
        contact_separator=separator,
        dates_on_title_line=dates_on_title_line,
        bullet_glyph=bullet_glyph,
        bullet_left_indent_in=bullet_indent_in,
        skills_layout=skills_layout,
        section_order=section_order,
        section_titles=section_titles,
        roles=roles,
    )
    defaults = default_format_profile()
    for role in ALL_ROLES:
        captured.roles.setdefault(role, defaults.roles[role])
    return captured


# ---------- render ----------


def _apply_role(para: Paragraph, style: RoleStyle):
    if style.alignment in _ALIGNMENTS:
        para.alignment = _ALIGNMENTS[style.alignment]
    pf = para.paragraph_format
    pf.space_before = Pt(style.space_before_pt)
    pf.space_after = Pt(style.space_after_pt)
    if style.line_spacing is not None:
        pf.line_spacing = style.line_spacing


def _write_run(para: Paragraph, text: str, style: RoleStyle):
    run = para.add_run(text)
    font = run.font
    if style.font_name:
        font.name = style.font_name
    if style.size_pt is not None:
        font.size = Pt(style.size_pt)
    font.bold = style.bold
    font.italic = style.italic
    if style.color:
        font.color.rgb = RGBColor.from_string(style.color)
    return run


def _role_para(doc: _Document, text: str, style: RoleStyle) -> Paragraph:
    para = doc.add_paragraph()
    _apply_role(para, style)
    _write_run(para, text, style)
    return para


def _set_columns(section, count: int):
    if count <= 1:
        return
    cols = section._sectPr.find(qn("w:cols"))
    if cols is None:
        cols = section._sectPr.makeelement(qn("w:cols"), {})
        section._sectPr.append(cols)
    cols.set(qn("w:num"), str(count))


def _content_width_in(fmt: FormatProfile) -> float:
    return 8.5 - fmt.page_margins_in["left"] - fmt.page_margins_in["right"]


def _dates(start: str, end: str | None) -> str:
    return f"{start} – {end or 'Present'}"


def _entry_header(doc: _Document, title: str, dates: str, fmt: FormatProfile):
    title_style = fmt.role(ROLE_ENTRY_TITLE)
    sub_style = fmt.role(ROLE_ENTRY_SUB)
    if fmt.dates_on_title_line:
        para = doc.add_paragraph()
        _apply_role(para, title_style)
        para.paragraph_format.tab_stops.add_tab_stop(
            Inches(_content_width_in(fmt)), WD_TAB_ALIGNMENT.RIGHT
        )
        _write_run(para, f"{title}\t", title_style)
        _write_run(para, dates, sub_style)
    else:
        _role_para(doc, title, title_style)
        _role_para(doc, dates, sub_style)


def _section_header(doc: _Document, section: str, fmt: FormatProfile):
    title = fmt.section_titles.get(section) or DEFAULT_SECTION_TITLES[section]
    _role_para(doc, title, fmt.role(ROLE_SECTION_HEADER))


def _bullet_para(doc: _Document, text: str, fmt: FormatProfile):
    style = fmt.role(ROLE_BULLET)
    para = doc.add_paragraph()
    _apply_role(para, style)
    if fmt.bullet_left_indent_in is not None:
        para.paragraph_format.left_indent = Inches(fmt.bullet_left_indent_in)
    glyph = f"{fmt.bullet_glyph} " if fmt.bullet_glyph else ""
    _write_run(para, f"{glyph}{text}", style)


def render_docx(content: ResumeContent, fmt: FormatProfile) -> bytes:
    """Rebuild a resume .docx from canonical content through a
    FormatProfile. Sections with no content are skipped; everything else
    follows the captured order and styles."""
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(fmt.page_margins_in["top"])
    section.right_margin = Inches(fmt.page_margins_in["right"])
    section.bottom_margin = Inches(fmt.page_margins_in["bottom"])
    section.left_margin = Inches(fmt.page_margins_in["left"])
    _set_columns(section, fmt.columns)

    header = content.header
    if header.name:
        _role_para(doc, header.name, fmt.role(ROLE_NAME))
    contact_bits = [
        bit
        for bit in [header.email, header.phone, header.location, *header.links]
        if bit
    ]
    if contact_bits:
        sep = f" {fmt.contact_separator} "
        _role_para(doc, sep.join(contact_bits), fmt.role(ROLE_CONTACT))

    body_style = fmt.role(ROLE_BODY)
    sub_style = fmt.role(ROLE_ENTRY_SUB)

    for section_key in fmt.section_order:
        if section_key == SECTION_SUMMARY and content.summary:
            _section_header(doc, section_key, fmt)
            _role_para(doc, content.summary, body_style)

        elif section_key == SECTION_EXPERIENCE and content.experiences:
            _section_header(doc, section_key, fmt)
            for exp in content.experiences:
                title = f"{exp.title} — {exp.company}"
                _entry_header(doc, title, _dates(exp.start_date, exp.end_date), fmt)
                for bullet in exp.bullets:
                    _bullet_para(doc, bullet, fmt)

        elif section_key == SECTION_SKILLS and content.skill_groups:
            _section_header(doc, section_key, fmt)
            if fmt.skills_layout == SKILLS_LAYOUT_GROUPED:
                for group in content.skill_groups:
                    label = f"{group.category}: " if group.category else ""
                    _role_para(
                        doc, f"{label}{', '.join(group.skills)}", body_style
                    )
            else:
                flat = [s for g in content.skill_groups for s in g.skills]
                _role_para(doc, ", ".join(flat), body_style)

        elif section_key == SECTION_EDUCATION and content.education:
            _section_header(doc, section_key, fmt)
            for edu in content.education:
                title = f"{edu.degree} — {edu.institution}"
                _entry_header(
                    doc, title, _dates(edu.start_date, edu.end_date), fmt
                )
                if edu.field_of_study:
                    _role_para(doc, edu.field_of_study, sub_style)
                if edu.description:
                    _role_para(doc, edu.description, body_style)

        elif section_key == SECTION_PROJECTS and content.projects:
            _section_header(doc, section_key, fmt)
            for proj in content.projects:
                title = proj.name + (f" — {proj.link}" if proj.link else "")
                _entry_header(
                    doc, title, _dates(proj.start_date, proj.end_date), fmt
                )
                if proj.description:
                    _role_para(doc, proj.description, body_style)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
