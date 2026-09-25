"""shared.pdfdoc IR tests — line flattening and the column heuristic.

Run: .venv/bin/python -m unittest backend.shared.tests.test_pdfdoc -v
     (from the repo root with the workspace venv)
"""

import unittest

from shared.pdfdoc import PdfDoc, PdfLine, PdfPage, PdfStyle, page_columns


def _line(text, *, x0=72.0, x1=300.0, top=100.0):
    return PdfLine(
        text=text,
        page=0,
        x0=x0,
        x1=x1,
        top=top,
        bottom=top + 12,
        style=PdfStyle(),
    )


def _page(lines, number=0):
    return PdfPage(number=number, width=612.0, height=792.0, lines=list(lines))


class Lines(unittest.TestCase):
    def test_flattens_pages_in_order(self):
        doc = PdfDoc(
            pages=[
                _page([_line("p1a"), _line("p1b")]),
                _page([_line("p2a")], number=1),
            ]
        )
        self.assertEqual([l.text for l in doc.lines], ["p1a", "p1b", "p2a"])

    def test_empty_doc(self):
        self.assertEqual(PdfDoc().lines, [])


class PageColumns(unittest.TestCase):
    def test_single_column_with_right_dates(self):
        # Right-aligned date fragments share the main column's right edge —
        # they're part of the entry line, not a second column.
        lines = [
            _line("long content line " + str(i), x0=72, x1=540, top=i * 20)
            for i in range(6)
        ]
        lines += [_line("2020", x0=500, x1=540, top=0)]
        self.assertEqual(page_columns(_page(lines)), 1)

    def test_two_columns(self):
        lines = []
        for i in range(6):
            lines.append(_line(f"side {i}", x0=72, x1=200, top=i * 20))
            lines.append(_line(f"main {i}", x0=230, x1=540, top=i * 20))
        self.assertEqual(page_columns(_page(lines)), 2)

    def test_too_few_lines_defaults_to_one(self):
        self.assertEqual(
            page_columns(_page([_line("a", x0=72, x1=100), _line("b", x0=300, x1=540)])), 1
        )


if __name__ == "__main__":
    unittest.main()
