"""Randomized resume PDF generator for the pdf parse → capture → render
pipeline (issue #49 and follow-ups).

Not collected by pytest (no test_ prefix) and needs reportlab + pillow, so
run it by hand from backend/dispatcher:

    uv run --with reportlab --with pillow python \\
        tests/fixtures/gen_resume_pdfs.py --out /tmp/corpus --seeds 0-299 --check

Every seed deterministically picks a layout (single column, left/right
sidebar of varying size, balanced two columns, scanned page) and styling
(fonts, title/company order and separators per section, bold attribution,
drawn or literal bullets, contact block style, Form XObject wrapping,
non-Latin names, long URLs, multi-page entries, blank pages), then writes
<name>.pdf plus a <name>.json manifest describing what was drawn where.
tests/pdf_corpus.py checks parse/capture/render against the manifest;
--check runs it over the corpus. --fixtures rewrites the curated
regression subset in tests/fixtures/generated/ (test_pdf_corpus.py).
"""

import argparse
import io
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = letter
FONT_DIR = Path("/usr/share/fonts/truetype")
TTF = {
    "DejaVuSans": FONT_DIR / "dejavu/DejaVuSans.ttf",
    "DejaVuSans-Bold": FONT_DIR / "dejavu/DejaVuSans-Bold.ttf",
    "DroidCJK": FONT_DIR / "droid/DroidSansFallbackFull.ttf",
}
HAVE_TTF = {name for name, path in TTF.items() if path.exists()}
for _name in HAVE_TTF:
    pdfmetrics.registerFont(TTFont(_name, str(TTF[_name])))

FAMILIES = {
    "helvetica": ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique"),
    "times": ("Times-Roman", "Times-Bold", "Times-Italic"),
}
GLYPH_FONT = "DejaVuSans"  # ●, ▪ aren't in the standard fonts' encoding

