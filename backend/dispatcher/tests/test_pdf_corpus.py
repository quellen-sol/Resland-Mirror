"""Regression tests over generated resume PDFs (fixtures/generated/).

Each PDF was drawn by fixtures/gen_resume_pdfs.py (reportlab — not needed
here) beside a JSON manifest of what it drew where; pdf_corpus.check_pdf
runs parse → capture → render against it (see that module for the
properties). The subset covers the layout families the pipeline must keep
handling: short/tiny sidebars on either side (the column-fusion
regression), a page break inside an entry under a right sidebar, a
balanced two-column page, a label grid + skills grid, a name beside an
icon contact stack, Form XObject text (issue #49), a CJK name with a long
URL, and an image-only page.

Regenerate (after a deliberate generator change):
    uv run --with reportlab --with pillow python \\
        tests/fixtures/gen_resume_pdfs.py --fixtures
"""

import json
import unittest
from pathlib import Path

from .pdf_corpus import check_pdf

try:
    import pdfminer.layout  # noqa: F401

    HAS_PDFMINER = True
except ImportError:
    HAS_PDFMINER = False

GENERATED = Path(__file__).parent / "fixtures" / "generated"
CASES = sorted(GENERATED.glob("*.json"))


def _manifest(path: Path) -> dict:
    return json.loads(path.read_text())


@unittest.skipUnless(HAS_PDFMINER, "pdfminer.six not installed")
class GeneratedCorpus(unittest.TestCase):
    def test_every_fixture_passes_the_corpus_checks(self):
        for path in CASES:
            with self.subTest(fixture=path.stem):
                problems = check_pdf(
                    path.with_suffix(".pdf").read_bytes(), _manifest(path)
                )
                self.assertEqual(problems, [])


class CorpusCoverage(unittest.TestCase):
    """The subset keeps covering what it's meant to."""

    def test_families_present(self):
        features = set()
        layouts = set()
        for path in CASES:
            m = _manifest(path)
            layouts.add(m["layout"])
            features.update(f.split(":")[0] for f in m["features"])
            if len({u["page"] for u in m["units"]}) > 1:
                features.add("multi-page")
        self.assertTrue(
            {"single", "left_sidebar", "right_sidebar", "two_column",
             "name_beside_contact", "scanned"} <= layouts,
            layouts,
        )
        self.assertTrue(
            {"form-xobjects", "contact-icons", "skills-grid", "long-url",
             "blank-page", "multi-page", "name"} <= features,
            features,
        )

    def test_fixtures_stay_small(self):
        for path in CASES:
            self.assertLess(path.with_suffix(".pdf").stat().st_size, 50_000, path.stem)


if __name__ == "__main__":
    unittest.main()
