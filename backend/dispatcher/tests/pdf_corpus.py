"""Property checks for generated resume PDFs (fixtures/gen_resume_pdfs.py).

Each generated PDF ships with a JSON manifest: every text unit the
generator drew (text, page, band — main column, sidebar, or full width —
reading-order flow, and which units share a visual line on purpose, like a
title and its right-floated date), the profile the parse agent would
extract, and what capture should detect. `check_pdf` runs parse → capture
→ render and returns human-readable problems (empty list = pass):

- every unit's text is parsed exactly as often as it was drawn;
- units share a parsed line only when drawn to (no sidebar/main fusion);
- each flow (a column, one column of a grid) reads in drawn order, the
  sidebar and main column don't interleave on a page, and each section's
  units sit after its header with no other header in between;
- bullet prefixes appear exactly on the units drawn with a bullet;
- capture detects each section's separator and order, the bullet glyph,
  and the contact layout;
- render_docx keeps each section's part order and bold attribution.

Not a test module itself: test_pdf_corpus.py runs it on the committed
fixtures, and the generator's --check runs it on a fresh corpus.
"""

import io
import re
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import pairwise
from typing import Any

BULLET_GLYPHS = ("•", "●", "▪", "○", "□", "-", "–", "·", "*", "►", "‣")


# Duck-typed stand-ins for the parser's UserDocxProfile — capture only
# reads attributes.


@dataclass
class Bullet:
    text: str


@dataclass
class Basic:
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    links: list = field(default_factory=list)


@dataclass
class Exp:
    company: str
    position: str
    start_date: str
    end_date: str | None
    bullets: list = field(default_factory=list)


@dataclass
class Cat:
    category: str
    skills: list


@dataclass
class Edu:
    institution: str
    degree: str
    field_of_study: str | None = None
    start_date: str = ""
    end_date: str | None = None
    description: str | None = None


@dataclass
class Proj:
    name: str
    link: str | None
    description: str
    start_date: str
    end_date: str | None


@dataclass
class Profile:
    summary: str | None
    basic_info: Basic
    experience: list = field(default_factory=list)
    skills: list = field(default_factory=list)
    education: list = field(default_factory=list)
    projects: list = field(default_factory=list)


def profile_from_manifest(manifest: dict[str, Any]) -> Profile:
    p = manifest["profile"]
    return Profile(
        summary=p.get("summary"),
        basic_info=Basic(**p["basic_info"]),
        experience=[
            Exp(
                company=e["company"],
                position=e["position"],
                start_date=e["start_date"],
                end_date=e["end_date"],
                bullets=[Bullet(b) for b in e["bullets"]],
            )
            for e in p["experience"]
        ],
        skills=[Cat(c["category"], c["skills"]) for c in p["skills"]],
        education=[Edu(**e) for e in p["education"]],
        projects=[Proj(**pr) for pr in p["projects"]],
    )


def content_from_manifest(manifest: dict[str, Any]):
    from shared.docgen import (
        ResumeContent,
        ResumeEducation,
        ResumeExperience,
        ResumeHeader,
        ResumeProject,
        ResumeSkillGroup,
    )

    p = manifest["profile"]
    basic = p["basic_info"]
    return ResumeContent(
        header=ResumeHeader(
            name=basic["name"],
            email=basic["email"] or None,
            phone=basic["phone"] or None,
            location=basic["location"] or None,
            links=list(basic["links"]),
        ),
        summary=p.get("summary"),
        experiences=[
            ResumeExperience(
                company=e["company"],
                title=e["position"],
                start_date=e["start_date"],
                end_date=e["end_date"],
                bullets=list(e["bullets"]),
            )
            for e in p["experience"]
        ],
        skill_groups=[
            ResumeSkillGroup(category=c["category"] or None, skills=c["skills"])
            for c in p["skills"]
        ],
        education=[
            ResumeEducation(
                institution=e["institution"],
                degree=e["degree"],
                field_of_study=e.get("field_of_study") or "",
                start_date=e.get("start_date") or "",
                end_date=e.get("end_date"),
            )
            for e in p["education"]
        ],
        projects=[ResumeProject(**pr) for pr in p["projects"]],
    )


def _find_all(haystack: str, needle: str) -> list[int]:
    hits, start = [], 0
    while needle and (j := haystack.find(needle, start)) >= 0:
        hits.append(j)
        start = j + 1
    return hits


