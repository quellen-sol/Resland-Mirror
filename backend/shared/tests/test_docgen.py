"""Docgen capture/render tests — stdlib unittest, no extra deps.

Run: .venv/bin/python -m unittest backend.shared.tests.test_docgen -v
     (from the repo root with the workspace venv)
"""

import io
import json
import unittest
from dataclasses import dataclass, field

import docx
from docx import Document
from docx.shared import Pt

from shared.docgen import (
    ALL_ROLES,
    ROLE_NAME,
    SECTION_EDUCATION,
    SECTION_EXPERIENCE,
    SECTION_SKILLS,
    SECTION_SUMMARY,
    FormatProfile,
    ResumeContent,
    ResumeEducation,
    ResumeExperience,
    ResumeHeader,
    ResumeSkillGroup,
    capture_format_profile,
    content_source_hash,
    default_format_profile,
    render_docx,
)


# Duck-typed stand-in for the parser's UserDocxProfile — capture only reads
# attributes, so anything shaped the same works.


@dataclass
class _Basic:
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""


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
class _Cat:
    category: str
    skills: list


@dataclass
class _Edu:
    institution: str
    degree: str
    field_of_study: str
    start_date: str
    end_date: str | None
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


def _sample_profile() -> _Profile:
    return _Profile(
        summary="Engineer who ships.",
        basic_info=_Basic(
            name="Jane Doe", email="jane@x.com", phone="555-1", location="NYC"
        ),
        experience=[
            _Exp(
                company="Acme",
                position="Senior Engineer",
                start_date="Jan 2020",
                end_date=None,
                bullets=[_Bullet("Built the thing"), _Bullet("Shipped it too")],
            )
        ],
        skills=[_Cat(category="Languages", skills=["Python", "Go"])],
        education=[
            _Edu(
                institution="MIT",
                degree="BS",
                field_of_study="CS",
                start_date="2016",
                end_date="2020",
            )
        ],
        projects=[
            _Proj(
                name="Side",
                link="side.dev",
                description="toy",
                start_date="2021",
                end_date=None,
            )
        ],
    )


def _resume_doc() -> Document:
    doc = Document()
    name_para = doc.add_paragraph()
    run = name_para.add_run("Jane Doe")
    run.font.size = Pt(24)
    run.font.bold = True
    doc.add_paragraph("jane@x.com | 555-1 | NYC")
    doc.add_paragraph("SUMMARY")
    doc.add_paragraph("Engineer who ships.")
    doc.add_paragraph("EXPERIENCE")
    doc.add_paragraph("Senior Engineer — Acme    Jan 2020 – Present")
    doc.add_paragraph("• Built the thing")
    doc.add_paragraph("• Shipped it too")
    doc.add_paragraph("SKILLS")
    doc.add_paragraph("Languages: Python, Go")
    doc.add_paragraph("EDUCATION")
    doc.add_paragraph("BS — MIT    2016 – 2020")
    doc.add_paragraph("CS")
    return doc


def _sample_content() -> ResumeContent:
    return ResumeContent(
        header=ResumeHeader(
            name="Jane Doe",
            email="jane@x.com",
            phone="555-1",
            location="NYC",
            links=["github.com/jane"],
        ),
        summary="Engineer who ships.",
        experiences=[
            ResumeExperience(
                company="Acme",
                title="Senior Engineer",
                start_date="Jan 2020",
                end_date=None,
                bullets=["Built the thing", "Shipped it too"],
            )
        ],
        skill_groups=[ResumeSkillGroup(category="Languages", skills=["Python", "Go"])],
        education=[
            ResumeEducation(
                institution="MIT",
                degree="BS",
                field_of_study="CS",
                start_date="2016",
                end_date="2020",
            )
        ],
        projects=[],
    )


class FormatProfileSerialization(unittest.TestCase):
    def test_json_roundtrip(self):
        fmt = default_format_profile()
        restored = FormatProfile.from_json(fmt.to_json())
        self.assertEqual(restored, fmt)

    def test_from_dict_restores_role_styles(self):
        fmt = default_format_profile()
        restored = FormatProfile.from_dict(json.loads(fmt.to_json()))
        self.assertEqual(
            restored.roles[ROLE_NAME].size_pt, fmt.roles[ROLE_NAME].size_pt
        )


