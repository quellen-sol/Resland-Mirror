"""Entry-line and header capture/render: per-section title order and
separator, date ranges without a start, and loading profiles written by
older or newer capturers.
"""

import io
import json
import unittest
from dataclasses import asdict, dataclass, field

import docx
from docx import Document
from shared.docgen import (
    FormatProfile,
    ResumeContent,
    ResumeEducation,
    ResumeExperience,
    ResumeHeader,
    ResumeProject,
    _dates,
    _title_separator,
    capture_format_profile,
    capture_format_profile_pdf,
    default_format_profile,
    render_docx,
)
from shared.pdfdoc import PdfDoc, PdfLine, PdfPage, PdfRun, PdfStyle


@dataclass
class _Basic:
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    links: list = field(default_factory=list)


@dataclass
class _Bullet:
    text: str


@dataclass
class _Exp:
    company: str
    position: str
    start_date: str
    end_date: str | None
    bullets: list = field(default_factory=list)


@dataclass
class _Edu:
    institution: str
    degree: str
    field_of_study: str = ""
    start_date: str = ""
    end_date: str | None = None
    description: str = ""


@dataclass
class _Proj:
    name: str
    link: str | None
    description: str
    start_date: str
    end_date: str | None


@dataclass
class _Profile:
    summary: str | None
    basic_info: _Basic
    experience: list = field(default_factory=list)
    skills: list = field(default_factory=list)
    education: list = field(default_factory=list)
    projects: list = field(default_factory=list)


def _profile() -> _Profile:
    return _Profile(
        summary=None,
        basic_info=_Basic(
            name="Jane Doe", email="jane@x.com", phone="555-1234", location="Denver, CO"
        ),
        experience=[
            _Exp("Acme Corp", "Software Engineer", "Jan 2020", None, [_Bullet("Built the thing")])
        ],
        education=[_Edu("State University", "BS", start_date="2016", end_date="2020")],
        projects=[
            _Proj("Widgetizer", "github.com/jane/widgetizer", "A widget tool", "2021", None)
        ],
    )


def _content() -> ResumeContent:
    return ResumeContent(
        header=ResumeHeader(
            name="Jane Doe", email="jane@x.com", phone="555-1234", location="Denver, CO"
        ),
        experiences=[
            ResumeExperience("Acme Corp", "Software Engineer", "Jan 2020", None, ["Built the thing"])
        ],
        education=[ResumeEducation("State University", "BS", "", "2016", "2020")],
        projects=[
            ResumeProject("Widgetizer", "github.com/jane/widgetizer", "A widget tool", "2021", None)
        ],
    )


def _paras(blob: bytes):
    return [p for p in docx.Document(io.BytesIO(blob)).paragraphs if p.text.strip()]


def _para(paras, needle):
    return next(p for p in paras if needle in p.text)


def _runs(para, *spec):
    """Add runs (text, bold, italic) to a docx paragraph."""
    for text, bold, italic in spec:
        run = para.add_run(text)
        run.font.bold = bold
        run.font.italic = italic


def _company_first_doc() -> Document:
    """Company-first experience (company bold), title-first education with
    a comma, project with a pipe — each section its own convention."""
    doc = Document()
    doc.add_paragraph("Jane Doe")
    doc.add_paragraph("jane@x.com | 555-1234 | Denver, CO")
    doc.add_paragraph("EXPERIENCE")
    _runs(
        doc.add_paragraph(),
        ("Acme Corp", True, False),
        (" - Software Engineer", False, False),
        ("\tJan 2020 – Present", False, False),
    )
    doc.add_paragraph("• Built the thing")
    doc.add_paragraph("EDUCATION")
    _runs(
        doc.add_paragraph(),
        ("BS", True, False),
        (", State University", False, True),
        ("\t2016 – 2020", False, False),
    )
    doc.add_paragraph("PROJECTS")
    _runs(
        doc.add_paragraph(),
        ("Widgetizer", True, False),
        (" | github.com/jane/widgetizer", False, False),
        ("\t2021", False, False),
    )
    doc.add_paragraph("A widget tool")
    return doc


def _pdf_line(text, top, runs=None, *, size=11.0, bold=False, x0=72.0, gap=4.0):
    style = PdfStyle(font_name="Helvetica", size_pt=size, bold=bold)
    return PdfLine(
        text=text,
        page=0,
        x0=x0,
        x1=540.0,
        top=top,
        bottom=top + size + 2,
        style=style,
        gap_before_pt=gap,
        runs=runs or [],
    )


