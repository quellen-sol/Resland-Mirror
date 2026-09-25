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

FORMAT_PROFILE_VERSION = 2

# Roles a FormatProfile carries a style for. `dates`/`contact` reuse
# `entry_sub`/`body` styles when not captured.
ROLE_NAME = "name"
ROLE_CONTACT = "contact"
ROLE_LOCATION = "location"
ROLE_SECTION_HEADER = "section_header"
ROLE_ENTRY_TITLE = "entry_title"
ROLE_ENTRY_SUB = "entry_sub"
ROLE_BODY = "body"
ROLE_BULLET = "bullet"
ALL_ROLES = (
    ROLE_NAME,
    ROLE_CONTACT,
    ROLE_LOCATION,
    ROLE_SECTION_HEADER,
    ROLE_ENTRY_TITLE,
    ROLE_ENTRY_SUB,
    ROLE_BODY,
    ROLE_BULLET,
)

# Body-adjacent roles that fall back to the document's dominant size when
# the source didn't reveal a role-specific size.
_BODY_SIZED_ROLES = {ROLE_BODY, ROLE_BULLET, ROLE_CONTACT, ROLE_ENTRY_SUB, ROLE_LOCATION}

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
    location_on_own_line: bool = False
    entry_title_separator: str = " — "
    # When the entry title line splits into a bold head (job title) and a
    # lighter tail (company/location/dates), the tail renders in entry_sub.
    entry_title_tail_sub: bool = False
    dates_on_title_line: bool = True
    dates_separator: str = " – "
    # Label used for open-ended entries ("Present"); None = render the
    # start date alone.
    dates_open_label: str | None = "Present"
    bullet_glyph: str | None = "•"
    bullet_left_indent_in: float | None = None
    # Hanging indent (numbered-list look): the glyph sits this many inches
    # left of the text block.
    bullet_hanging_indent_in: float | None = None
    skills_layout: str = SKILLS_LAYOUT_FLAT
    skills_category_separator: str = ": "
    skills_category_bold: bool = False
    project_link_on_own_line: bool = False
    project_dates_inline: bool = False
    # Empty paragraphs the source puts directly above each section header.
    section_blank_lines: dict[str, int] = field(default_factory=dict)
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


