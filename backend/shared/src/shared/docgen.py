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
from dataclasses import asdict, dataclass, field, fields
from typing import Any

from docx import Document
from docx.document import Document as _Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.text.paragraph import Paragraph
from docx.text.run import Run

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
# Optional roles — present only when the source shows them: hyperlinks
# (contact line links, own-line project links) and project block styles,
# which often differ from the experience look.
ROLE_LINK = "link"
ROLE_PROJECT_TITLE = "project_title"
ROLE_PROJECT_SUB = "project_sub"
ROLE_PROJECT_BODY = "project_body"
# Entry dates, when the source styles them apart from the entry tail
# (e.g. smaller gray dates under a bold title); falls back to entry_sub.
ROLE_DATES = "dates"
# Education lines' leading/trailing part looks; fall back to entry_title /
# entry_sub.
ROLE_EDUCATION_TITLE = "education_title"
ROLE_EDUCATION_SUB = "education_sub"
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

# Header contact block layouts: every field on one line joined by
# contact_separator, or one field per line ("Phone: …" / "Email: …").
CONTACT_INLINE = "inline"
CONTACT_STACKED = "stacked"
CONTACT_EMAIL = "email"
CONTACT_PHONE = "phone"
CONTACT_LOCATION = "location"
CONTACT_LINKS = "links"
_CONTACT_FIELDS = (CONTACT_EMAIL, CONTACT_PHONE, CONTACT_LOCATION, CONTACT_LINKS)

_ALIGNMENTS = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def _known_fields(cls, data: dict[str, Any]) -> dict[str, Any]:
    names = {f.name for f in fields(cls)}
    return {k: v for k, v in data.items() if k in names}