def _run(text, bold=False, italic=False, color=None, x0=None):
    return PdfRun(
        text=text,
        style=PdfStyle(
            font_name="Helvetica", size_pt=11.0, bold=bold, italic=italic, color=color
        ),
        x0=x0,
    )


def _company_first_pdf() -> PdfDoc:
    """The same resume as pdf IR lines carrying style runs."""
    lines = [
        _pdf_line("Jane Doe", 60, size=22, bold=True),
        _pdf_line("jane@x.com | 555-1234 | Denver, CO", 90),
        _pdf_line("EXPERIENCE", 120, bold=True),
        _pdf_line(
            "Acme Corp - Software Engineer    Jan 2020 – Present",
            140,
            [
                _run("Acme Corp", bold=True),
                _run(" - Software Engineer    "),
                _run("Jan 2020 – Present", color="666666", x0=450),
            ],
        ),
        _pdf_line("• Built the thing", 156, x0=90),
        _pdf_line("EDUCATION", 180, bold=True),
        _pdf_line(
            "BS, State University    2016 – 2020",
            200,
            [_run("BS", bold=True), _run(", State University    ", italic=True), _run("2016 – 2020", x0=470)],
        ),
        _pdf_line("PROJECTS", 224, bold=True),
        _pdf_line(
            "Widgetizer | github.com/jane/widgetizer    2021",
            244,
            [_run("Widgetizer", bold=True), _run(" | github.com/jane/widgetizer    2021")],
        ),
        _pdf_line("A widget tool", 260),
    ]
    return PdfDoc(pages=[PdfPage(number=0, width=612.0, height=792.0, lines=lines)])


class FormatProfileCompat(unittest.TestCase):
    def test_profile_from_before_these_fields_loads_with_old_behavior(self):
        old = asdict(default_format_profile())
        for key in [k for k in old if k.startswith(("education_title", "project_title"))]:
            del old[key]
        del old["entry_title_tail_first"]
        fmt = FormatProfile.from_dict(json.loads(json.dumps(old)))
        self.assertIsNone(fmt.education_title_separator)
        # Education/projects fall back to the experience separator and the
        # title-first order, as before.
        paras = _paras(render_docx(_content(), fmt))
        self.assertTrue(_para(paras, "State University").text.startswith("BS — State University"))
        self.assertTrue(_para(paras, "Widgetizer").text.startswith("Widgetizer — github.com"))
        self.assertTrue(_para(paras, "jane@x.com").text.startswith("jane@x.com | 555-1234"))

    def test_unknown_keys_from_a_newer_capturer_are_ignored(self):
        """The API loads profiles the dispatcher wrote; a newer dispatcher
        must not make an older API fall back to the default look."""
        data = json.loads(default_format_profile().to_json())
        data["entry_title_future_knob"] = True
        data["roles"]["name"]["kerning"] = 0.2
        data["section_header_roles"] = {"skills": {"bold": True, "glow": 1}}
        fmt = FormatProfile.from_dict(data)
        self.assertTrue(fmt.roles["name"].bold)
        self.assertTrue(fmt.section_header_roles["skills"].bold)


class TitleSeparator(unittest.TestCase):
    def test_variants(self):
        cases = [
            ("Engineer — Acme", "Engineer", "Acme", (" — ", False)),
            ("Acme - Engineer    2020", "Engineer", "Acme", (" - ", True)),
            ("Engineer, Acme", "Engineer", "Acme", (", ", False)),
            ("Engineer at Acme", "Engineer", "Acme", (" at ", False)),
            ("ACME CORP | Engineer", "Engineer", "Acme Corp", (" | ", True)),
            # Bracketed institution: "( … )" — the renderer adds the ")".
            ("In Progress: Certificate (Coursera) | Expected", "Certificate", "Coursera", (" (", False)),
            # A tech stack between name and date: the joining token.
            ("VATMissions | Go, React | 2026", "VATMissions", "2026", (" | ", False)),
        ]
        for text, head, tail, want in cases:
            with self.subTest(text=text):
                self.assertEqual(_title_separator(text, head, tail), want)

    def test_date_range_dash_is_not_a_title_separator(self):
        # Company on the next line: the only dash is inside the dates.
        self.assertIsNone(
            _title_separator("Software Engineer    Jan 2020 – Present", "Software Engineer", "Acme")
        )

    def test_strict_needs_both_parts(self):
        self.assertIsNone(_title_separator("Widgetizer | Go", "Widgetizer", "2026", strict=True))
        self.assertEqual(_title_separator("Widgetizer | Go", "Widgetizer", "2026"), (" | ", False))