def content_source_hash(
    content: ResumeContent,
    template: str = "original",
    fmt: "FormatProfile | None" = None,
) -> str:
    """Stable hash of what the generated docx depends on. Recomputed at
    export time; a mismatch with the stored hash means regenerate. The
    effective format belongs in the key too — a fresh upload that only
    changes layout must still invalidate the cached docx."""
    payload = json.dumps(
        {
            "template": template,
            "format_version": FORMAT_PROFILE_VERSION,
            "format": json.loads(fmt.to_json()) if fmt is not None else None,
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
            ROLE_LOCATION: RoleStyle(font_name="Calibri", size_pt=10, italic=True),
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


def _last_text_run(para: Paragraph):
    for run in reversed(para.runs):
        if run.text.strip():
            return run
    return _first_text_run(para)


def _para_style(para: Paragraph) -> RoleStyle:
    """Resolve a paragraph's effective look: direct run props fall back to
    the paragraph style. Unknown values stay None — the renderer then falls
    back to the document default like Word does."""
    run = _first_text_run(para)
    return _run_style(run, para)


def _run_style(run, para: Paragraph) -> RoleStyle:
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


def _all_paragraphs(doc: _Document) -> list[Paragraph]:
    """Every paragraph in document order, including those inside table
    cells — resume layouts built on invisible tables still match content."""
    try:
        items = doc.iter_inner_content()
    except AttributeError:
        return list(doc.paragraphs)
    paras = []
    for item in items:
        if isinstance(item, Paragraph):
            paras.append(item)
        else:
            for row in item.rows:
                for cell in row.cells:
                    paras.extend(cell.paragraphs)
    return paras


def _doc_default_font(doc: _Document) -> tuple[str | None, float | None]:
    """w:docDefaults run font/size — what runs without explicit props get."""
    try:
        styles_el = doc.styles.element
        rpr_default = styles_el.find(qn("w:docDefaults"))
        if rpr_default is None:
            return None, None
        rpr = rpr_default.find(qn("w:rPrDefault") + "/" + qn("w:rPr"))
        if rpr is None:
            return None, None
        fonts = rpr.find(qn("w:rFonts"))
        sz = rpr.find(qn("w:sz"))
        name = fonts.get(qn("w:ascii")) if fonts is not None else None
        size = float(sz.get(qn("w:val"))) / 2.0 if sz is not None else None
        return name, size
    except Exception:
        return None, None


def _dominant_font(
    paras: list[Paragraph], default: tuple[str | None, float | None]
) -> tuple[str | None, float | None]:
    """Modal (font name, size) across all runs — the doc's everyday look,
    used to fill roles the source never revealed a style for."""
    from collections import Counter

    counter: Counter = Counter()
    for para in paras:
        for run in para.runs:
            if not run.text.strip():
                continue
            counter[
                (run.font.name or default[0], run.font.size or default[1])
            ] += len(run.text)
    if not counter:
        return default
    name, size = counter.most_common(1)[0][0]
    return name, round(size.pt, 1) if hasattr(size, "pt") else size


_SEPARATORS = (" | ", " — ", " – ", " - ", " · ", " @ ", " at ")


def _title_separator(text: str, head: str, tail: str) -> str | None:
    """The separator joining title and company on an entry line — "|" or
    "—" etc. Detected from what actually sits between them in the source."""
    i = text.find(head)
    j = text.find(tail, i + len(head)) if i >= 0 else -1
    if i >= 0 and j > i:
        between = text[i + len(head) : j]
        if between.strip():
            return f" {between.strip()} "
    for candidate in _SEPARATORS:
        if candidate in text:
            return candidate
    return None


_DATE_RANGE = re.compile(
    r"\d{4}\s*([-–—])\s*(?:\d{4}|\w{3,9}\s*\d{4}|Present|Current|Now)",
    re.IGNORECASE,
)
_OPEN_LABEL = re.compile(r"\b(Present|Current|Now)\b")


def _dates_separator(texts: list[str]) -> str | None:
    """The dash between start and end dates — " - " vs " – " vs " — "."""
    for text in texts:
        m = _DATE_RANGE.search(text)
        if m:
            return f" {m.group(1)} "
    return None


def _dates_open_label(texts: list[str]) -> str | None:
    """How the source marks open-ended entries — \"Present\", \"Current\" —
    or None when no open-ended label appears."""
    for text in texts:
        m = _OPEN_LABEL.search(text)
        if m:
            return m.group(1)
    return None


def _numbering_glyph(doc: _Document, para: Paragraph) -> str | None:
    """Resolve a paragraph's list marker through numbering.xml: the
    abstractNum's lvlText for its ilvl ("●", "1.", …)."""
    pPr = para._p.find(qn("w:pPr"))
    numPr = pPr.find(qn("w:numPr")) if pPr is not None else None
    if numPr is None:
        return None
    num_id_el = numPr.find(qn("w:numId"))
    ilvl_el = numPr.find(qn("w:ilvl"))
    if num_id_el is None:
        return None
    num_id = num_id_el.get(qn("w:val"))
    ilvl = ilvl_el.get(qn("w:val")) if ilvl_el is not None else "0"
    numbering_part = next(
        (
            rel.target_part
            for rel in doc.part.rels.values()
            if rel.reltype.endswith("/numbering")
        ),
        None,
    )
    if numbering_part is None:
        return None
    ns = numbering_part.element
    num = ns.find(f'{qn("w:num")}[@{qn("w:numId")}="{num_id}"]')
    if num is None:
        return None
    abstract_id_el = num.find(qn("w:abstractNumId"))
    if abstract_id_el is None:
        return None
    abstract = ns.find(
        f'{qn("w:abstractNum")}[@{qn("w:abstractNumId")}="{abstract_id_el.get(qn("w:val"))}"]'
    )
    if abstract is None:
        return None
    lvl = abstract.find(f'{qn("w:lvl")}[@{qn("w:ilvl")}="{ilvl}"]')
    if lvl is None:
        return None
    num_fmt_el = lvl.find(qn("w:numFmt"))
    lvl_text_el = lvl.find(qn("w:lvlText"))
    lvl_text = lvl_text_el.get(qn("w:val")) if lvl_text_el is not None else None
    if num_fmt_el is not None and num_fmt_el.get(qn("w:val")) != "bullet":
        # Numbered lists render a counter, not a glyph — approximate with "1.".
        if lvl_text:
            return lvl_text.replace("%1", "1")
        return "1."
    return lvl_text


def _blank_lines_above(paras, header_idx: int) -> int:
    """Count of consecutive empty paragraphs directly above a header — how
    some resumes create vertical space between sections."""
    count = 0
    j = header_idx - 1
    while j >= 0 and not paras[j].text.strip():
        count += 1
        j -= 1
    return count


def _dates_inline(text: str, start_date: str) -> bool:
    """True when the entry's start date sits inside the title line's
    separator chain ("Name | tech | 2026") rather than floated right via a
    tab or wide space gap ("Company          Mar 2020 - Oct 2021")."""
    needle = (start_date or "").strip()
    if not needle:
        return False
    idx = text.find(needle)
    if idx <= 0:
        return False
    prefix = text[:idx].rstrip()
    if not prefix:
        return False
    # Right-floated dates leave a wide gap of whitespace, not a separator.
    if re.search(r"\s{4,}$", text[:idx]):
        return False
    return prefix[-1] in "|—–·-@" or prefix.endswith(" at")


def _skills_category_split(text: str, category: str, first_skill: str):
    """"Languages: Python, …" → (": ", bold-label flag handled by caller)."""
    idx = text.find(category)
    if idx < 0:
        return None
    after = text[idx + len(category) :]
    skill_idx = after.find(first_skill) if first_skill else -1
    sep = after[:skill_idx] if skill_idx > 0 else after
    return sep if sep.strip() else None


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


def _match_skill_idx(paras: list, category: str | None, skills: list) -> int | None:
    """Locate a skill group's line: prefer the line opening with the
    category label ("Languages: …"), else the "skill, skill" pair. Loose
    label+skill matching is last — labels and skill names both appear
    inside experience bullets ("…AWS infrastructure with Terraform…")."""
    skills = [s for s in skills if s]
    cat = _norm(category)
    if cat:
        label = re.compile(rf"^{re.escape(cat)}\s*[:;\-–—|•]")
        for i, para in enumerate(paras):
            if label.search(_norm(para.text)):
                return i
    if len(skills) >= 2:
        hit = _match_idx(paras, f"{_norm(skills[0])}, {_norm(skills[1])}")
        if hit is not None:
            return hit
    if cat and skills:
        first = _norm(skills[0])
        for i, para in enumerate(paras):
            text = _norm(para.text)
            if cat in text and first in text:
                return i
    return _match_idx(paras, skills[0] if skills else None)


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
    paras = _all_paragraphs(doc)
    roles: dict[str, RoleStyle] = {}
    section_titles: dict[str, str] = {}

    basic = profile.basic_info
    links = getattr(basic, "links", None) or []
    name_idx = _match_idx(paras, basic.name)
    if name_idx is None:
        name_idx = next((i for i, p in enumerate(paras) if p.text.strip()), None)
    contact_idx = _match_any_idx(paras, [basic.email, basic.phone, *links])
    location_idx = _match_idx(paras, basic.location)

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
            _match_skill_idx(paras, cat.category, cat.skills)
            for cat in profile.skills
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
    section_blank_lines: dict[str, int] = {}
    for section, first in section_first.items():
        header_idx = _section_header_idx(paras, first, claimed)
        if header_idx is None:
            continue
        claimed.add(header_idx)
        section_titles[section] = paras[header_idx].text.strip()
        blank = _blank_lines_above(paras, header_idx)
        if blank:
            section_blank_lines[section] = blank
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

    # Entry title line: which separator joins title to company, whether the
    # tail (company/dates) runs lighter than the title, and whether dates
    # sit on the title line vs their own line.
    first_exp = profile.experience[0] if profile.experience else None
    dates_on_title_line = True
    entry_title_separator = " — "
    tail_sub = False
    tail_style: RoleStyle | None = None
    if first_exp is not None:
        exp_para_idx = _match_any_idx(
            paras, [first_exp.position, first_exp.company]
        )
        if exp_para_idx is not None:
            exp_para = paras[exp_para_idx]
            exp_text = exp_para.text
            sep = _title_separator(
                exp_text, first_exp.position, first_exp.company
            )
            if sep:
                entry_title_separator = sep
            date_bits = _norm(first_exp.start_date)
            dates_on_title_line = bool(
                date_bits and date_bits.split()[0] in _norm(exp_text)
            )
            # Bold head + lighter tail → the tail gets its own (sub) style.
            head_run = _first_text_run(exp_para)
            tail_run = _last_text_run(exp_para)
            if (
                head_run is not None
                and tail_run is not None
                and tail_run is not head_run
                and head_run.font.bold
                and not tail_run.font.bold
            ):
                tail_sub = True
                tail_style = _run_style(tail_run, exp_para)
        else:
            dates_on_title_line = True

    # Dates style: separator between start/end and the open-ended label.
    # Entries that print dates on their own line put them right after the
    # title, so look at each matched entry and the two paragraphs below it.
    entry_idxs = sorted(i for i in (exp_idx + edu_idx + proj_idx))
    date_texts = [
        paras[j].text
        for i in entry_idxs
        for j in range(i, min(i + 3, len(paras)))
    ]
    dates_separator = _dates_separator(date_texts) or " – "
    dates_open_label = _dates_open_label(date_texts)

    # Bullet glyph/indent from the first matched bullet paragraph.
    bullet_glyph = None
    bullet_indent_in = None
    bullet_hanging_in = None
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
        elif has_numbering:
            # The real marker lives in numbering.xml ("●", "1.", …).
            bullet_glyph = _numbering_glyph(doc, bullet_para) or "•"
        elif "list" in style_name.lower():
            bullet_glyph = "•"
        indent = bullet_para.paragraph_format.left_indent
        bullet_indent_in = round(indent.inches, 2) if indent is not None else None
        hanging = bullet_para.paragraph_format.first_line_indent
        if hanging is not None and hanging < 0:
            bullet_hanging_in = round(-hanging.inches, 2)

    # Contact separator between the header fields, and whether location
    # sits on its own line.
    separator = "|"
    if contact_idx is not None:
        contact_text = paras[contact_idx].text
        for candidate in ("|", "•", "·", "-"):
            if f" {candidate} " in contact_text:
                separator = candidate
                break
    location_on_own_line = (
        location_idx is not None and location_idx != contact_idx
    )

    # Skills: how the source separates category from items, and whether the
    # category label is bolded.
    skills_category_separator = ": "
    skills_category_bold = False
    first_cat = profile.skills[0] if profile.skills else None
    first_cat_idx = (
        _match_skill_idx(paras, first_cat.category, first_cat.skills)
        if first_cat is not None
        else None
    )
    if first_cat_idx is not None and first_cat is not None:
        skill_para = paras[first_cat_idx]
        sep = _skills_category_split(
            skill_para.text,
            first_cat.category or "",
            first_cat.skills[0] if first_cat.skills else "",
        )
        if sep:
            skills_category_separator = sep
        # The label run may end before the items begin — a bold first run
        # means the source bolds the "Category:" label.
        cat_run = _first_text_run(skill_para)
        if cat_run is not None and cat_run.font.bold:
            skills_category_bold = True

    # Projects: link on its own line, and dates inside the title line's
    # separator chain rather than floated right.
    project_link_on_own_line = False
    project_dates_inline = False
    first_proj = profile.projects[0] if profile.projects else None
    if first_proj is not None:
        proj_name_idx = _match_idx(paras, first_proj.name)
        if proj_name_idx is not None:
            proj_text = paras[proj_name_idx].text
            if first_proj.link:
                link_idx = _match_idx(paras, first_proj.link)
                project_link_on_own_line = (
                    link_idx is not None and link_idx != proj_name_idx
                )
            project_dates_inline = _dates_inline(
                proj_text, first_proj.start_date
            )
            if first_exp is None or not _title_separator(
                exp_text, first_exp.position, first_exp.company
            ):
                # No experience line to learn the separator from — the
                # project line's own chain is the next best witness.
                anchor = first_proj.link or first_proj.start_date
                proj_sep = _title_separator(proj_text, first_proj.name, anchor)
                if proj_sep:
                    entry_title_separator = proj_sep

    # Roles from matched paragraphs (first hit wins per role).
    if name_idx is not None:
        roles.setdefault(ROLE_NAME, _para_style(paras[name_idx]))
    if contact_idx is not None:
        roles.setdefault(ROLE_CONTACT, _para_style(paras[contact_idx]))
    if location_idx is not None:
        roles.setdefault(ROLE_LOCATION, _para_style(paras[location_idx]))
    if exp_idx:
        roles.setdefault(ROLE_ENTRY_TITLE, _para_style(paras[exp_idx[0]]))
    if summary_idx is not None:
        roles.setdefault(ROLE_BODY, _para_style(paras[summary_idx]))
    elif edu_idx:
        roles.setdefault(ROLE_BODY, _para_style(paras[edu_idx[0]]))
    elif skill_idx:
        # The items run, not the bold "Category:" label, is the body look.
        roles.setdefault(
            ROLE_BODY,
            _run_style(_last_text_run(paras[skill_idx[0]]), paras[skill_idx[0]]),
        )
    elif bullet_idx:
        roles.setdefault(ROLE_BODY, _para_style(paras[bullet_idx[0]]))
    # The sub role covers company/dates on entry lines and edu fields:
    # prefer the tail-run style when the title line splits, then education,
    # then the title itself so dates still match the line they sit on.
    if tail_style is not None:
        roles.setdefault(ROLE_ENTRY_SUB, tail_style)
    elif edu_idx:
        roles.setdefault(ROLE_ENTRY_SUB, _para_style(paras[edu_idx[0]]))
    elif exp_idx:
        roles.setdefault(ROLE_ENTRY_SUB, _para_style(paras[exp_idx[0]]))
    if bullet_idx:
        roles.setdefault(ROLE_BULLET, _para_style(paras[bullet_idx[0]]))

    # Page setup from the first section.
    margins = {"top": 1.0, "right": 1.0, "bottom": 1.0, "left": 1.0}
    columns = 1
    if doc.sections:
        s = doc.sections[0]
        margins = {
            "top": round(s.top_margin.inches, 3),
            "right": round(s.right_margin.inches, 3),
            "bottom": round(s.bottom_margin.inches, 3),
            "left": round(s.left_margin.inches, 3),
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
        location_on_own_line=location_on_own_line,
        entry_title_separator=entry_title_separator,
        entry_title_tail_sub=tail_sub,
        dates_on_title_line=dates_on_title_line,
        dates_separator=dates_separator,
        dates_open_label=dates_open_label,
        bullet_glyph=bullet_glyph,
        bullet_left_indent_in=bullet_indent_in,
        bullet_hanging_indent_in=bullet_hanging_in,
        skills_layout=skills_layout,
        skills_category_separator=skills_category_separator,
        skills_category_bold=skills_category_bold,
        project_link_on_own_line=project_link_on_own_line,
        project_dates_inline=project_dates_inline,
        section_blank_lines=section_blank_lines,
        section_order=section_order,
        section_titles=section_titles,
        roles=roles,
    )
    # Any role the doc didn't reveal falls back to defaults patched toward
    # the document's dominant font, so rendering never produces a foreign
    # typeface for roles the source left unseen.
    dominant = _dominant_font(paras, _doc_default_font(doc))
    default_font = _doc_default_font(doc)
    for role in ALL_ROLES:
        if role not in captured.roles:
            fallback = RoleStyle(**asdict(default_format_profile().roles[role]))
            if dominant[0]:
                fallback.font_name = dominant[0]
            if role in _BODY_SIZED_ROLES and dominant[1]:
                fallback.size_pt = dominant[1]
            captured.roles[role] = fallback
            continue
        style = captured.roles[role]
        # A captured None means the source inherits the document default —
        # the output doc carries a different one, so pin it explicitly.
        if style.font_name is None and default_font[0]:
            style.font_name = default_font[0]
        if style.size_pt is None and default_font[1]:
            style.size_pt = default_font[1]
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
        return round(min(max(pt / 72.0, 0.25), 2.5), 3)

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
    links = getattr(basic, "links", None) or []
    name_idx = _match_idx(lines, basic.name)
    if name_idx is None:
        name_idx = next((i for i, line in enumerate(lines) if not line.empty), None)
    contact_idx = _match_any_idx(lines, [basic.email, basic.phone, *links])
    location_idx = _match_idx(lines, basic.location)

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
            _match_skill_idx(lines, cat.category, cat.skills)
            for cat in profile.skills
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

    # Entry title line: separator between title and company, and whether
    # dates sit on the title line vs their own line.
    first_exp = profile.experience[0] if profile.experience else None
    dates_on_title_line = True
    entry_title_separator = " — "
    if first_exp is not None:
        exp_line_idx = _match_any_idx(
            lines, [first_exp.position, first_exp.company]
        )
        if exp_line_idx is not None:
            exp_line = lines[exp_line_idx].text
            sep = _title_separator(
                exp_line, first_exp.position, first_exp.company
            )
            if sep:
                entry_title_separator = sep
            date_bits = _norm(first_exp.start_date)
            dates_on_title_line = bool(
                date_bits and date_bits.split()[0] in _norm(exp_line)
            )

    # Dates style: separator between start/end and the open-ended label.
    # Same rule as docx — separate date lines sit right under the title.
    entry_idxs = sorted(i for i in (exp_idx + edu_idx + proj_idx))
    date_texts = [
        lines[j].text
        for i in entry_idxs
        for j in range(i, min(i + 3, len(lines)))
    ]
    dates_separator = _dates_separator(date_texts) or " – "
    dates_open_label = _dates_open_label(date_texts)

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

    # Contact separator between the header fields, and whether location
    # sits on its own line.
    separator = "|"
    if contact_idx is not None:
        contact_text = lines[contact_idx].text
        for candidate in ("|", "•", "·", "-"):
            if f" {candidate} " in contact_text:
                separator = candidate
                break
    location_on_own_line = (
        location_idx is not None and location_idx != contact_idx
    )

    # Skills: how the source separates category from items.
    skills_category_separator = ": "
    skills_category_bold = False
    first_cat = profile.skills[0] if profile.skills else None
    first_cat_idx = (
        _match_skill_idx(lines, first_cat.category, first_cat.skills)
        if first_cat is not None
        else None
    )
    if first_cat_idx is not None and first_cat is not None:
        sep = _skills_category_split(
            lines[first_cat_idx].text,
            first_cat.category or "",
            first_cat.skills[0] if first_cat.skills else "",
        )
        if sep:
            skills_category_separator = sep
        skills_category_bold = lines[first_cat_idx].style.bold

    # Projects: link on its own line, and dates inside the title line's
    # separator chain rather than floated right.
    project_link_on_own_line = False
    project_dates_inline = False
    first_proj = profile.projects[0] if profile.projects else None
    if first_proj is not None:
        proj_name_idx = _match_idx(lines, first_proj.name)
        if proj_name_idx is not None:
            proj_text = lines[proj_name_idx].text
            if first_proj.link:
                link_idx = _match_idx(lines, first_proj.link)
                project_link_on_own_line = (
                    link_idx is not None and link_idx != proj_name_idx
                )
            project_dates_inline = _dates_inline(
                proj_text, first_proj.start_date
            )
            if first_exp is None or exp_line_idx is None:
                anchor = first_proj.link or first_proj.start_date
                proj_sep = _title_separator(proj_text, first_proj.name, anchor)
                if proj_sep:
                    entry_title_separator = proj_sep

    # Roles from matched lines (first hit wins per role).
    if name_idx is not None:
        roles.setdefault(ROLE_NAME, _style(lines[name_idx]))
    if contact_idx is not None:
        roles.setdefault(ROLE_CONTACT, _style(lines[contact_idx]))
    if location_idx is not None:
        roles.setdefault(ROLE_LOCATION, _style(lines[location_idx]))
    if exp_idx:
        roles.setdefault(ROLE_ENTRY_TITLE, _style(lines[exp_idx[0]]))
    if summary_idx is not None:
        roles.setdefault(ROLE_BODY, _style(lines[summary_idx]))
    elif edu_idx:
        roles.setdefault(ROLE_BODY, _style(lines[edu_idx[0]]))
    elif skill_idx:
        roles.setdefault(ROLE_BODY, _style(lines[skill_idx[0]]))
    elif bullet_idx:
        roles.setdefault(ROLE_BODY, _style(lines[bullet_idx[0]]))
    # Sub role covers company/dates on entry lines and edu fields: prefer
    # education lines, else the title itself so dates still match the line
    # they sit on.
    if edu_idx:
        roles.setdefault(ROLE_ENTRY_SUB, _style(lines[edu_idx[0]]))
    elif exp_idx:
        roles.setdefault(ROLE_ENTRY_SUB, _style(lines[exp_idx[0]]))
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
        location_on_own_line=location_on_own_line,
        entry_title_separator=entry_title_separator,
        dates_on_title_line=dates_on_title_line,
        dates_separator=dates_separator,
        dates_open_label=dates_open_label,
        bullet_glyph=bullet_glyph,
        bullet_left_indent_in=bullet_indent_in,
        skills_layout=skills_layout,
        skills_category_separator=skills_category_separator,
        skills_category_bold=skills_category_bold,
        project_link_on_own_line=project_link_on_own_line,
        project_dates_inline=project_dates_inline,
        section_order=section_order,
        section_titles=section_titles,
        roles=roles,
    )
    # Any role the doc didn't reveal falls back to defaults patched toward
    # the document's dominant font, so rendering never produces a foreign
    # typeface for roles the source left unseen.
    dominant = _pdf_dominant_font(doc)
    for role in ALL_ROLES:
        if role in captured.roles:
            continue
        fallback = RoleStyle(**asdict(default_format_profile().roles[role]))
        if dominant[0]:
            fallback.font_name = dominant[0]
        if role in _BODY_SIZED_ROLES and dominant[1]:
            fallback.size_pt = dominant[1]
        captured.roles[role] = fallback
    return captured


def _pdf_dominant_font(doc: PdfDoc) -> tuple[str | None, float | None]:
    """Modal (font name, size) across all pdf lines — the doc's everyday
    look, used to fill roles the source never revealed a style for."""
    from collections import Counter

    counter: Counter = Counter()
    for line in doc.lines:
        if line.empty:
            continue
        counter[(line.style.font_name, line.style.size_pt)] += len(line.text)
    if not counter:
        return None, None
    return counter.most_common(1)[0][0]


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


def _dates(start: str, end: str | None, fmt: FormatProfile) -> str:
    if end and end != start:
        return f"{start}{fmt.dates_separator}{end}"
    if not end and fmt.dates_open_label:
        return f"{start}{fmt.dates_separator}{fmt.dates_open_label}"
    return start


def _entry_header(
    doc: _Document, title: str, tail: str | None, dates: str, fmt: FormatProfile
):
    """One entry heading: title + optional tail (company) joined by the
    captured separator, dates floated right through a tab stop. When the
    source styles the tail lighter than the title (entry_title_tail_sub),
    the tail and dates run in entry_sub."""
    title_style = fmt.role(ROLE_ENTRY_TITLE)
    sub_style = fmt.role(ROLE_ENTRY_SUB)
    sep = fmt.entry_title_separator

    def _title_runs(para: Paragraph):
        if tail and fmt.entry_title_tail_sub:
            _write_run(para, title, title_style)
            _write_run(para, f"{sep}{tail}", sub_style)
        elif tail:
            _write_run(para, f"{title}{sep}{tail}", title_style)
        else:
            _write_run(para, title, title_style)

    if fmt.dates_on_title_line and dates:
        para = doc.add_paragraph()
        _apply_role(para, title_style)
        para.paragraph_format.tab_stops.add_tab_stop(
            Inches(_content_width_in(fmt)), WD_TAB_ALIGNMENT.RIGHT
        )
        _title_runs(para)
        _write_run(para, "\t", sub_style)
        _write_run(para, dates, sub_style)
    else:
        para = doc.add_paragraph()
        _apply_role(para, title_style)
        _title_runs(para)
        if dates:
            _role_para(doc, dates, sub_style)


def _section_header(doc: _Document, section: str, fmt: FormatProfile):
    # Reproduce the blank paragraphs the source puts above the header.
    for _ in range(fmt.section_blank_lines.get(section, 0)):
        blank = doc.add_paragraph()
        _apply_role(blank, fmt.role(ROLE_BODY))
    title = fmt.section_titles.get(section) or DEFAULT_SECTION_TITLES[section]
    _role_para(doc, title, fmt.role(ROLE_SECTION_HEADER))


def _bullet_para(doc: _Document, text: str, fmt: FormatProfile):
    style = fmt.role(ROLE_BULLET)
    para = doc.add_paragraph()
    _apply_role(para, style)
    glyph = fmt.bullet_glyph
    if fmt.bullet_left_indent_in is not None:
        para.paragraph_format.left_indent = Inches(fmt.bullet_left_indent_in)
    if glyph and fmt.bullet_hanging_indent_in:
        # Numbered-list look: glyph in the margin, text tabbed to the
        # paragraph indent.
        para.paragraph_format.first_line_indent = Inches(
            -fmt.bullet_hanging_indent_in
        )
        text_at = fmt.bullet_left_indent_in or fmt.bullet_hanging_indent_in
        para.paragraph_format.tab_stops.add_tab_stop(
            Inches(text_at), WD_TAB_ALIGNMENT.LEFT
        )
        _write_run(para, f"{glyph}\t", style)
        _write_run(para, text, style)
    else:
        prefix = f"{glyph} " if glyph else ""
        _write_run(para, f"{prefix}{text}", style)


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
        bit for bit in [header.email, header.phone] if bit
    ]
    if not fmt.location_on_own_line and header.location:
        contact_bits.append(header.location)
    contact_bits.extend(bit for bit in header.links if bit)
    if contact_bits:
        sep = f" {fmt.contact_separator} "
        _role_para(doc, sep.join(contact_bits), fmt.role(ROLE_CONTACT))
    if fmt.location_on_own_line and header.location:
        _role_para(doc, header.location, fmt.role(ROLE_LOCATION))

    body_style = fmt.role(ROLE_BODY)
    sub_style = fmt.role(ROLE_ENTRY_SUB)

    for section_key in fmt.section_order:
        if section_key == SECTION_SUMMARY and content.summary:
            _section_header(doc, section_key, fmt)
            _role_para(doc, content.summary, body_style)

        elif section_key == SECTION_EXPERIENCE and content.experiences:
            _section_header(doc, section_key, fmt)
            for exp in content.experiences:
                _entry_header(
                    doc,
                    exp.title,
                    exp.company,
                    _dates(exp.start_date, exp.end_date, fmt),
                    fmt,
                )
                for bullet in exp.bullets:
                    _bullet_para(doc, bullet, fmt)

        elif section_key == SECTION_SKILLS and content.skill_groups:
            _section_header(doc, section_key, fmt)
            if fmt.skills_layout == SKILLS_LAYOUT_GROUPED:
                for group in content.skill_groups:
                    para = doc.add_paragraph()
                    _apply_role(para, body_style)
                    if group.category:
                        label = _write_run(
                            para,
                            f"{group.category}{fmt.skills_category_separator}",
                            body_style,
                        )
                        if fmt.skills_category_bold:
                            label.font.bold = True
                    _write_run(para, ", ".join(group.skills), body_style)
            else:
                flat = [s for g in content.skill_groups for s in g.skills]
                _role_para(doc, ", ".join(flat), body_style)

        elif section_key == SECTION_EDUCATION and content.education:
            _section_header(doc, section_key, fmt)
            for edu in content.education:
                _entry_header(
                    doc,
                    edu.degree,
                    edu.institution,
                    _dates(edu.start_date, edu.end_date, fmt),
                    fmt,
                )
                if edu.field_of_study:
                    _role_para(doc, edu.field_of_study, sub_style)
                if edu.description:
                    _role_para(doc, edu.description, body_style)

        elif section_key == SECTION_PROJECTS and content.projects:
            _section_header(doc, section_key, fmt)
            for proj in content.projects:
                dates = _dates(proj.start_date, proj.end_date, fmt)
                if fmt.project_dates_inline:
                    # Dates join the title line's separator chain —
                    # "Name | stack | 2026". A link on that same line joins
                    # the chain too rather than moving to its own line.
                    tail = (
                        f"{proj.link}{fmt.entry_title_separator}{dates}"
                        if proj.link and not fmt.project_link_on_own_line
                        else dates
                    )
                    _entry_header(doc, proj.name, tail, "", fmt)
                else:
                    tail = (
                        proj.link if not fmt.project_link_on_own_line else None
                    )
                    _entry_header(doc, proj.name, tail, dates, fmt)
                if fmt.project_link_on_own_line and proj.link:
                    _role_para(doc, proj.link, sub_style)
                if proj.description:
                    _role_para(doc, proj.description, body_style)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