@dataclass
class RoleStyle:
    font_name: str | None = None
    size_pt: float | None = None
    bold: bool = False
    italic: bool = False
    color: str | None = None  # "RRGGBB"
    underline: bool = False
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
    # Stacked layout: contact_order lists the fields top to bottom,
    # contact_labels maps field → the label printed before it ("Phone:"),
    # and labelled values align at contact_value_tab_in when the source
    # tab-aligns them.
    contact_layout: str = CONTACT_INLINE
    contact_order: list[str] = field(default_factory=list)
    contact_labels: dict[str, str] = field(default_factory=dict)
    contact_label_bold: bool = False
    contact_value_tab_in: float | None = None
    # Experience entry lines: the separator between title and company.
    entry_title_separator: str = " — "
    # When the entry line splits into a styled leading part (bold title,
    # or bold company in a company-first source) and a lighter trailing
    # part, the trailing part renders in entry_sub. Styles follow position
    # — entry_title is the leading part's look — so the source's emphasis
    # stays on whichever part it put first.
    entry_title_tail_sub: bool = False
    # True when the source orders experience lines company first —
    # "Company - Title" instead of "Title - Company".
    entry_title_tail_first: bool = False
    # Education and project lines keep their own order, separator and
    # trailing-part look: "Institution - Degree" doesn't follow from
    # "Company - Title". None falls back to the experience value.
    education_title_separator: str | None = None
    education_title_tail_first: bool = False
    education_title_tail_sub: bool | None = None
    project_title_separator: str | None = None
    project_title_tail_first: bool = False
    project_title_tail_sub: bool | None = None
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
    # Per-section header styles — sources often size SKILLS/PROJECTS
    # headers differently from EXPERIENCE. Falls back to
    # roles[ROLE_SECTION_HEADER] for sections not captured.
    section_header_roles: dict[str, RoleStyle] = field(default_factory=dict)
    section_order: list[str] = field(default_factory=lambda: list(ALL_SECTIONS))
    section_titles: dict[str, str] = field(
        default_factory=lambda: dict(DEFAULT_SECTION_TITLES)
    )
    roles: dict[str, RoleStyle] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "FormatProfile":
        # Unknown keys are dropped: a profile written by a newer capturer
        # (the dispatcher deploys independently of the API) must still
        # load instead of falling back to the default look.
        data = _known_fields(FormatProfile, data)
        data["roles"] = {
            role: RoleStyle(**_known_fields(RoleStyle, style))
            for role, style in data.get("roles", {}).items()
        }
        data["section_header_roles"] = {
            section: RoleStyle(**_known_fields(RoleStyle, style))
            for section, style in data.get("section_header_roles", {}).items()
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


def _text_runs(para: Paragraph):
    """Runs in text order, including those inside hyperlinks — what
    `para.text` concatenates."""
    try:
        items = list(para.iter_inner_content())
    except AttributeError:
        return list(para.runs)
    runs = []
    for item in items:
        if isinstance(item, Run):
            runs.append(item)
        else:
            runs.extend(item.runs)
    return runs


def _run_at_offset(para: Paragraph, offset: int):
    """The run holding character `offset` of `para.text` (skipping to the
    next run with visible text when the offset lands on whitespace)."""
    if offset < 0:
        return None
    pos = 0
    hit = False
    for run in _text_runs(para):
        pos += len(run.text)
        if offset < pos:
            hit = True
        if hit and run.text.strip():
            return run
    return None


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
    underline = _pick(
        run.font.underline if run else None,
        getattr(style_font, "underline", None),
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
        underline=bool(underline) if underline is not None else False,
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
# Word separators accepted between an entry's parts ("Engineer at Acme").
_SEPARATOR_WORDS = ("at", "@")
# "Degree (Institution)": the opener is the separator, the closer trails.
_BRACKETS = {"(": ")", "[": "]"}


def _join_token(between: str) -> str | None:
    """The separator token in the text between an entry's two parts. A
    long gap holds more content (a field of study, a tech stack) — then
    the token touching the second part is the separator: "Name | Go,
    React | 2026" joins name and date with "|"."""
    if between.lower() in _SEPARATOR_WORDS:
        return between
    if len(between) <= 3 and not any(c.isalnum() for c in between):
        return between
    last = between.split()[-1]
    if last.lower() in _SEPARATOR_WORDS or (
        len(last) <= 2 and not any(c.isalnum() for c in last)
    ):
        return last
    if last[-1] in ",;":
        return last[-1]
    return None


def _title_separator(
    text: str, head: str, tail: str, strict: bool = False
) -> tuple[str, bool] | None:
    """(separator, tail_first) joining title and company on an entry line
    — "|" or "—" etc. Detected from what actually sits between them in
    the source, in whichever order the source writes them; tail_first is
    True when the tail (company) precedes the head (title). Unless
    `strict`, a line without both parts still yields the first common
    separator it shows outside a date range."""
    low = text.lower()
    for first, second, tail_first in (
        (head, tail, False),
        (tail, head, True),
    ):
        if not first or not second:
            continue
        i = low.find(first.lower())
        j = low.find(second.lower(), i + len(first)) if i >= 0 else -1
        if i < 0 or j <= i:
            continue
        between = " ".join(text[i + len(first) : j].split())
        token = _join_token(between) if between else None
        if token is None:
            continue
        if token in _BRACKETS:
            if not text[j + len(second) :].lstrip().startswith(_BRACKETS[token]):
                continue
            return f" {token}", tail_first
        # Punctuation joins take no leading space:
        # "Title, Company", not "Title , Company".
        if token[0] in ",;:.":
            return f"{token} ", tail_first
        return f" {token} ", tail_first
    if strict:
        return None
    # The dash inside "2020 – Present" isn't the title separator.
    scan = _DATE_RANGE.sub(" ", text)
    for candidate in _SEPARATORS:
        if candidate in scan:
            return candidate, False
    return None


def _offset_after(text: str, needle: str | None, start: int = 0) -> int:
    """Case-insensitive position of `needle` in `text` at/after `start`;
    -1 when absent."""
    if not needle:
        return -1
    return text.lower().find(needle.lower(), start)


def _entry_parts(entry_text: str, head: str, tail: str, tail_first: bool):
    """Offsets of an entry line's leading and trailing parts (whichever of
    head/tail the source writes first), -1 when not found."""
    lead, trail = (tail, head) if tail_first else (head, tail)
    li = _offset_after(entry_text, lead)
    ti = _offset_after(entry_text, trail, li + len(lead) if li >= 0 else 0)
    return li, ti


def _styles_differ(a: RoleStyle, b: RoleStyle) -> bool:
    return (a.font_name, a.size_pt, a.bold, a.italic, a.underline, a.color) != (
        b.font_name,
        b.size_pt,
        b.bold,
        b.italic,
        b.underline,
        b.color,
    )


def _contact_block(lines: list, basic: Any) -> tuple[list[str], dict[str, int]] | None:
    """Stacked contact block: (field order, field → line index) when each
    contact field sits on a line of its own and the lines form one block —
    "Phone: …" / "Email: …" / "Address: …" under the name. None for the
    inline "a | b | c" layout."""
    hits = {
        name: _match_all(lines, getattr(basic, name, None))
        for name in (CONTACT_EMAIL, CONTACT_PHONE, CONTACT_LOCATION)
    }
    anchors = hits[CONTACT_EMAIL][:1] + hits[CONTACT_PHONE][:1]
    if not anchors:
        return None

    def _nearest(idxs: list[int], value: str) -> int:
        # A city also shows up on entry lines ("Acme    Denver, CO"); the
        # header's copy is the one next to the email/phone lines, and on a
        # tie the line holding little besides the value.
        return min(
            idxs,
            key=lambda i: (
                sum(abs(i - a) for a in anchors),
                len(_norm(lines[i].text)) - len(_norm(value)),
                i,
            ),
        )

    found = {
        name: _nearest(idxs, getattr(basic, name))
        for name, idxs in hits.items()
        if idxs
    }
    link_idx = [
        _nearest(idxs, link)
        for link, idxs in (
            (link, _match_all(lines, link))
            for link in getattr(basic, "links", None) or []
        )
        if idxs
    ]
    if link_idx:
        found[CONTACT_LINKS] = min(link_idx)
    taken = [i for name, i in found.items() if name != CONTACT_LINKS] + link_idx
    if len(found) < 2 or len(set(taken)) != len(taken):
        return None
    if max(taken) - min(taken) > len(taken):
        # Scattered across the document, not one block.
        return None
    return sorted(found, key=found.get), found


def _contact_label(text: str, value: str | None) -> tuple[str, int] | None:
    """("Phone:", value offset) when a short label precedes the value."""
    pos = _offset_after(text, value)
    if pos <= 0:
        return None
    label = text[:pos].strip()
    if label.endswith(":") and len(label) <= 24:
        return label, pos
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


def _match_all(paras: list, needle: str | None) -> list[int]:
    """Every paragraph index whose text contains `needle` (normalized)."""
    target = _norm(needle)
    if not target:
        return []
    return [i for i, para in enumerate(paras) if target in _norm(para.text)]


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
    matched content — treated as that section's header line. A line ending
    in sentence punctuation is content (e.g. a wrapped bullet tail), so
    the scan skips it and keeps looking for the real header above."""
    j = content_idx - 1
    while j >= 0 and content_idx - j <= 6:
        text = paras[j].text.strip()
        if text and len(text) <= 48 and j not in claimed:
            if not text.endswith((".", ",", ";")):
                return j
        elif text:
            # Hit another section's content — stop looking.
            return None
        j -= 1
    return None


def _project_tail_sub(roles: dict[str, RoleStyle]) -> bool | None:
    """Whether the project line's trailing part (link/dates) looks unlike
    its name; None when no project line was captured (inherit)."""
    if ROLE_PROJECT_TITLE not in roles:
        return None
    sub = roles.get(ROLE_PROJECT_SUB)
    return sub is not None and _styles_differ(roles[ROLE_PROJECT_TITLE], sub)


def _project_separator(text: str, proj: Any) -> tuple[str, bool] | None:
    """Separator/order on a project line: the name joined to its link, else
    to its inline dates, else the first common separator on the line."""
    for anchor in (proj.link, proj.start_date):
        detected = _title_separator(text, proj.name, anchor, strict=True)
        if detected:
            return detected
    if _offset_after(text, proj.name) >= 0:
        return _title_separator(text, proj.name, None)
    return None


def _capture_contact_docx(
    paras: list[Paragraph], basic: Any
) -> tuple[dict[str, Any], dict[str, RoleStyle]]:
    """(FormatProfile contact_* fields, contact/location roles read from
    the value runs) for a stacked contact block; ({}, {}) keeps the inline
    defaults. A labelled line's first run is its label, so the field's own
    look comes from the run holding the value."""
    block = _contact_block(paras, basic)
    if block is None:
        return {}, {}
    order, at = block
    labels: dict[str, str] = {}
    roles: dict[str, RoleStyle] = {}
    label_bold = False
    tab_in: float | None = None
    for name in order:
        if name == CONTACT_LINKS:
            continue
        para = paras[at[name]]
        hit = _contact_label(para.text, getattr(basic, name, None))
        if hit is None:
            continue
        label, pos = hit
        value_run = _run_at_offset(para, pos)
        if value_run is not None:
            role = ROLE_LOCATION if name == CONTACT_LOCATION else ROLE_CONTACT
            roles.setdefault(role, _run_style(value_run, para))
        if not labels:
            run = _run_at_offset(para, 0)
            label_bold = run is not None and _run_style(run, para).bold
            stops = list(para.paragraph_format.tab_stops)
            if "\t" in para.text[:pos] and stops:
                tab_in = round(stops[0].position.inches, 2)
        labels[name] = label
    return {
        "contact_layout": CONTACT_STACKED,
        "contact_order": order,
        "contact_labels": labels,
        "contact_label_bold": label_bold,
        "contact_value_tab_in": tab_in,
    }, roles


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
    section_header_roles: dict[str, RoleStyle] = {}
    for section, first in section_first.items():
        header_idx = _section_header_idx(paras, first, claimed)
        if header_idx is None:
            continue
        claimed.add(header_idx)
        section_titles[section] = paras[header_idx].text.strip()
        section_header_roles[section] = _para_style(paras[header_idx])
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
    exp_separator_found = False
    tail_first = False
    tail_sub = False
    head_style: RoleStyle | None = None
    tail_style: RoleStyle | None = None
    dates_style: RoleStyle | None = None
    if first_exp is not None:
        exp_para_idx = _match_any_idx(
            paras, [first_exp.position, first_exp.company]
        )
        if exp_para_idx is not None:
            exp_para = paras[exp_para_idx]
            exp_text = exp_para.text
            detected = _title_separator(
                exp_text, first_exp.position, first_exp.company
            )
            if detected:
                entry_title_separator, tail_first = detected
                exp_separator_found = True
            date_bits = _norm(first_exp.start_date)
            dates_on_title_line = bool(
                date_bits and date_bits.split()[0] in _norm(exp_text)
            )
            # Styles follow position: the run where the source's leading
            # part starts is the entry_title look, the trailing part's run
            # the entry_sub look — for "Acme (bold) - Engineer" the bold
            # stays on the company the source emphasized.
            lead_at, trail_at = _entry_parts(
                exp_text, first_exp.position, first_exp.company, tail_first
            )
            head_run = _run_at_offset(exp_para, lead_at) or _first_text_run(
                exp_para
            )
            tail_run = _run_at_offset(exp_para, trail_at) or _last_text_run(
                exp_para
            )
            if head_run is not None:
                head_style = _run_style(head_run, exp_para)
                if tail_run is not None and tail_run is not head_run:
                    candidate = _run_style(tail_run, exp_para)
                    if _styles_differ(head_style, candidate):
                        tail_sub = True
                        tail_style = candidate
            if date_bits:
                token = date_bits.split()[0]
                if dates_on_title_line:
                    date_run = _run_at_offset(
                        exp_para, _offset_after(exp_text, token)
                    )
                    if date_run is not None:
                        dates_style = _run_style(date_run, exp_para)
                else:
                    for j in range(exp_para_idx + 1, min(exp_para_idx + 3, len(paras))):
                        if token in _norm(paras[j].text):
                            dates_style = _para_style(paras[j])
                            break

    # Education and project lines: their own order, separator, and
    # leading/trailing looks (same position rule as experience).
    edu_separator: str | None = None
    edu_tail_first = False
    edu_tail_sub: bool | None = None
    first_edu = profile.education[0] if profile.education else None
    if first_edu is not None:
        edu_para_idx = _match_any_idx(
            paras, [first_edu.degree, first_edu.institution]
        )
        if edu_para_idx is not None:
            edu_para = paras[edu_para_idx]
            detected = _title_separator(
                edu_para.text,
                first_edu.degree,
                first_edu.institution,
                strict=True,
            )
            if detected:
                edu_separator, edu_tail_first = detected
            lead_at, trail_at = _entry_parts(
                edu_para.text, first_edu.degree, first_edu.institution, edu_tail_first
            )
            lead_run = _run_at_offset(edu_para, lead_at)
            trail_run = _run_at_offset(edu_para, trail_at)
            if lead_run is not None:
                edu_head = _run_style(lead_run, edu_para)
                roles[ROLE_EDUCATION_TITLE] = edu_head
                if trail_run is not None:
                    edu_tail = _run_style(trail_run, edu_para)
                    edu_tail_sub = trail_run is not lead_run and _styles_differ(
                        edu_head, edu_tail
                    )
                    if edu_tail_sub:
                        roles[ROLE_EDUCATION_SUB] = edu_tail

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
    contact, contact_roles = _capture_contact_docx(paras, basic)
    for role, style in contact_roles.items():
        roles.setdefault(role, style)

    # Hyperlinks carry their own look (blue, underlined) distinct from
    # the contact text around them — capture the first hyperlink run.
    if contact_idx is not None and ROLE_LINK not in roles:
        for hlink in paras[contact_idx]._p.findall(qn("w:hyperlink")):
            r = hlink.find(qn("w:r"))
            if r is not None:
                roles[ROLE_LINK] = _run_style(
                    Run(r, paras[contact_idx]), paras[contact_idx]
                )
                break

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
    proj_separator: str | None = None
    proj_tail_first = False
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
            proj_detected = _project_separator(proj_text, first_proj)
            if proj_detected:
                proj_separator, proj_tail_first = proj_detected
                if not exp_separator_found:
                    # No experience line to learn the separator from —
                    # the project line's chain is the next best witness.
                    entry_title_separator = proj_separator
            # Projects often style name/tail/link differently from
            # experience entries — capture dedicated roles from the first
            # matched project block.
            proj_para = paras[proj_name_idx]
            roles.setdefault(
                ROLE_PROJECT_TITLE,
                _run_style(_first_text_run(proj_para), proj_para),
            )
            proj_tail_run = _last_text_run(proj_para)
            if proj_tail_run is not None and proj_tail_run is not _first_text_run(
                proj_para
            ):
                roles.setdefault(
                    ROLE_PROJECT_SUB, _run_style(proj_tail_run, proj_para)
                )
            if first_proj.description:
                desc_idx = _match_idx(paras, first_proj.description[:48])
                if desc_idx is not None:
                    roles.setdefault(
                        ROLE_PROJECT_BODY, _para_style(paras[desc_idx])
                    )
            if project_link_on_own_line and first_proj.link:
                link_para = paras[link_idx]
                for hlink in link_para._p.findall(qn("w:hyperlink")):
                    r = hlink.find(qn("w:r"))
                    if r is not None:
                        roles.setdefault(
                            ROLE_LINK, _run_style(Run(r, link_para), link_para)
                        )
                        break
                if ROLE_LINK not in roles:
                    link_style = _para_style(link_para)
                    if link_style.color or link_style.underline:
                        roles[ROLE_LINK] = link_style

    # Roles from matched paragraphs (first hit wins per role).
    if name_idx is not None:
        roles.setdefault(ROLE_NAME, _para_style(paras[name_idx]))
    if contact_idx is not None:
        roles.setdefault(ROLE_CONTACT, _para_style(paras[contact_idx]))
    if location_idx is not None:
        roles.setdefault(ROLE_LOCATION, _para_style(paras[location_idx]))
    if head_style is not None:
        roles.setdefault(ROLE_ENTRY_TITLE, head_style)
    elif exp_idx:
        roles.setdefault(ROLE_ENTRY_TITLE, _para_style(paras[exp_idx[0]]))
    if dates_style is not None:
        roles.setdefault(ROLE_DATES, dates_style)
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
        **contact,
        entry_title_separator=entry_title_separator,
        entry_title_tail_sub=tail_sub,
        entry_title_tail_first=tail_first,
        education_title_separator=edu_separator,
        education_title_tail_first=edu_tail_first,
        education_title_tail_sub=edu_tail_sub,
        project_title_tail_sub=_project_tail_sub(roles),
        project_title_separator=proj_separator,
        project_title_tail_first=proj_tail_first,
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
        section_header_roles=section_header_roles,
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


def _pdf_style_role(style, base: RoleStyle | None = None) -> RoleStyle:
    """A run's character style as a RoleStyle; paragraph-level settings
    (alignment, spacing) come from `base` — the line it sits on — when the
    role styles whole paragraphs."""
    role = RoleStyle(
        font_name=style.font_name,
        size_pt=style.size_pt,
        bold=style.bold,
        italic=style.italic,
        color=style.color,
    )
    if base is not None:
        role.alignment = base.alignment
        role.space_before_pt = base.space_before_pt
    return role


def _capture_contact_pdf(
    lines: list[PdfLine], basic: Any, base: Any
) -> tuple[dict[str, Any], dict[str, RoleStyle]]:
    """pdf analogue of _capture_contact_docx. Values that start their own
    run at one shared x (a label column, then the values) give the tab
    position. `base` maps a line to its paragraph-level RoleStyle."""
    block = _contact_block(lines, basic)
    if block is None:
        return {}, {}
    order, at = block
    labels: dict[str, str] = {}
    roles: dict[str, RoleStyle] = {}
    label_bold = False
    offsets: list[float] = []
    for name in order:
        if name == CONTACT_LINKS:
            continue
        line = lines[at[name]]
        hit = _contact_label(line.text, getattr(basic, name, None))
        if hit is None:
            continue
        label, pos = hit
        role = ROLE_LOCATION if name == CONTACT_LOCATION else ROLE_CONTACT
        roles.setdefault(role, _pdf_style_role(line.style_at(pos), base=base(line)))
        if not labels:
            label_bold = line.style_at(0).bold
        labels[name] = label
        start = 0
        for run in line.runs:
            if start <= pos < start + len(run.text):
                if not line.text[start:pos].strip() and run.x0 is not None:
                    offsets.append(run.x0 - line.x0)
                break
            start += len(run.text)
    tab_in = None
    if (
        labels
        and len(offsets) == len(labels)
        and min(offsets) > 0
        and max(offsets) - min(offsets) <= 2.0
    ):
        tab_in = round(sum(offsets) / len(offsets) / 72.0, 2)
    return {
        "contact_layout": CONTACT_STACKED,
        "contact_order": order,
        "contact_labels": labels,
        "contact_label_bold": label_bold,
        "contact_value_tab_in": tab_in,
    }, roles


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
    section_header_roles: dict[str, RoleStyle] = {}
    for section, first in section_first.items():
        header_idx = _section_header_idx(lines, first, claimed)
        if header_idx is None:
            continue
        claimed.add(header_idx)
        section_titles[section] = lines[header_idx].text.strip()
        section_header_roles[section] = _style(lines[header_idx])
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
    exp_separator_found = False
    tail_first = False
    tail_sub = False
    head_style: RoleStyle | None = None
    tail_style: RoleStyle | None = None
    dates_style: RoleStyle | None = None
    if first_exp is not None:
        exp_line_idx = _match_any_idx(
            lines, [first_exp.position, first_exp.company]
        )
        if exp_line_idx is not None:
            exp_line = lines[exp_line_idx]
            detected = _title_separator(
                exp_line.text, first_exp.position, first_exp.company
            )
            if detected:
                entry_title_separator, tail_first = detected
                exp_separator_found = True
            date_bits = _norm(first_exp.start_date)
            dates_on_title_line = bool(
                date_bits and date_bits.split()[0] in _norm(exp_line.text)
            )
            # Same position rule as docx, read from the line's style runs:
            # the leading part's look is entry_title, a differently styled
            # trailing part becomes entry_sub.
            lead_at, trail_at = _entry_parts(
                exp_line.text, first_exp.position, first_exp.company, tail_first
            )
            head_pdf = exp_line.style_at(lead_at) if lead_at >= 0 else exp_line.style
            head_style = _pdf_style_role(head_pdf, base=_style(exp_line))
            if trail_at >= 0:
                tail_candidate = _pdf_style_role(exp_line.style_at(trail_at))
                if _styles_differ(_pdf_style_role(head_pdf), tail_candidate):
                    tail_sub = True
                    tail_style = tail_candidate
            if date_bits:
                token = date_bits.split()[0]
                if dates_on_title_line:
                    dates_style = _pdf_style_role(
                        exp_line.style_at(_offset_after(exp_line.text, token))
                    )
                else:
                    for j in range(exp_line_idx + 1, min(exp_line_idx + 3, len(lines))):
                        if token in _norm(lines[j].text):
                            dates_style = _style(lines[j])
                            break

    # Education and project lines: their own order, separator, and
    # leading/trailing looks (same position rule as experience).
    edu_separator: str | None = None
    edu_tail_first = False
    edu_tail_sub: bool | None = None
    first_edu = profile.education[0] if profile.education else None
    if first_edu is not None:
        edu_line_idx = _match_any_idx(
            lines, [first_edu.degree, first_edu.institution]
        )
        if edu_line_idx is not None:
            edu_line = lines[edu_line_idx]
            detected = _title_separator(
                edu_line.text,
                first_edu.degree,
                first_edu.institution,
                strict=True,
            )
            if detected:
                edu_separator, edu_tail_first = detected
            lead_at, trail_at = _entry_parts(
                edu_line.text, first_edu.degree, first_edu.institution, edu_tail_first
            )
            if lead_at >= 0:
                edu_head = _pdf_style_role(
                    edu_line.style_at(lead_at), base=_style(edu_line)
                )
                roles[ROLE_EDUCATION_TITLE] = edu_head
                if trail_at >= 0:
                    edu_tail = _pdf_style_role(edu_line.style_at(trail_at))
                    edu_tail_sub = _styles_differ(_pdf_style_role(edu_line.style_at(lead_at)), edu_tail)
                    if edu_tail_sub:
                        roles[ROLE_EDUCATION_SUB] = edu_tail

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
    contact, contact_roles = _capture_contact_pdf(lines, basic, _style)
    for role, style in contact_roles.items():
        roles.setdefault(role, style)

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
        cat_line = lines[first_cat_idx]
        cat_at = _offset_after(cat_line.text, first_cat.category)
        # The label's own run, not the line's dominant (items) style.
        skills_category_bold = (
            cat_line.style_at(cat_at) if cat_at >= 0 else cat_line.style
        ).bold

    # Projects: link on its own line, and dates inside the title line's
    # separator chain rather than floated right.
    project_link_on_own_line = False
    project_dates_inline = False
    proj_separator: str | None = None
    proj_tail_first = False
    first_proj = profile.projects[0] if profile.projects else None
    if first_proj is not None:
        proj_name_idx = _match_idx(lines, first_proj.name)
        if proj_name_idx is not None:
            proj_line = lines[proj_name_idx]
            proj_text = proj_line.text
            if first_proj.link:
                link_idx = _match_idx(lines, first_proj.link)
                project_link_on_own_line = (
                    link_idx is not None and link_idx != proj_name_idx
                )
            project_dates_inline = _dates_inline(
                proj_text, first_proj.start_date
            )
            proj_detected = _project_separator(proj_text, first_proj)
            if proj_detected:
                proj_separator, proj_tail_first = proj_detected
                if not exp_separator_found:
                    # No experience line to learn the separator from —
                    # the project line's chain is the next best witness.
                    entry_title_separator = proj_separator
            # Same optional project roles as the docx path: the name's run
            # is the title look, a differently styled last run the tail.
            name_at = _offset_after(proj_text, first_proj.name)
            name_pdf = proj_line.style_at(name_at) if name_at >= 0 else proj_line.style
            roles.setdefault(
                ROLE_PROJECT_TITLE, _pdf_style_role(name_pdf, base=_style(proj_line))
            )
            if proj_line.runs and proj_line.runs[-1] is not proj_line.run_at(
                max(name_at, 0)
            ):
                roles.setdefault(
                    ROLE_PROJECT_SUB, _pdf_style_role(proj_line.runs[-1].style)
                )
            if first_proj.description:
                desc_idx = _match_idx(lines, first_proj.description[:48])
                if desc_idx is not None:
                    roles.setdefault(
                        ROLE_PROJECT_BODY, _style(lines[desc_idx])
                    )
            if project_link_on_own_line and first_proj.link:
                link_style = _style(lines[link_idx])
                if link_style.color:
                    roles.setdefault(ROLE_LINK, link_style)

    # Roles from matched lines (first hit wins per role).
    if name_idx is not None:
        roles.setdefault(ROLE_NAME, _style(lines[name_idx]))
    if contact_idx is not None:
        roles.setdefault(ROLE_CONTACT, _style(lines[contact_idx]))
    if location_idx is not None:
        roles.setdefault(ROLE_LOCATION, _style(lines[location_idx]))
    if head_style is not None:
        roles.setdefault(ROLE_ENTRY_TITLE, head_style)
    elif exp_idx:
        roles.setdefault(ROLE_ENTRY_TITLE, _style(lines[exp_idx[0]]))
    if dates_style is not None:
        roles.setdefault(ROLE_DATES, dates_style)
    if summary_idx is not None:
        roles.setdefault(ROLE_BODY, _style(lines[summary_idx]))
    elif edu_idx:
        roles.setdefault(ROLE_BODY, _style(lines[edu_idx[0]]))
    elif skill_idx:
        roles.setdefault(ROLE_BODY, _style(lines[skill_idx[0]]))
    elif bullet_idx:
        roles.setdefault(ROLE_BODY, _style(lines[bullet_idx[0]]))
    # Sub role covers company/dates on entry lines and edu fields: prefer
    # the title line's lighter trailing part, then education lines, else
    # the title itself so dates still match the line they sit on.
    if tail_style is not None:
        roles.setdefault(ROLE_ENTRY_SUB, tail_style)
    elif edu_idx:
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
        **contact,
        entry_title_separator=entry_title_separator,
        entry_title_tail_sub=tail_sub,
        entry_title_tail_first=tail_first,
        education_title_separator=edu_separator,
        education_title_tail_first=edu_tail_first,
        education_title_tail_sub=edu_tail_sub,
        project_title_tail_sub=_project_tail_sub(roles),
        project_title_separator=proj_separator,
        project_title_tail_first=proj_tail_first,
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
        section_header_roles=section_header_roles,
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
    if style.underline:
        font.underline = True
    if style.color:
        font.color.rgb = RGBColor.from_string(style.color)
    return run


def _role_para(doc: _Document, text: str, style: RoleStyle) -> Paragraph:
    para = doc.add_paragraph()
    _apply_role(para, style)
    _write_run(para, text, style)
    return para


def _overlay_link(base: RoleStyle, link: RoleStyle) -> RoleStyle:
    """Link look on top of the surrounding text's style: inherit font and
    size from the base so an 8.5pt link run inside a 12pt contact line
    doesn't snap the line to 8.5pt."""
    merged = RoleStyle(**asdict(link))
    if merged.font_name is None:
        merged.font_name = base.font_name
    if merged.size_pt is None:
        merged.size_pt = base.size_pt
    return merged


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


def _dates(start: str | None, end: str | None, fmt: FormatProfile) -> str:
    """"Jan 2020 – Mar 2022"; an open-ended entry gets the source's open
    label ("Jan 2020 – Present"); an entry with only an end date (a
    certificate completed in December 2025) shows just that date — never a
    dangling separator."""
    start = (start or "").strip()
    end = (end or "").strip()
    if start and end and end != start:
        return f"{start}{fmt.dates_separator}{end}"
    if start and not end:
        if fmt.dates_open_label:
            return f"{start}{fmt.dates_separator}{fmt.dates_open_label}"
        return start
    return end or start


def _entry_header(
    doc: _Document,
    title: str,
    tail: str | None,
    dates: str,
    fmt: FormatProfile,
    title_role: str = ROLE_ENTRY_TITLE,
    sub_role: str = ROLE_ENTRY_SUB,
    sep: str | None = None,
    tail_first: bool = False,
    tail_sub: bool | None = None,
):
    """One entry heading: title + optional tail (company) joined by the
    section's separator in the section's order, dates floated right through
    a tab stop. Styles follow position like the capture: the leading part
    gets the title role, and when the source styles its trailing part
    lighter (the section's tail_sub, else entry_title_tail_sub) that part
    runs in the sub role."""
    title_style = fmt.roles.get(title_role, fmt.role(ROLE_ENTRY_TITLE))
    sub_style = fmt.roles.get(sub_role, fmt.role(ROLE_ENTRY_SUB))
    dates_style = fmt.roles.get(ROLE_DATES, sub_style)
    sep = sep if sep is not None else fmt.entry_title_separator
    closer = _BRACKETS.get(sep.strip(), "")
    if tail_sub is None:
        tail_sub = fmt.entry_title_tail_sub

    def _title_runs(para: Paragraph):
        if not tail:
            _write_run(para, title, title_style)
            return
        lead, trail = (tail, title) if tail_first else (title, tail)
        _write_run(para, lead, title_style)
        _write_run(
            para,
            f"{sep}{trail}{closer}",
            sub_style if tail_sub else title_style,
        )

    if fmt.dates_on_title_line and dates:
        para = doc.add_paragraph()
        _apply_role(para, title_style)
        para.paragraph_format.tab_stops.add_tab_stop(
            Inches(_content_width_in(fmt)), WD_TAB_ALIGNMENT.RIGHT
        )
        _title_runs(para)
        _write_run(para, "\t", dates_style)
        _write_run(para, dates, dates_style)
    else:
        para = doc.add_paragraph()
        _apply_role(para, title_style)
        _title_runs(para)
        if dates:
            _role_para(doc, dates, dates_style)


def _section_header(doc: _Document, section: str, fmt: FormatProfile):
    # Reproduce the blank paragraphs the source puts above the header.
    for _ in range(fmt.section_blank_lines.get(section, 0)):
        blank = doc.add_paragraph()
        _apply_role(blank, fmt.role(ROLE_BODY))
    title = fmt.section_titles.get(section) or DEFAULT_SECTION_TITLES[section]
    _role_para(
        doc,
        title,
        fmt.section_header_roles.get(section, fmt.role(ROLE_SECTION_HEADER)),
    )


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


def _inline_contact(doc: _Document, header: ResumeHeader, fmt: FormatProfile):
    """email | phone | location | links on one line (location optionally
    on its own line below)."""
    contact_bits = [
        bit for bit in [header.email, header.phone] if bit
    ]
    if not fmt.location_on_own_line and header.location:
        contact_bits.append(header.location)
    contact_bits.extend(bit for bit in header.links if bit)
    if contact_bits:
        sep = f" {fmt.contact_separator} "
        contact_style = fmt.role(ROLE_CONTACT)
        link_style = fmt.roles.get(ROLE_LINK)
        para = doc.add_paragraph()
        _apply_role(para, contact_style)
        link_set = set(header.links)
        for i, bit in enumerate(contact_bits):
            if i:
                _write_run(para, sep, contact_style)
            style = (
                _overlay_link(contact_style, link_style)
                if link_style and bit in link_set
                else contact_style
            )
            _write_run(para, bit, style)
    if fmt.location_on_own_line and header.location:
        _role_para(doc, header.location, fmt.role(ROLE_LOCATION))


def _stacked_contact(doc: _Document, header: ResumeHeader, fmt: FormatProfile):
    """One contact field per line in the source's order, each behind its
    captured label ("Phone:"), values tab-aligned when the source aligns
    them. Fields the source didn't show follow in the default order."""
    contact_style = fmt.role(ROLE_CONTACT)
    link_style = fmt.roles.get(ROLE_LINK)
    order = [f for f in fmt.contact_order if f in _CONTACT_FIELDS]
    order += [f for f in _CONTACT_FIELDS if f not in order]
    values = {
        CONTACT_EMAIL: [header.email],
        CONTACT_PHONE: [header.phone],
        CONTACT_LOCATION: [header.location],
        CONTACT_LINKS: list(header.links),
    }
    for name in order:
        style = (
            fmt.role(ROLE_LOCATION) if name == CONTACT_LOCATION else contact_style
        )
        value_style = (
            _overlay_link(style, link_style)
            if name == CONTACT_LINKS and link_style
            else style
        )
        for value in values[name]:
            if not value:
                continue
            para = doc.add_paragraph()
            _apply_role(para, style)
            label = fmt.contact_labels.get(name)
            if label:
                label_style = RoleStyle(**asdict(style))
                label_style.bold = label_style.bold or fmt.contact_label_bold
                if fmt.contact_value_tab_in:
                    para.paragraph_format.tab_stops.add_tab_stop(
                        Inches(fmt.contact_value_tab_in), WD_TAB_ALIGNMENT.LEFT
                    )
                    _write_run(para, f"{label}\t", label_style)
                else:
                    _write_run(para, f"{label} ", label_style)
            _write_run(para, value, value_style)


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
    if fmt.contact_layout == CONTACT_STACKED:
        _stacked_contact(doc, header, fmt)
    else:
        _inline_contact(doc, header, fmt)

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
                    tail_first=fmt.entry_title_tail_first,
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
                    title_role=ROLE_EDUCATION_TITLE,
                    sub_role=ROLE_EDUCATION_SUB,
                    sep=fmt.education_title_separator,
                    tail_first=fmt.education_title_tail_first,
                    tail_sub=fmt.education_title_tail_sub,
                )
                if edu.field_of_study:
                    _role_para(doc, edu.field_of_study, sub_style)
                if edu.description:
                    _role_para(doc, edu.description, body_style)

        elif section_key == SECTION_PROJECTS and content.projects:
            _section_header(doc, section_key, fmt)
            proj_body_style = fmt.roles.get(ROLE_PROJECT_BODY, body_style)
            proj_sep = fmt.project_title_separator or fmt.entry_title_separator
            for proj in content.projects:
                dates = _dates(proj.start_date, proj.end_date, fmt)
                inline_link = (
                    proj.link if not fmt.project_link_on_own_line else None
                )
                if fmt.project_dates_inline:
                    # Dates join the title line's separator chain —
                    # "Name | stack | 2026". A link on that same line joins
                    # the chain too rather than moving to its own line.
                    tail = proj_sep.join(b for b in (inline_link, dates) if b)
                    _entry_header(
                        doc,
                        proj.name,
                        tail or None,
                        "",
                        fmt,
                        title_role=ROLE_PROJECT_TITLE,
                        sub_role=ROLE_PROJECT_SUB,
                        sep=proj_sep,
                        tail_first=fmt.project_title_tail_first,
                        tail_sub=fmt.project_title_tail_sub,
                    )
                else:
                    _entry_header(
                        doc,
                        proj.name,
                        inline_link,
                        dates,
                        fmt,
                        title_role=ROLE_PROJECT_TITLE,
                        sub_role=ROLE_PROJECT_SUB,
                        sep=proj_sep,
                        tail_first=fmt.project_title_tail_first,
                        tail_sub=fmt.project_title_tail_sub,
                    )
                if fmt.project_link_on_own_line and proj.link:
                    link_style = fmt.roles.get(ROLE_LINK)
                    _role_para(
                        doc,
                        proj.link,
                        _overlay_link(sub_style, link_style)
                        if link_style
                        else sub_style,
                    )
                if proj.description:
                    _role_para(doc, proj.description, proj_body_style)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