class SectionScopedOrder(unittest.TestCase):
    """Finding B: the company-first order learned from experience must not
    flip education or project lines."""

    def _check(self, fmt):
        self.assertEqual(fmt.entry_title_separator, " - ")
        self.assertTrue(fmt.entry_title_tail_first)
        self.assertEqual(fmt.education_title_separator, ", ")
        self.assertFalse(fmt.education_title_tail_first)
        self.assertEqual(fmt.project_title_separator, " | ")
        self.assertFalse(fmt.project_title_tail_first)
        paras = _paras(render_docx(_content(), fmt))
        self.assertTrue(_para(paras, "Software Engineer").text.startswith("Acme Corp - Software Engineer"))
        self.assertTrue(_para(paras, "State University").text.startswith("BS, State University"))
        self.assertTrue(_para(paras, "Widgetizer").text.startswith("Widgetizer | github.com/jane/widgetizer"))

    def test_docx(self):
        self._check(capture_format_profile(_company_first_doc(), _profile()))

    def test_pdf(self):
        self._check(capture_format_profile_pdf(_company_first_pdf(), _profile()))

    def test_education_order_detected_on_its_own(self):
        doc = Document()
        doc.add_paragraph("Jane Doe")
        doc.add_paragraph("EDUCATION")
        doc.add_paragraph("State University - BS    2016 – 2020")
        profile = _profile()
        profile.experience = []
        profile.projects = []
        fmt = capture_format_profile(doc, profile)
        self.assertTrue(fmt.education_title_tail_first)
        paras = _paras(render_docx(_content(), fmt))
        self.assertTrue(_para(paras, "BS").text.startswith("State University - BS"))
        # Experience keeps the default title-first order.
        self.assertTrue(_para(paras, "Acme").text.startswith("Software Engineer"))

    def test_bracketed_institution_renders_closed(self):
        fmt = default_format_profile()
        fmt.education_title_separator = " ("
        paras = _paras(render_docx(_content(), fmt))
        self.assertTrue(_para(paras, "State University").text.startswith("BS (State University)"))

    def test_experience_not_found_does_not_crash_capture(self):
        """The profile's experience isn't in the document but a project
        line is — capture used to read an unset exp_text here."""
        doc = Document()
        doc.add_paragraph("Jane Doe")
        doc.add_paragraph("Widgetizer | github.com/jane/widgetizer")
        profile = _profile()
        profile.experience[0].position = "Not In Doc"
        profile.experience[0].company = "Nowhere Inc"
        fmt = capture_format_profile(doc, profile)
        self.assertEqual(fmt.entry_title_separator, " | ")


class Dates(unittest.TestCase):
    """Finding F: a missing start date never leaves a dangling dash."""

    def test_dates(self):
        fmt = default_format_profile()
        self.assertEqual(_dates("", "December 2025", fmt), "December 2025")
        self.assertEqual(_dates(None, "December 2025", fmt), "December 2025")
        self.assertEqual(_dates("Jan 2020", None, fmt), "Jan 2020 – Present")
        self.assertEqual(_dates("Jan 2020", "Mar 2022", fmt), "Jan 2020 – Mar 2022")
        self.assertEqual(_dates("2026", "2026", fmt), "2026")
        self.assertEqual(_dates("", None, fmt), "")
        self.assertEqual(_dates("", "Present", fmt), "Present")
        fmt.dates_open_label = None
        self.assertEqual(_dates("Jan 2020", None, fmt), "Jan 2020")

    def test_render_education_without_start(self):
        content = _content()
        content.education[0].start_date = ""
        content.education[0].end_date = "December 2025"
        para = _para(_paras(render_docx(content, default_format_profile())), "State University")
        self.assertTrue(para.text.endswith("\tDecember 2025"))
        self.assertNotIn("– December", para.text)

    def test_render_entry_without_any_dates(self):
        content = _content()
        content.education[0].start_date = ""
        content.education[0].end_date = None
        para = _para(_paras(render_docx(content, default_format_profile())), "State University")
        self.assertEqual(para.text, "BS — State University")


if __name__ == "__main__":
    unittest.main()
