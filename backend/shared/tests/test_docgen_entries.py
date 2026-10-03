"""Entry-line and header capture/render: date ranges without a start.
"""

import io
import unittest

import docx
from shared.docgen import (
    ResumeContent,
    ResumeEducation,
    ResumeExperience,
    ResumeHeader,
    ResumeProject,
    _dates,
    default_format_profile,
    render_docx,
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