FIRST = ["Jane", "Marcus", "Priya", "Tomas", "Aiko", "Olu", "Greta", "Rafael"]
LAST = ["Doe", "Okafor", "Lindqvist", "Moreau", "Tanaka", "Haddad", "Novak"]
SPECIAL_NAMES = ["Zoë Ørsted", "José Núñez", "李明"]
TITLES = [
    "Senior Software Engineer", "Product Manager", "Data Analyst",
    "Operations Coordinator", "Executive Assistant", "Marketing Specialist",
    "Backend Developer", "UX Designer", "Project Manager", "Support Engineer",
    "Financial Analyst", "Shift Lead",
]
COMPANIES = [
    "Acme Robotics", "Northwind Traders", "Globex Corporation", "Initech",
    "Umbrella Health", "Stark Logistics", "Wayne Analytics", "Hooli",
    "Vandelay Industries", "Soylent Foods", "Cyberdyne Labs", "Tyrell Systems",
    "Pied Piper", "Massive Dynamic",
]
VERBS = [
    "Led", "Built", "Designed", "Automated", "Coordinated", "Reduced",
    "Launched", "Streamlined", "Negotiated", "Migrated", "Mentored", "Audited",
]
OBJECTS = [
    "the quarterly planning cycle", "a customer onboarding portal",
    "vendor contracts across three regions", "the nightly reporting jobs",
    "an internal analytics dashboard", "the support escalation process",
    "a team of five contractors", "inventory tracking for two warehouses",
    "the billing reconciliation workflow", "a mobile ordering experience",
    "the hiring pipeline for interns", "cloud spend reviews",
]
RESULTS = [
    "cutting turnaround time by 30%", "saving roughly 12 hours per week",
    "lifting retention by 8 points", "with zero missed deadlines",
    "while keeping costs flat", "ahead of the fiscal year close",
    "and documented every step for handoff", "raising satisfaction scores to 4.8",
]
SKILLS = [
    "Python", "TypeScript", "PostgreSQL", "Kubernetes", "Terraform", "GraphQL",
    "Redis", "Docker", "Kafka", "Figma", "Excel", "Tableau", "Salesforce",
    "Jira", "Scrum", "Budgeting", "Forecasting", "Copywriting",
]
CATEGORIES = ["Languages", "Tools", "Platforms", "Methods"]
SCHOOLS = [
    "State University", "Lakeside College", "Northern Institute of Technology",
    "Riverside Community College", "University of Westfield",
]
DEGREES = [
    "BS Computer Science", "BA Economics", "MBA", "MS Data Science",
    "Associate of Arts", "Project Management Certificate",
]
PROJECTS = ["Widgetizer", "Trailmap", "Ledgerly", "Bramble", "Quillpad"]
LANGUAGES = ["English (native)", "Spanish (fluent)", "German (basic)", "Japanese (conversational)"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"]

EXP_SEPARATORS = [" - ", " | ", ", ", " at ", " — ", " – ", " · "]
EDU_SEPARATORS = [" - ", ", ", " | ", " ("]
PROJ_SEPARATORS = [" | ", " - ", " — "]
DATE_SEPARATORS = [" – ", " - ", " — "]
BULLET_STYLES = ["circle", "square", "hollow", "•", "●", "▪", "-", "none"]


def width(text: str, font: str, size: float) -> float:
    return pdfmetrics.stringWidth(text, font, size)


def wrap(text: str, font: str, size: float, max_w: float) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and width(trial, font, size) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


class Span:
    def __init__(self, text, font, size, color=(0, 0, 0)):
        self.text, self.font, self.size, self.color = text, font, size, color

    @property
    def w(self):
        return width(self.text, self.font, self.size)


class Resume:
    """Draw ops per page plus the manifest units describing them."""

    def __init__(self, rng: random.Random, name: str):
        self.rng = rng
        self.name = name
        self.pages: list[list] = [[]]
        self.units: list[dict] = []
        self.seq: dict[str, int] = defaultdict(int)
        self.joins = 0
        self.forms = 0
        self.wrap_forms = False

    def op(self, page: int, fn):
        while len(self.pages) <= page:
            self.pages.append([])
        self.pages[page].append(fn)

    def unit(self, text, page, band, flow, kind, section=None, join=None, glyph=None):
        self.seq[flow] += 1
        self.units.append(
            {
                "id": len(self.units),
                "text": text,
                "page": page,
                "band": band,
                "flow": flow,
                "seq": self.seq[flow],
                "kind": kind,
                "section": section,
                "join": join,
                "glyph": glyph,
            }
        )

    def new_join(self) -> str:
        self.joins += 1
        return f"j{self.joins}"

    def spans(self, page, x, y, spans, form=None):
        """Draw spans left to right from x on baseline y; Form XObject
        wrapping (like Canva/Word exports) when requested."""
        use_form = self.wrap_forms if form is None else form

        def fn(c, spans=spans, x=x, y=y):
            cx = x
            for s in spans:
                c.setFont(s.font, s.size)
                c.setFillColorRGB(*s.color)
                c.drawString(cx, y, s.text)
                cx += s.w

        if use_form:
            self.forms += 1
            name = f"Fm{self.forms}"

            def wrapped(c, fn=fn, name=name):
                c.beginForm(name)
                fn(c)
                c.endForm()
                c.doForm(name)

            self.op(page, wrapped)
        else:
            self.op(page, fn)

    def shape(self, page, kind, x, y, size, color=(0, 0, 0)):
        def fn(c):
            c.setFillColorRGB(*color)
            c.setStrokeColorRGB(*color)
            c.setLineWidth(0.6)
            if kind == "circle":
                c.circle(x + size / 2, y + size / 2, size / 2, stroke=0, fill=1)
            elif kind == "square":
                c.rect(x, y, size, size, stroke=0, fill=1)
            elif kind == "hollow":
                c.circle(x + size / 2, y + size / 2, size / 2, stroke=1, fill=0)
            elif kind == "roundrect":
                c.roundRect(x, y, size, size, size / 4, stroke=0, fill=1)
            elif kind == "envelope":
                c.rect(x, y, size * 1.3, size, stroke=1, fill=0)
                c.line(x, y + size, x + size * 0.65, y + size * 0.4)
                c.line(x + size * 0.65, y + size * 0.4, x + size * 1.3, y + size)
            elif kind == "pin":
                p = c.beginPath()
                p.moveTo(x + size / 2, y)
                p.lineTo(x, y + size * 0.6)
                p.curveTo(x, y + size * 1.2, x + size, y + size * 1.2, x + size, y + size * 0.6)
                p.close()
                c.drawPath(p, stroke=0, fill=1)

        self.op(page, fn)

    def underlay(self, page, x, y, w, h, color):
        """A filled panel drawn before the page's other ops."""

        def fn(c):
            c.setFillColorRGB(*color)
            c.rect(x, y, w, h, stroke=0, fill=1)

        self.op(page, lambda c: None)
        self.pages[page].insert(0, fn)
        self.pages[page].pop()

    def hrule(self, page, x0, x1, y, color=(0.3, 0.3, 0.3)):
        def fn(c):
            c.setStrokeColorRGB(*color)
            c.setLineWidth(0.8)
            c.line(x0, y, x1, y)

        self.op(page, fn)

    def render(self) -> bytes:
        buf = io.BytesIO()
        # invariant: fixed dates/ids, so a seed always yields the same bytes.
        c = canvas.Canvas(buf, pagesize=letter, pageCompression=1, invariant=1)
        c.setTitle(self.name)
        for ops in self.pages:
            for fn in ops:
                fn(c)
            c.showPage()
        c.save()
        return buf.getvalue()


class Flow:
    """A column of text that runs top-down and may continue on the next
    page (same x range, from `cont_top`)."""

    def __init__(self, doc, band, flow, x0, x1, top, page=0, bottom=54, cont_top=None, can_break=True):
        self.doc, self.band, self.flow = doc, band, flow
        self.x0, self.x1 = x0, x1
        self.y = top
        self.page = page
        self.bottom = bottom
        self.cont_top = cont_top if cont_top is not None else PAGE_H - 54
        self.can_break = can_break

    @property
    def w(self):
        return self.x1 - self.x0

    def advance(self, leading: float) -> tuple[int, float]:
        """Baseline for the next row (breaking to a new page if needed)."""
        if self.y - leading < self.bottom:
            if not self.can_break:
                raise OverflowError(self.flow)
            self.page += 1
            self.y = self.cont_top
        self.y -= leading
        return self.page, self.y

    def gap(self, pts: float):
        self.y -= pts


class Style:
    def __init__(self, rng: random.Random):
        fam = rng.choice(list(FAMILIES))
        self.regular, self.bold, self.italic = FAMILIES[fam]
        self.size = rng.choice([9.5, 10, 10.5, 11])
        self.leading = self.size * rng.choice([1.25, 1.3, 1.4])
        self.header_size = self.size + rng.choice([1, 2, 3])
        self.header_color = rng.choice([(0, 0, 0), (0.0, 0.21, 0.43), (0.0, 0.42, 0.27)])
        self.rule_under_header = rng.random() < 0.5
        self.bullet = rng.choice(BULLET_STYLES)
        if self.bullet in ("●", "▪") and GLYPH_FONT not in HAVE_TTF:
            self.bullet = "•"
        self.date_sep = rng.choice(DATE_SEPARATORS)
        self.open_label = rng.choice(["Present", "Current"])

    def span(self, text, weight="regular", size=None, color=(0, 0, 0)):
        font = {"regular": self.regular, "bold": self.bold, "italic": self.italic}[weight]
        return Span(text, font, size or self.size, color)


class Builder:
    """Content model + layout for one seed."""

    def __init__(self, seed: int):
        self.seed = seed
        rng = self.rng = random.Random(seed)
        self.st = Style(rng)
        self.doc = Resume(rng, f"seed{seed}")
        self.doc.wrap_forms = rng.random() < 0.35
        self.expect: dict = {}
        self.features: list[str] = []
        if self.doc.wrap_forms:
            self.features.append("form-xobjects")
        # --- content
        special = rng.random() < 0.2
        name = rng.choice(SPECIAL_NAMES) if special else f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        if name == "李明" and "DroidCJK" not in HAVE_TTF:
            name = "Zoë Ørsted"
        if special:
            self.features.append(f"name:{name}")
        handle = f"user{seed}"
        self.basic = {
            "name": name,
            "email": f"{handle}@example.com",
            "phone": f"({rng.randint(200, 989)}) {rng.randint(200, 989)}-{rng.randint(1000, 9999)}",
            "location": rng.choice(["Denver, CO", "Austin, Texas", "Portland, OR", "Grand Rapids, Michigan"]),
            "links": [f"linkedin.com/in/{handle}"] if rng.random() < 0.5 else [],
        }
        titles = rng.sample(TITLES, len(TITLES))
        companies = rng.sample(COMPANIES, len(COMPANIES))
        # A quarter of the résumés run long enough to spill onto page two,
        # usually splitting an entry's bullets across the break.
        long_doc = rng.random() < 0.25
        n_exp = rng.choice([6, 7, 8]) if long_doc else rng.choice([1, 2, 3, 3, 4, 5])
        max_bullets = 6 if long_doc else 4
        bullets = self._bullets(n_exp * max_bullets)
        self.experience = []
        year = 2025
        for i in range(n_exp):
            start_y = year - rng.randint(1, 3)
            start = f"{rng.choice(MONTHS)} {start_y}"
            end = None if i == 0 and rng.random() < 0.6 else f"{rng.choice(MONTHS)} {year}"
            year = start_y
            self.experience.append(
                {
                    "company": companies[i],
                    "position": titles[i],
                    "start_date": start,
                    "end_date": end,
                    "bullets": [bullets.pop() for _ in range(rng.randint(1, max_bullets))],
                }
            )
        self.exp_order = rng.choice(["title_first", "company_first"])
        seps = EXP_SEPARATORS if self.exp_order == "title_first" else [s for s in EXP_SEPARATORS if s != " at "]
        self.exp_sep = rng.choice(seps)
        self.exp_weights = rng.choice([("bold", "regular"), ("bold", "italic"), ("bold", "bold")])
        self.two_line_entries = rng.random() < 0.15
        n_edu = rng.choice([0, 1, 1, 2])
        schools = rng.sample(SCHOOLS, len(SCHOOLS))
        degrees = rng.sample(DEGREES, len(DEGREES))
        self.education = []
        for i in range(n_edu):
            only_end = rng.random() < 0.35
            end_y = rng.randint(2008, 2025)
            self.education.append(
                {
                    "institution": schools[i],
                    "degree": degrees[i],
                    "field_of_study": None,
                    "start_date": "" if only_end else str(end_y - 4),
                    "end_date": f"{rng.choice(['May', 'December', 'June'])} {end_y}" if only_end else str(end_y),
                    "description": None,
                }
            )
        self.edu_order = rng.choice(["degree_first", "institution_first"])
        edu_seps = EDU_SEPARATORS if self.edu_order == "degree_first" else [s for s in EDU_SEPARATORS if s != " ("]
        self.edu_sep = rng.choice(edu_seps)
        n_proj = rng.choice([0, 0, 1, 2])
        self.projects = []
        for name_ in rng.sample(PROJECTS, n_proj):
            long_url = rng.random() < 0.3
            link = (
                f"https://github.com/{handle}/{name_.lower()}-with-an-unusually-long-repository-name/tree/main/packages/core"
                if long_url
                else f"github.com/{handle}/{name_.lower()}"
            )
            if long_url:
                self.features.append("long-url")
            self.projects.append(
                {
                    "name": name_,
                    "link": link,
                    "description": f"{name_} turns {rng.choice(OBJECTS)} into a weekly digest.",
                    "start_date": str(rng.randint(2019, 2025)),
                    "end_date": None,
                }
            )
        self.proj_sep = rng.choice(PROJ_SEPARATORS)
        self.link_own_line = rng.random() < 0.4
        skills = rng.sample(SKILLS, rng.randint(4, 10))
        self.skills_style = rng.choice(["flat", "categories", "grid"])
        if self.skills_style == "categories":
            cats = rng.sample(CATEGORIES, 2)
            half = len(skills) // 2
            self.skills = [
                {"category": cats[0], "skills": skills[:half]},
                {"category": cats[1], "skills": skills[half:]},
            ]
        else:
            self.skills = [{"category": "", "skills": skills}]
        self.summary = (
            f"Generalist with a record of {rng.choice(RESULTS)} who owns "
            f"{rng.choice(OBJECTS)} end to end and keeps stakeholders informed."
        )

    def _bullets(self, n):
        out = set()
        while len(out) < n:
            out.add(
                f"{self.rng.choice(VERBS)} {self.rng.choice(OBJECTS)} "
                f"{self.rng.choice(RESULTS)}"
            )
        return sorted(out)

    # ---------- drawing primitives ----------

    def header(self, fl: Flow, title: str, section: str):
        st = self.st
        fl.gap(st.size * 0.8)
        page, y = fl.advance(st.header_size * 1.3)
        self.doc.spans(page, fl.x0, y, [st.span(title, "bold", st.header_size, st.header_color)])
        self.doc.unit(title, page, fl.band, fl.flow, "header", section)
        if st.rule_under_header:
            self.doc.hrule(page, fl.x0, fl.x1, y - 4)
            fl.gap(4)

    def text_lines(self, fl: Flow, text: str, section: str, kind="text", weight="regular", size=None):
        st = self.st
        size = size or st.size
        for line in wrap(text, st.span("", weight).font, size, fl.w):
            page, y = fl.advance(size * (st.leading / st.size))
            self.doc.spans(page, fl.x0, y, [st.span(line, weight, size)])
            self.doc.unit(line, page, fl.band, fl.flow, kind, section)

    def bullet_item(self, fl: Flow, text: str, section: str, style: str | None = None):
        st = self.st
        style = style or st.bullet
        indent = 14
        lines = wrap(text, st.regular, st.size, fl.w - indent)
        for i, line in enumerate(lines):
            page, y = fl.advance(st.leading)
            glyph = None
            if i == 0 and style != "none":
                if style in ("circle", "square", "hollow"):
                    d = st.size * 0.3
                    self.doc.shape(page, style, fl.x0 + 3, y + st.size * 0.33 - d / 2, d)
                    glyph = {"circle": "•", "square": "▪", "hollow": "○"}[style]
                else:
                    # "•" stays in the standard font: reportlab encodes it
                    # as WinAnsi code 127 (pdfminer: "(cid:127)").
                    font = GLYPH_FONT if style in ("●", "▪") else st.regular
                    self.doc.spans(page, fl.x0 + 2, y, [Span(style, font, st.size)])
                    glyph = style
            self.doc.spans(page, fl.x0 + indent, y, [st.span(line)])
            self.doc.unit(line, page, fl.band, fl.flow, "bullet", section, glyph=glyph)

    def entry_row(self, fl: Flow, spans: list[Span], right: str | None, section: str, kind="title"):
        """A row: spans at the left, optional right-floated text (dates,
        location) on the same baseline — drawn as separate strings, read
        as one line."""
        st = self.st
        page, y = fl.advance(st.leading * 1.1)
        self.doc.spans(page, fl.x0, y, spans)
        text = "".join(s.text for s in spans)
        join = self.doc.new_join() if right else None
        self.doc.unit(text, page, fl.band, fl.flow, kind, section, join=join)
        if right:
            rs = st.span(right, "regular")
            self.doc.spans(page, fl.x1 - rs.w, y, [rs])
            self.doc.unit(right, page, fl.band, fl.flow, "date", section, join=join)

    def date_text(self, start, end) -> str:
        st = self.st
        if start and end:
            return f"{start}{st.date_sep}{end}"
        if start:
            return f"{start}{st.date_sep}{st.open_label}"
        return end

    # ---------- sections ----------

    def experience_section(self, fl: Flow):
        st = self.st
        self.header(fl, "EXPERIENCE", "experience")
        head_w, tail_w = self.exp_weights
        for e in self.experience:
            fl.gap(st.size * 0.4)
            dates = self.date_text(e["start_date"], e["end_date"])
            if self.two_line_entries:
                self.entry_row(fl, [st.span(e["position"], "bold")], dates, "experience")
                self.entry_row(
                    fl, [st.span(e["company"], "italic")], self.basic["location"], "experience", kind="sub"
                )
            else:
                lead, trail = (
                    (e["company"], e["position"])
                    if self.exp_order == "company_first"
                    else (e["position"], e["company"])
                )
                spans = [st.span(lead, head_w), st.span(f"{self.exp_sep}{trail}", tail_w)]
                total = sum(s.w for s in spans) + width(dates, st.regular, st.size) + 24
                if total <= fl.w:
                    self.entry_row(fl, spans, dates, "experience")
                else:
                    self.entry_row(fl, spans, None, "experience")
                    self.text_lines(fl, dates, "experience", kind="date")
            for b in e["bullets"]:
                self.bullet_item(fl, b, "experience")
        if self.two_line_entries:
            # Company on its own line: no separator to learn (capture
            # falls back to the project line's or the default), and the
            # render joins title and company in the title style.
            self.expect["experience"] = {
                "separator": None, "tail_first": False, "tail_sub": False,
                "head_bold": True, "tail_bold": True,
            }
        else:
            self.expect["experience"] = {
                "separator": self.exp_sep,
                "tail_first": self.exp_order == "company_first",
                "tail_sub": head_w != tail_w,
                "head_bold": head_w == "bold",
                "tail_bold": tail_w == "bold",
            }
        first_bullets = [
            u for u in self.doc.units if u["section"] == "experience" and u["kind"] == "bullet"
        ]
        matchable = any(
            any(u["text"].startswith(b[:48]) for u in first_bullets)
            for e in self.experience
            for b in e["bullets"][:2]
        )
        if matchable:
            self.expect["bullet_glyph"] = {
                "circle": "•", "square": "▪", "hollow": "○", "none": None,
            }.get(st.bullet, st.bullet)

    def education_section(self, fl: Flow):
        if not self.education:
            return
        st = self.st
        self.header(fl, "EDUCATION", "education")
        for e in self.education:
            fl.gap(st.size * 0.3)
            lead, trail = (
                (e["institution"], e["degree"])
                if self.edu_order == "institution_first"
                else (e["degree"], e["institution"])
            )
            closer = ")" if self.edu_sep == " (" else ""
            spans = [st.span(lead, "bold"), st.span(f"{self.edu_sep}{trail}{closer}", "regular")]
            dates = self.date_text(e["start_date"], e["end_date"])
            if sum(s.w for s in spans) + width(dates, st.regular, st.size) + 24 <= fl.w:
                self.entry_row(fl, spans, dates, "education")
            else:
                self.entry_row(fl, spans, None, "education")
                self.text_lines(fl, dates, "education", kind="date")
        self.expect["education"] = {
            "separator": self.edu_sep,
            "tail_first": self.edu_order == "institution_first",
            "head_bold": True,
            "tail_bold": False,
        }

    def projects_section(self, fl: Flow):
        if not self.projects:
            return
        st = self.st
        self.header(fl, "PROJECTS", "projects")
        for p in self.projects:
            fl.gap(st.size * 0.3)
            link_size = st.size
            long_link = width(p["link"], st.regular, st.size) > fl.w * 0.55
            own_line = self.link_own_line or long_link
            if own_line:
                self.entry_row(fl, [st.span(p["name"], "bold")], p["start_date"], "projects")
                while width(p["link"], st.regular, link_size) > fl.w and link_size > 5:
                    link_size -= 0.5
                page, y = fl.advance(st.leading)
                self.doc.spans(page, fl.x0, y, [st.span(p["link"], size=link_size, color=(0.07, 0.33, 0.8))])
                self.doc.unit(p["link"], page, fl.band, fl.flow, "link", "projects")
            else:
                spans = [st.span(p["name"], "bold"), st.span(f"{self.proj_sep}{p['link']}")]
                self.entry_row(fl, spans, p["start_date"], "projects")
            self.text_lines(fl, p["description"], "projects")
        if not (self.link_own_line or any(
            width(p["link"], st.regular, st.size) > fl.w * 0.55 for p in self.projects
        )):
            self.expect["projects"] = {
                "separator": self.proj_sep, "tail_first": False,
                "head_bold": True, "tail_bold": False,
            }

    def skills_section(self, fl: Flow, grid_ok=True):
        st = self.st
        self.header(fl, "SKILLS", "skills")
        if self.skills_style == "categories":
            for cat in self.skills:
                spans = [st.span(f"{cat['category']}: ", "bold"), st.span(", ".join(cat["skills"]))]
                if sum(s.w for s in spans) <= fl.w:
                    page, y = fl.advance(st.leading)
                    self.doc.spans(page, fl.x0, y, spans)
                    self.doc.unit("".join(s.text for s in spans), page, fl.band, fl.flow, "skill", "skills")
                else:
                    self.text_lines(fl, f"{cat['category']}: {', '.join(cat['skills'])}", "skills", kind="skill")
        elif self.skills_style == "grid" and grid_ok:
            self.features.append("skills-grid")
            items = self.skills[0]["skills"]
            col_w = fl.w / 2
            left = Flow(self.doc, fl.band, f"{fl.flow}-gridL", fl.x0, fl.x0 + col_w - 16, fl.y, fl.page, can_break=False)
            right = Flow(self.doc, fl.band, f"{fl.flow}-gridR", fl.x0 + col_w, fl.x1, fl.y, fl.page, can_break=False)
            rows = (len(items) + 1) // 2
            if fl.y - rows * st.leading < fl.bottom:
                fl.page += 1
                fl.y = fl.cont_top
                left.page = right.page = fl.page
                left.y = right.y = fl.y
            for i in range(rows):
                for col, idx in ((left, i), (right, rows + i)):
                    if idx < len(items):
                        self.bullet_item(col, items[idx], "skills", style="circle" if st.bullet in ("circle", "square", "hollow") else "none")
                    else:
                        col.advance(st.leading)
            fl.y = min(left.y, right.y)
        else:
            self.text_lines(fl, ", ".join(self.skills[0]["skills"]), "skills", kind="skill")

    def summary_section(self, fl: Flow):
        self.header(fl, "SUMMARY", "summary")
        self.text_lines(fl, self.summary, "summary")

    # ---------- header / contact ----------

    def name_span(self, size):
        name = self.basic["name"]
        if name == "李明":
            return Span(name, "DroidCJK", size)
        return self.st.span(name, "bold", size)

    def contact_block(self, fl: Flow, style: str):
        """Contact fields: inline joined row, or stacked lines — plain,
        "Label: value", a tab-aligned label column, or icons."""
        st = self.st
        b = self.basic
        fields = [("email", b["email"]), ("phone", b["phone"]), ("location", b["location"])]
        self.rng.shuffle(fields)
        links = list(b["links"])
        if style == "inline":
            text = " | ".join([v for _, v in fields] + links)
            if width(text, st.regular, st.size) > fl.w:
                text = " | ".join(v for _, v in fields)
                links = []
                b["links"] = []
            page, y = fl.advance(st.leading)
            self.doc.spans(page, fl.x0, y, [st.span(text)])
            self.doc.unit(text, page, fl.band, fl.flow, "contact", "header")
            self.expect["contact_layout"] = "inline"
            return
        labels = {"email": "Email:", "phone": "Phone:", "location": "Address:"}
        label_w = max(width(v, st.bold, st.size) for v in labels.values()) + self.rng.choice([10, 18, 26])
        icon = self.rng.choice(["circle", "roundrect", "envelope", "pin"])
        expect_labels = {}

        def fitted(text, room):
            # Narrow sidebars shrink long values (emails) instead of letting
            # them run into the next column.
            size = st.size
            while width(text, st.regular, size) > room and size > 6:
                size -= 0.5
            return size

        for key, value in fields + [("links", link) for link in links]:
            page, y = fl.advance(st.leading)
            if style == "labels" and key != "links":
                text = f"{labels[key]} {value}"
                size = fitted(text, fl.w - 6)
                self.doc.spans(
                    page, fl.x0, y,
                    [st.span(f"{labels[key]} ", "bold", size), st.span(value, size=size)],
                )
                self.doc.unit(text, page, fl.band, fl.flow, "contact", "header")
                expect_labels[key] = labels[key]
            elif style == "label-grid" and key != "links":
                join = self.doc.new_join()
                self.doc.spans(page, fl.x0, y, [st.span(labels[key], "bold")])
                self.doc.unit(labels[key], page, fl.band, fl.flow, "label", "header", join=join)
                size = fitted(value, fl.w - label_w)
                self.doc.spans(page, fl.x0 + label_w, y, [st.span(value, size=size)])
                self.doc.unit(value, page, fl.band, fl.flow, "contact", "header", join=join)
                expect_labels[key] = labels[key]
            elif style == "icons":
                dot = 5.0
                self.doc.shape(page, icon, fl.x0, y + st.size * 0.33 - dot / 2, dot, color=(0.2, 0.2, 0.2))
                size = fitted(value, fl.w - 12)
                self.doc.spans(page, fl.x0 + 12, y, [st.span(value, size=size)])
                self.doc.unit(value, page, fl.band, fl.flow, "contact", "header")
            else:
                size = fitted(value, fl.w)
                self.doc.spans(page, fl.x0, y, [st.span(value, size=size)])
                self.doc.unit(value, page, fl.band, fl.flow, "contact", "header")
        self.expect["contact_layout"] = "stacked"
        self.expect["contact_labels"] = expect_labels
        self.expect["contact_order"] = [k for k, _ in fields]
        if style == "icons":
            self.features.append(f"contact-icons:{icon}")
        self.features.append(f"contact:{style}")

    def name_row(self, fl: Flow, size):
        page, y = fl.advance(size * 1.2)
        span = self.name_span(size)
        self.doc.spans(page, fl.x0, y, [span])
        self.doc.unit(self.basic["name"], page, fl.band, fl.flow, "name", "header")

    # ---------- layouts ----------

    def build(self) -> tuple[bytes, dict]:
        rng = self.rng
        layout = rng.choice(
            ["single", "single", "single", "left_sidebar", "right_sidebar",
             "left_sidebar", "right_sidebar", "two_column", "name_beside_contact"]
        )
        if self.seed % 37 == 36:
            layout = "scanned"
        self.layout = layout
        getattr(self, f"layout_{layout}")()
        if layout != "scanned" and rng.random() < 0.12:
            self.doc.pages.append([])
            self.expect.setdefault("textless_pages", []).append(len(self.doc.pages) - 1)
            self.features.append("blank-page")
        self.expect["pages"] = len(self.doc.pages)
        pdf = self.doc.render()
        manifest = {
            "seed": self.seed,
            "layout": layout,
            "features": self.features,
            "units": self.doc.units,
            "expect": self.expect,
            "profile": None
            if layout == "scanned"
            else {
                "summary": self.summary,
                "basic_info": self.basic,
                "experience": self.experience,
                "skills": self.skills,
                "education": self.education,
                "projects": self.projects,
            },
        }
        return pdf, manifest

    def layout_single(self):
        st = self.st
        margin = self.rng.choice([40, 54, 72])
        fl = Flow(self.doc, "full", "main", margin, PAGE_W - margin, PAGE_H - margin)
        self.name_row(fl, st.size + 10)
        self.contact_block(fl, self.rng.choice(["inline", "labels", "label-grid", "icons", "plain"]))
        order = ["summary", "experience", "skills", "education", "projects"]
        if self.rng.random() < 0.5:
            order = ["summary", "skills", "experience", "projects", "education"]
        for section in order:
            getattr(self, f"{section}_section")(fl)

    def layout_name_beside_contact(self):
        st = self.st
        margin = 54
        top = PAGE_H - margin
        name_fl = Flow(self.doc, "full", "name", margin, PAGE_W / 2, top, can_break=False)
        self.name_row(name_fl, st.size + 12)
        contact_fl = Flow(self.doc, "full", "contact", PAGE_W * 0.62, PAGE_W - margin, top, can_break=False)
        self.contact_block(contact_fl, self.rng.choice(["plain", "icons", "labels"]))
        fl = Flow(self.doc, "full", "main", margin, PAGE_W - margin, min(name_fl.y, contact_fl.y) - 6)
        self.features.append("name-beside-contact")
        for section in ("summary", "experience", "skills", "education", "projects"):
            getattr(self, f"{section}_section")(fl)

    def _sidebar(self, side: str):
        rng = self.rng
        st = self.st
        side_w = rng.choice([110, 130, 150, 170])
        gutter = rng.choice([20, 26, 34])
        margin = 36
        full_header = rng.random() < 0.5
        top = PAGE_H - margin
        if full_header:
            hdr = Flow(self.doc, "full", "header", margin, PAGE_W - margin, top, can_break=False)
            self.name_row(hdr, st.size + 10)
            self.contact_block(hdr, "inline")
            top = hdr.y - 14
        if side == "left":
            side_x0, side_x1 = margin, margin + side_w
            main_x0, main_x1 = side_x1 + gutter, PAGE_W - margin
        else:
            main_x0, main_x1 = margin + 14, PAGE_W - margin - side_w - gutter
            side_x0, side_x1 = PAGE_W - margin - side_w, PAGE_W - margin
        if rng.random() < 0.5:
            # Tinted sidebar panel, painted under everything else.
            self.doc.underlay(
                0, side_x0 - 8, 0, side_x1 - side_x0 + 16, PAGE_H, (0.93, 0.95, 0.98)
            )
            self.features.append("sidebar-panel")
        side_fl = Flow(self.doc, "side", "side", side_x0, side_x1, top, can_break=False)
        main_fl = Flow(self.doc, "main", "main", main_x0, main_x1, top, cont_top=PAGE_H - margin)
        if not full_header:
            self.name_row(main_fl, st.size + 8)
            self.contact_block(side_fl, rng.choice(["plain", "labels", "icons"]))
        # Sidebar size varies a lot: nothing but a contact stub up to a
        # long list — the short ones are what column_gutter misses.
        size = rng.choice(["tiny", "short", "medium", "long"])
        self.features.append(f"{side}-sidebar:{size}:w{side_w}")
        side_size = st.size - rng.choice([0, 0, 0.5, 1.5])
        if size != "tiny":
            self.header(side_fl, "SKILLS", "skills")
            items = [s for c in self.skills for s in c["skills"]]
            items = items[: {"short": 4, "medium": 8, "long": 12}[size]]
            self.skills = [{"category": "", "skills": items}]
            for item in items:
                self.text_lines(side_fl, item, "skills", kind="skill", size=side_size)
        else:
            self.skills = []
        if size in ("medium", "long"):
            self.header(side_fl, "LANGUAGES", "languages")
            for lang in LANGUAGES[: rng.randint(2, 4)]:
                self.text_lines(side_fl, lang, "languages", size=side_size)
        if size == "long":
            self.header(side_fl, "INTERESTS", "interests")
            for hobby in ("Trail running", "Film photography", "Community garden", "Chess club"):
                self.text_lines(side_fl, hobby, "interests", size=side_size)
        self.summary_section(main_fl)
        self.experience_section(main_fl)
        self.education_section(main_fl)
        self.projects_section(main_fl)

    def layout_left_sidebar(self):
        self._sidebar("left")

    def layout_right_sidebar(self):
        self._sidebar("right")

    def layout_two_column(self):
        st = self.st
        margin = 40
        hdr = Flow(self.doc, "full", "header", margin, PAGE_W - margin, PAGE_H - margin, can_break=False)
        self.name_row(hdr, st.size + 10)
        self.contact_block(hdr, "inline")
        top = hdr.y - 16
        mid = PAGE_W / 2
        left = Flow(self.doc, "main", "left", margin, mid - 14, top, can_break=False)
        right = Flow(self.doc, "side", "right", mid + 14, PAGE_W - margin, top, can_break=False)
        self.experience = self.experience[:3]
        self.summary_section(left)
        self.experience_section(left)
        self.skills_style = "flat" if self.skills_style == "grid" else self.skills_style
        self.skills_section(right)
        self.education_section(right)
        self.projects_section(right)
        self.features.append("two-column")

    def layout_scanned(self):
        """An image-only page — no text layer at all."""
        from PIL import Image, ImageDraw

        img = Image.new("L", (510, 660), 255)
        draw = ImageDraw.Draw(img)
        for i in range(40):
            y = 30 + i * 15
            draw.rectangle([40, y, 40 + self.rng.randint(150, 430), y + 7], fill=40)

        def fn(c, img=img):
            c.drawImage(ImageReader(img), 51, 66, 510, 660)

        self.doc.op(0, fn)
        self.expect["textless_pages"] = [0]
        self.features.append("scanned")


def generate(seed: int) -> tuple[bytes, dict]:
    for attempt in range(20):
        try:
            return Builder(seed * 1000 + attempt).build()
        except OverflowError:
            continue
    raise RuntimeError(f"seed {seed}: no layout fit")


def parse_seeds(spec: str) -> list[int]:
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


# Seeds whose PDFs are committed under tests/fixtures/generated — each one
# covers a layout family the regression tests must keep passing.
FIXTURE_SEEDS: dict[int, str] = {
    0: "left_sidebar_short_icons",
    6: "left_sidebar_tiny_pins",
    101: "right_sidebar_two_pages",
    235: "right_sidebar_labelled_contact",
    4: "two_column",
    477: "label_grid_skills_grid_brackets",
    298: "name_beside_icon_contact",
    85: "form_xobjects_icons_grid",
    565: "cjk_name_long_url",
    36: "scanned_no_text",
    125: "entry_split_across_pages",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path("/tmp/resume-corpus"))
    ap.add_argument("--seeds", default="0-99")
    ap.add_argument("--check", action="store_true", help="run tests/pdf_corpus.py checks")
    ap.add_argument("--fixtures", action="store_true", help="rewrite tests/fixtures/generated")
    args = ap.parse_args()

    here = Path(__file__).resolve()
    sys.path.insert(0, str(here.parents[2]))  # backend/dispatcher, for tests.pdf_corpus
    if args.fixtures:
        target = here.parent / "generated"
        target.mkdir(exist_ok=True)
        for seed, label in FIXTURE_SEEDS.items():
            pdf, manifest = generate(seed)
            manifest["label"] = label
            (target / f"{label}.pdf").write_bytes(pdf)
            (target / f"{label}.json").write_text(
                json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
            print(f"{label}: seed {seed}, {len(pdf)} bytes")
        return

    args.out.mkdir(parents=True, exist_ok=True)
    failures = 0
    stats: dict[str, int] = defaultdict(int)
    for seed in parse_seeds(args.seeds):
        pdf, manifest = generate(seed)
        stem = f"seed{seed:04d}-{manifest['layout']}"
        (args.out / f"{stem}.pdf").write_bytes(pdf)
        (args.out / f"{stem}.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
        stats[manifest["layout"]] += 1
        if args.check:
            from tests.pdf_corpus import check_pdf

            try:
                problems = check_pdf(pdf, manifest)
            except Exception as exc:  # report and keep going
                problems = [f"crash: {exc!r}"]
            if problems:
                failures += 1
                print(f"FAIL {stem} {manifest['features']}")
                for p in problems[:8]:
                    print(f"    {p}")
    print(f"{sum(stats.values())} pdfs: {dict(stats)}")
    if args.check:
        print(f"{failures} failing")
        sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