class Capture(unittest.TestCase):
    def setUp(self):
        self.fmt = capture_format_profile(_resume_doc(), _sample_profile())

    def test_captures_all_roles(self):
        for role in ALL_ROLES:
            self.assertIn(role, self.fmt.roles, f"missing role {role}")

    def test_captures_name_style(self):
        self.assertEqual(self.fmt.roles[ROLE_NAME].size_pt, 24.0)
        self.assertTrue(self.fmt.roles[ROLE_NAME].bold)

    def test_captures_section_order_and_titles(self):
        self.assertEqual(
            self.fmt.section_order[:4],
            [
                SECTION_SUMMARY,
                SECTION_EXPERIENCE,
                SECTION_SKILLS,
                SECTION_EDUCATION,
            ],
        )
        self.assertEqual(self.fmt.section_titles[SECTION_EXPERIENCE], "EXPERIENCE")

    def test_captures_bullet_glyph(self):
        self.assertEqual(self.fmt.bullet_glyph, "•")

    def test_captures_contact_separator(self):
        self.assertEqual(self.fmt.contact_separator, "|")

    def test_serializes_to_json(self):
        # The DB stores fmt.to_json() — it must round-trip without loss.
        self.assertEqual(FormatProfile.from_json(self.fmt.to_json()), self.fmt)


class Render(unittest.TestCase):
    def _texts(self, blob: bytes) -> list[str]:
        doc = docx.Document(io.BytesIO(blob))
        return [p.text for p in doc.paragraphs if p.text.strip()]

    def test_roundtrip_contains_content(self):
        content = _sample_content()
        blob = render_docx(content, default_format_profile())
        texts = self._texts(blob)
        joined = "\n".join(texts)
        for expected in [
            "Jane Doe",
            "jane@x.com",
            "github.com/jane",
            "SUMMARY",
            "Engineer who ships.",
            "EXPERIENCE",
            "Senior Engineer — Acme",
            "Jan 2020 – Present",
            "• Built the thing",
            "SKILLS",
            "Python, Go",
            "EDUCATION",
            "BS — MIT",
        ]:
            self.assertIn(expected, joined)

    def test_section_order_follows_format(self):
        content = _sample_content()
        fmt = default_format_profile()
        fmt.section_order = [
            SECTION_EDUCATION,
            SECTION_EXPERIENCE,
            SECTION_SKILLS,
            SECTION_SUMMARY,
        ]
        texts = self._texts(render_docx(content, fmt))
        self.assertLess(texts.index("EDUCATION"), texts.index("EXPERIENCE"))

    def test_skips_empty_sections(self):
        content = _sample_content()
        content.summary = None
        content.projects = []
        texts = self._texts(render_docx(content, default_format_profile()))
        self.assertNotIn("SUMMARY", texts)
        self.assertNotIn("PROJECTS", texts)

    def test_grouped_skills_render_categories(self):
        content = _sample_content()
        content.skill_groups = [
            ResumeSkillGroup(category="Languages", skills=["Python"]),
            ResumeSkillGroup(category="Tools", skills=["Docker"]),
        ]
        fmt = default_format_profile()
        fmt.skills_layout = "grouped"
        texts = "\n".join(self._texts(render_docx(content, fmt)))
        self.assertIn("Languages: Python", texts)
        self.assertIn("Tools: Docker", texts)


class SourceHash(unittest.TestCase):
    def test_stable_for_identical_content(self):
        self.assertEqual(
            content_source_hash(_sample_content()),
            content_source_hash(_sample_content()),
        )

    def test_changes_when_content_changes(self):
        a = _sample_content()
        b = _sample_content()
        b.experiences[0].bullets[0] = "Rebuilt the thing"
        self.assertNotEqual(content_source_hash(a), content_source_hash(b))

    def test_changes_when_summary_dropped(self):
        a = _sample_content()
        b = _sample_content()
        b.summary = None
        self.assertNotEqual(content_source_hash(a), content_source_hash(b))


if __name__ == "__main__":
    unittest.main()