def check_parse(doc, manifest: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    texts = [line.text for line in doc.lines]
    pages = [line.page for line in doc.lines]
    units = manifest["units"]
    by_id = {u["id"]: u for u in units}

    expect_pages = manifest["expect"].get("pages")
    if expect_pages is not None and len(doc.pages) != expect_pages:
        problems.append(f"pages: drawn {expect_pages}, parsed {len(doc.pages)}")
    for page in manifest["expect"].get("textless_pages", []):
        if any(p == page for p in pages):
            problems.append(f"page {page} should have no text lines")

    # 1. Each unit parsed as often as drawn; remember unique positions.
    pos: dict[int, tuple[int, int]] = {}
    for u in units:
        drawn = sum(len(_find_all(o["text"], u["text"])) for o in units)
        hits = [(i, j) for i, t in enumerate(texts) for j in _find_all(t, u["text"])]
        if len(hits) != drawn:
            problems.append(
                f"unit {u['text']!r} drawn {drawn}x, parsed {len(hits)}x"
            )
        elif drawn == 1:
            pos[u["id"]] = hits[0]

    # 2. Units share a parsed line only when drawn to.
    on_line: dict[int, list[int]] = defaultdict(list)
    for uid, (li, _) in pos.items():
        on_line[li].append(uid)
    for li, uids in on_line.items():
        joins = {by_id[uid]["join"] or f"#{uid}" for uid in uids}
        if len(joins) > 1:
            problems.append(f"line fuses separate units: {texts[li]!r}")
    joined: dict[str, set[int]] = defaultdict(set)
    for uid, (li, _) in pos.items():
        if by_id[uid]["join"]:
            joined[by_id[uid]["join"]].add(li)
    for lis in joined.values():
        if len(lis) > 1:
            problems.append(
                "units meant for one line split: "
                + " / ".join(repr(texts[li]) for li in sorted(lis))
            )

    # 3a. Each flow reads in drawn order.
    flows: dict[str, list[dict]] = defaultdict(list)
    for u in units:
        if u["id"] in pos:
            flows[u["flow"]].append(u)
    for flow, members in flows.items():
        members.sort(key=lambda u: u["seq"])
        for a, b in pairwise(members):
            if pos[a["id"]] >= pos[b["id"]]:
                problems.append(
                    f"flow {flow}: {a['text']!r} should read before {b['text']!r}"
                )
                break

    # 3b. Sidebar and main column don't interleave on a page.
    by_page: dict[int, list[dict]] = defaultdict(list)
    for u in units:
        if u["id"] in pos and u["band"] in ("main", "side"):
            by_page[u["page"]].append(u)
    for page, members in by_page.items():
        members.sort(key=lambda u: pos[u["id"]])
        bands = [u["band"] for u in members]
        switches = sum(1 for a, b in pairwise(bands) if a != b)
        if switches > 1:
            problems.append(f"page {page}: sidebar/main interleave ({switches} switches)")

    # 3c. Sections stay contiguous behind their headers.
    headers = {
        u["section"]: u["id"] for u in units if u["kind"] == "header" and u["id"] in pos
    }
    for section, hid in headers.items():
        members = [
            pos[u["id"]] for u in units if u["section"] == section and u["id"] in pos
        ]
        lo, hi = min(members), max(members)
        if lo != pos[hid]:
            problems.append(f"section {section}: content before its header")
        for other, oid in headers.items():
            if other != section and lo < pos[oid] < hi:
                problems.append(f"section {section}: header {other} inside it")

    # 4. Bullet prefixes exactly where bullets were drawn.
    for uid, (li, off) in pos.items():
        u = by_id[uid]
        prefix = texts[li][:off]
        if u["glyph"]:
            if not re.fullmatch(rf"{re.escape(u['glyph'])}\s+", prefix):
                problems.append(f"bullet {u['glyph']!r} missing: {texts[li]!r}")
        elif prefix.strip() in BULLET_GLYPHS and prefix.strip():
            problems.append(f"unexpected bullet prefix: {texts[li]!r}")
    return problems


def _run_with(para, text: str):
    for run in para.runs:
        if text and text[: min(len(text), 12)] in run.text:
            return run
    return None


def _check_entry_render(paras, label, head, tail, sep, closer, expect) -> list[str]:
    para = next(
        (p for p in paras if head in p.text and tail in p.text), None
    )
    if para is None:
        return [f"render {label}: no paragraph with {head!r} and {tail!r}"]
    problems = []
    want = f"{head}{sep}{tail}{closer}"
    if not para.text.startswith(want):
        problems.append(f"render {label}: {para.text!r} should start {want!r}")
    for part, key in ((head, "head_bold"), (tail, "tail_bold")):
        if key not in expect:
            continue
        run = _run_with(para, part)
        if run is None or bool(run.font.bold) != expect[key]:
            problems.append(
                f"render {label}: {part!r} bold should be {expect[key]}"
            )
    return problems


def check_capture_render(doc, manifest: dict[str, Any]) -> list[str]:
    from docx import Document
    from shared.docgen import (
        FormatProfile,
        capture_format_profile_pdf,
        render_docx,
    )

    problems: list[str] = []
    expect = manifest["expect"]
    profile = profile_from_manifest(manifest)
    fmt = capture_format_profile_pdf(doc, profile)
    if FormatProfile.from_json(fmt.to_json()) != fmt:
        problems.append("format profile doesn't round-trip through JSON")

    exp = expect.get("experience")
    if exp:
        exp = dict(exp)
        if exp["separator"] is None:
            # Nothing to learn it from on the source line — whatever
            # capture fell back to, the render must use it.
            exp["separator"] = fmt.entry_title_separator
        got = (fmt.entry_title_separator, fmt.entry_title_tail_first)
        if got != (exp["separator"], exp["tail_first"]):
            problems.append(f"capture experience order/separator {got} != {exp}")
        if "tail_sub" in exp and fmt.entry_title_tail_sub != exp["tail_sub"]:
            problems.append(f"capture tail_sub {fmt.entry_title_tail_sub} != {exp['tail_sub']}")
    edu = expect.get("education")
    if edu:
        got = (fmt.education_title_separator, fmt.education_title_tail_first)
        if got != (edu["separator"], edu["tail_first"]):
            problems.append(f"capture education order/separator {got} != {edu}")
    proj = expect.get("projects")
    if proj:
        got = (fmt.project_title_separator, fmt.project_title_tail_first)
        if got != (proj["separator"], proj["tail_first"]):
            problems.append(f"capture project order/separator {got} != {proj}")
    if "bullet_glyph" in expect and fmt.bullet_glyph != expect["bullet_glyph"]:
        problems.append(f"capture bullet glyph {fmt.bullet_glyph!r} != {expect['bullet_glyph']!r}")
    if "contact_layout" in expect:
        if fmt.contact_layout != expect["contact_layout"]:
            problems.append(f"capture contact layout {fmt.contact_layout} != {expect['contact_layout']}")
        elif fmt.contact_labels != expect.get("contact_labels", {}):
            problems.append(f"capture contact labels {fmt.contact_labels} != {expect.get('contact_labels')}")

    content = content_from_manifest(manifest)
    rendered = Document(io.BytesIO(render_docx(content, fmt)))
    paras = rendered.paragraphs
    if exp:
        for e in content.experiences[:2]:
            head, tail = (e.company, e.title) if exp["tail_first"] else (e.title, e.company)
            problems += _check_entry_render(
                paras, "experience", head, tail, exp["separator"], "", exp
            )
    if edu:
        sep = edu["separator"]
        closer = {"(": ")", "[": "]"}.get(sep.strip(), "")
        for e in content.education[:2]:
            head, tail = (e.institution, e.degree) if edu["tail_first"] else (e.degree, e.institution)
            problems += _check_entry_render(paras, "education", head, tail, sep, closer, edu)
    if proj:
        for pr in content.projects[:2]:
            if not pr.link or fmt.project_link_on_own_line:
                continue
            problems += _check_entry_render(
                paras, "project", pr.name, pr.link, proj["separator"], "", proj
            )
    texts = [p.text for p in paras]
    for e in content.education:
        if not e.start_date and e.end_date:
            # The entry's own paragraph, or the dates line right below it.
            at = [i for i, t in enumerate(texts) if e.degree in t and e.institution in t]
            near = [texts[j] for i in at for j in (i, i + 1) if j < len(texts)]
            if not any(t.endswith(e.end_date) for t in near):
                problems.append(f"render: education end date {e.end_date!r} missing")
            if any(f"{fmt.dates_separator}{e.end_date}" in t for t in near):
                problems.append(f"render: dangling date separator before {e.end_date!r}")
    if expect.get("contact_layout") == "stacked":
        basic = content.header
        for name in expect["contact_order"]:
            value = {"email": basic.email, "phone": basic.phone, "location": basic.location}.get(name)
            label = expect.get("contact_labels", {}).get(name)
            para = next(
                (p for p in paras if p.text.endswith(value or "\0") and (not label or p.text.startswith(label))),
                None,
            )
            if value and para is None:
                problems.append(f"render: stacked contact line for {name} missing")
            elif value and label and (
                # Bold labels, plain values — like the source draws them.
                not para.runs[0].font.bold or para.runs[-1].font.bold
            ):
                problems.append(f"render: contact {name} label/value bold mixed up")
    return problems


def check_pdf(pdf_bytes: bytes, manifest: dict[str, Any]) -> list[str]:
    from dispatcher.doc_parsers.pdf import parse_pdf

    doc = parse_pdf(pdf_bytes)
    problems = check_parse(doc, manifest)
    if manifest["profile"] is not None:
        problems += check_capture_render(doc, manifest)
    return problems
