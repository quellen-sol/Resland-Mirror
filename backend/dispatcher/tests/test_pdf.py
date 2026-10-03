"""doc_parsers/pdf tests — the view functions run against a hand-built
PdfDoc IR (no pdfminer needed); parse_pdf tests build a real PDF in memory
with a small stdlib writer and skip when pdfminer.six isn't installed.

Run: .venv/bin/python -m unittest backend.dispatcher.tests.test_pdf -v
     (from the repo root with the workspace venv)
"""

import io
import unittest
from itertools import pairwise
from unittest.mock import MagicMock, patch

from dispatcher.agents import docx_parser, pdf_parser
from dispatcher.doc_parsers import pdf as pdfdoc
from shared.pdfdoc import PdfDoc, PdfLine, PdfPage, PdfStyle

try:
    import pdfminer.layout  # noqa: F401

    HAS_PDFMINER = True
except ImportError:
    HAS_PDFMINER = False


def _line(
    text,
    *,
    x0=72.0,
    x1=300.0,
    top=100.0,
    height=12.0,
    page=0,
    font="Helvetica",
    size=11.0,
    bold=False,
    italic=False,
    color=None,
    gap=0.0,
    ends_page=False,
):
    return PdfLine(
        text=text,
        page=page,
        x0=x0,
        x1=x1,
        top=top,
        bottom=top + height,
        style=PdfStyle(
            font_name=font, size_pt=size, bold=bold, italic=italic, color=color
        ),
        gap_before_pt=gap,
        ends_page=ends_page,
    )


def _doc(lines, hrules=(), number=0, width=612.0, height=792.0):
    return PdfDoc(
        pages=[
            PdfPage(
                number=number,
                width=width,
                height=height,
                lines=list(lines),
                hrules=list(hrules),
            )
        ]
    )


def _pdf_bytes(ops, extra_objs=(), extra_resources=b""):
    """Minimal single-page PDF — Type1 base fonts, no compression — that a
    real extractor can parse. xref offsets are computed, not guessed.
    extra_objs are appended after the three font objects (8 0 obj on)."""
    content = "\n".join(ops).encode()
    resources = (
        b"/Resources << /Font << /F1 5 0 R /F2 6 0 R /F3 7 0 R >>"
        + (b" " + extra_resources if extra_resources else b"")
        + b" >>"
    )
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        + resources
        + b" /Contents 4 0 R >>",
        b"<< /Length "
        + str(len(content)).encode()
        + b" >>\nstream\n"
        + content
        + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique >>",
        *extra_objs,
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(out.tell())
        out.write(b"%d 0 obj\n" % i)
        out.write(body)
        out.write(b"\nendobj\n")
    xref = out.tell()
    out.write(b"xref\n0 %d\n" % (len(objs) + 1))
    out.write(b"0000000000 65535 f \n")
    for off in offsets:
        out.write(b"%010d 00000 n \n" % off)
    out.write(
        b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (len(objs) + 1, xref)
    )
    return out.getvalue()


def _pdf_pages_bytes(pages):
    """Like _pdf_bytes, one page per ops list, sharing the Helvetica fonts."""
    n = len(pages)
    fonts = [3 + 2 * n, 4 + 2 * n]
    resources = b"/Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >>" % tuple(fonts)
    kids = b" ".join(b"%d 0 R" % (3 + i) for i in range(n))
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [" + kids + b"] /Count %d >>" % n,
    ]
    objs += [
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        + resources
        + b" /Contents %d 0 R >>" % (3 + n + i)
        for i in range(n)
    ]
    for ops in pages:
        content = "\n".join(ops).encode()
        objs.append(
            b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream"
        )
    objs += [
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(out.tell())
        out.write(b"%d 0 obj\n" % i + body + b"\nendobj\n")
    xref = out.tell()
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1))
    for off in offsets:
        out.write(b"%010d 00000 n \n" % off)
    out.write(
        b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (len(objs) + 1, xref)
    )
    return out.getvalue()


def _text(x, y, text, font="F1", size=11):
    return f"BT /{font} {size} Tf {x} {y} Td ({text}) Tj ET"


def _circle(cx, cy, r, paint="f"):
    """A circle from four Bézier arcs — how generators draw bullet dots."""
    k = 0.5523 * r
    return (
        f"{cx + r} {cy} m "
        f"{cx + r} {cy + k} {cx + k} {cy + r} {cx} {cy + r} c "
        f"{cx - k} {cy + r} {cx - r} {cy + k} {cx - r} {cy} c "
        f"{cx - r} {cy - k} {cx - k} {cy - r} {cx} {cy - r} c "
        f"{cx + k} {cy - r} {cx + r} {cy - k} {cx + r} {cy} c {paint}"
    )


def _texts(ops):
    return [line.text for line in pdfdoc.parse_pdf(_pdf_bytes(ops)).lines]


def _resume_ops():
    """A one-page resume: name (bold, big), contact, a rule, then a
    section header + entry line — y measured from the bottom (PDF coords)."""
    return [
        _text(72, 720, "Jane Doe", font="F2", size=24),
        _text(72, 700, "jane@x.com | 555-1 | NYC"),
        # divider rule under the header area
        "72 688 m 540 688 l S",
        _text(72, 660, "EXPERIENCE", font="F2", size=14),
        _text(72, 640, "Senior Engineer - Acme    Jan 2020 - Present"),
        _text(90, 620, "- Built the thing"),
        _text(72, 590, "SKILLS", font="F2", size=14),
        _text(72, 570, "Languages: Python, Go"),
    ]


class Views(unittest.TestCase):
    def test_raw_text_joins_lines(self):
        doc = _doc([_line("one"), _line(""), _line("two")])
        self.assertEqual(pdfdoc.raw_text(doc), "one\n\ntwo")

    def test_block_sequence_lines_carry_style(self):
        doc = _doc(
            [
                _line("Jane Doe", font="Helvetica-Bold", size=24, bold=True),
                _line("plain"),
            ]
        )
        blocks = pdfdoc.block_sequence(doc)
        self.assertEqual(blocks[0]["type"], "line")
        self.assertEqual(blocks[0]["text"], "Jane Doe")
        self.assertEqual(blocks[0]["font_name"], "Helvetica-Bold")
        self.assertEqual(blocks[0]["size_pt"], 24.0)
        self.assertTrue(blocks[0]["bold"])

    def test_block_sequence_rules_inserted_in_order(self):
        doc = _doc(
            [_line("above", top=100), _line("below", top=200)],
            hrules=[150.0],
        )
        blocks = pdfdoc.block_sequence(doc)
        types = [b["type"] for b in blocks]
        self.assertEqual(types, ["line", "rule", "line"])
        self.assertEqual(blocks[1]["page"], 0)

    def test_block_sequence_flags_page_end(self):
        doc = _doc([_line("last", ends_page=True)])
        blocks = pdfdoc.block_sequence(doc)
        self.assertTrue(blocks[-1]["ends_page"])

    def test_whitespace_map_flags_gaps(self):
        doc = _doc(
            [
                _line("title", top=100, gap=0.0),
                _line("next", top=130, gap=18.0),
                _line("   ", top=160, gap=0.0),
            ]
        )
        m = pdfdoc.whitespace_map(doc)
        self.assertEqual(len(m), 3)
        self.assertFalse(m[0]["empty"])
        self.assertEqual(m[1]["gap_before_pt"], 18.0)
        self.assertTrue(m[2]["empty"])
        self.assertEqual(m[0]["page"], 0)

    def test_column_counts_single_column(self):
        # One dominant left edge; right-aligned date-ish lines share the
        # content column's right edge — not a column.
        lines = [_line("content line " + str(i), x0=72, x1=540, top=100 + i * 15)
                 for i in range(6)]
        lines += [_line("2020", x0=500, x1=540, top=100)]
        doc = _doc(lines)
        self.assertEqual(pdfdoc.column_counts(doc), [1])

    def test_column_counts_two_columns(self):
        # Sidebar lines (x 72→200) + main column (x 230→540).
        lines = []
        for i in range(6):
            lines.append(_line(f"side {i}", x0=72, x1=200, top=100 + i * 15))
            lines.append(_line(f"main {i}", x0=230, x1=540, top=100 + i * 15))
        doc = _doc(lines)
        self.assertEqual(pdfdoc.column_counts(doc), [2])


class FontHelpers(unittest.TestCase):
    def test_font_family_splits_style(self):
        self.assertEqual(pdfdoc._font_family("ABCDEF+Inter-Bold"), "Inter")
        self.assertEqual(pdfdoc._font_family("Helvetica"), "Helvetica")
        self.assertEqual(pdfdoc._font_family("TimesNewRomanPS-BoldMT"), "TimesNewRomanPS")

    def test_font_flags(self):
        self.assertEqual(pdfdoc._font_flags("Helvetica-Bold"), (True, False))
        self.assertEqual(pdfdoc._font_flags("Times-Italic"), (False, True))
        self.assertEqual(pdfdoc._font_flags("Inter"), (False, False))
        # "It"-suffixed styles (the food-service fixture's titles).
        self.assertEqual(pdfdoc._font_flags("ProximaNova-RegularIt"), (False, True))
        self.assertEqual(pdfdoc._font_flags("SourceSans-BoldIt"), (True, True))
        self.assertEqual(pdfdoc._font_flags("Inter-SemiBold"), (True, False))
        self.assertEqual(pdfdoc._font_flags("Arial,BoldItalic"), (True, True))

    def test_color_hex(self):
        self.assertIsNone(pdfdoc._color_hex((0.0, 0.0, 0.0)))
        self.assertIsNone(pdfdoc._color_hex(0.0))
        self.assertEqual(pdfdoc._color_hex((0.5, 0.0, 1.0)), "8000FF")
        self.assertIsNone(pdfdoc._color_hex("weird"))


class PdfAgent(unittest.TestCase):
    def _build(self):
        agent = MagicMock()
        with patch.object(
            docx_parser, "create_agent", return_value=agent
        ) as create:
            out = pdf_parser.build_pdf_resume_agent(
                _doc([_line("Jane Doe"), _line("Engineer")])
            )
        _, kwargs = create.call_args
        tools = {t.name: t for t in kwargs["tools"]}
        return out, agent, kwargs, tools

    def test_wired_like_docx_agent(self):
        _, _, kwargs, tools = self._build()
        self.assertEqual(kwargs["model"], docx_parser.RESUME_PARSER_MODEL)
        self.assertEqual(
            kwargs["system_prompt"], docx_parser.PDF_AGENT_PARSER_SYSTEM_PROMPT
        )
        self.assertEqual(
            set(tools),
            {
                "get_raw_doc_text",
                "get_block_sequence",
                "get_whitespace_map",
                "get_columns",
                "submit_user_profile",
            },
        )

    def test_tools_return_pdf_views(self):
        _, _, _, tools = self._build()
        self.assertIn("Jane Doe", tools["get_raw_doc_text"].invoke({}))
        blocks = tools["get_block_sequence"].invoke({})
        self.assertEqual(blocks[0]["type"], "line")
        self.assertIsInstance(tools["get_whitespace_map"].invoke({}), list)
        self.assertEqual(tools["get_columns"].invoke({}), [1])

    def test_submit_fills_queue(self):
        out, _, _, tools = self._build()
        profile = docx_parser.UserDocxProfile(
            summary="s",
            basic_info=docx_parser.UserProfileBasicInfo(
                name="Jane", email="", phone="", location=""
            ),
            experience=[],
            skills=[],
            education=[],
            projects=[],
        )
        tools["submit_user_profile"].invoke({"profile": profile})
        self.assertIs(out.profile_queue.get_nowait(), profile)

    def test_agent_parse_pdf_invokes_and_returns_queue(self):
        out, agent, _, _ = self._build()
        with patch.object(
            pdf_parser, "build_pdf_resume_agent", return_value=out
        ):
            q = pdf_parser.agent_parse_pdf(MagicMock(name="pdf"))
        agent.invoke.assert_called_once()
        self.assertIs(q, out.profile_queue)


@unittest.skipUnless(HAS_PDFMINER, "pdfminer.six not installed")
class ParsePdf(unittest.TestCase):
    def test_parses_real_pdf_lines_and_styles(self):
        doc = pdfdoc.parse_pdf(_pdf_bytes(_resume_ops()))
        self.assertEqual(len(doc.pages), 1)
        lines = {line.text: line for line in doc.lines}
        self.assertIn("Jane Doe", lines)
        name = lines["Jane Doe"]
        self.assertEqual(name.style.font_name, "Helvetica")
        self.assertEqual(name.style.size_pt, 24.0)
        self.assertTrue(name.style.bold)
        contact = lines["jane@x.com | 555-1 | NYC"]
        self.assertEqual(contact.style.size_pt, 11.0)
        self.assertFalse(contact.style.bold)
        # y coords flipped: the name is near the top of the page.
        self.assertLess(name.top, contact.top)

    def test_detects_horizontal_rule(self):
        doc = pdfdoc.parse_pdf(_pdf_bytes(_resume_ops()))
        self.assertTrue(doc.pages[0].hrules)
        blocks = pdfdoc.block_sequence(doc)
        self.assertIn("rule", [b["type"] for b in blocks])

    def test_gaps_and_page_end(self):
        doc = pdfdoc.parse_pdf(_pdf_bytes(_resume_ops()))
        last = doc.lines[-1]
        self.assertTrue(last.ends_page)
        header = next(l for l in doc.lines if l.text == "EXPERIENCE")
        # 28pt gap above the section header (rule + spacing).
        self.assertGreater(header.gap_before_pt, 10.0)

    def test_single_line_document(self):
        doc = pdfdoc.parse_pdf(_pdf_bytes([_text(72, 720, "Page two")]))
        self.assertEqual([l.text for l in doc.lines], ["Page two"])

    def test_empty_content_stream(self):
        doc = pdfdoc.parse_pdf(_pdf_bytes([]))
        self.assertEqual(doc.lines, [])

    def _fig_xobject(self, ops, w=300, h=100):
        """A Form XObject (obj 8) — pdfminer surfaces it as LTFigure, and
        real exporters (Canva, Word) wrap most page content in them."""
        body = "\n".join(ops).encode()
        return (
            b"<< /Type /XObject /Subtype /Form /FormType 1 "
            + f"/BBox [0 0 {w} {h}] ".encode()
            + b"/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> "
            + b"/Length "
            + str(len(body)).encode()
            + b" >>\nstream\n"
            + body
            + b"\nendstream"
        )

    def test_text_inside_figures(self):
        """Text drawn inside a Form XObject still lands in the IR —
        the bug that emptied the issue-49 resume's header."""
        fig = self._fig_xobject([_text(10, 50, "HIDDEN NAME", font="F2", size=16)])
        ops = [
            _text(72, 720, "before fig"),
            "q 1 0 0 1 300 500 cm /Fm1 Do Q",
            _text(72, 680, "after fig"),
        ]
        doc = pdfdoc.parse_pdf(
            _pdf_bytes(
                ops,
                extra_objs=[fig],
                extra_resources=b"/XObject << /Fm1 8 0 R >>",
            )
        )
        texts = [l.text for l in doc.lines]
        self.assertIn("HIDDEN NAME", texts)
        self.assertIn("before fig", texts)
        self.assertIn("after fig", texts)
        fig_line = next(l for l in doc.lines if l.text == "HIDDEN NAME")
        self.assertTrue(fig_line.style.bold)
        self.assertEqual(fig_line.style.size_pt, 16.0)
        # Absolute position — page x ≈ 300+10, baseline y = 500+50.
        self.assertAlmostEqual(fig_line.x0, 310.0, delta=2.0)

    def test_same_row_fragments_merge(self):
        """A title at the left edge and right-floated dates at the same
        baseline merge into one line."""
        ops = [
            _text(72, 640, "Acme - Engineer", font="F2", size=11),
            _text(450, 640, "Jan 2020 - Present", font="F3", size=11),
        ]
        doc = pdfdoc.parse_pdf(_pdf_bytes(ops))
        self.assertEqual(len(doc.lines), 1)
        line = doc.lines[0]
        self.assertIn("Acme - Engineer", line.text)
        self.assertIn("Jan 2020 - Present", line.text)

    def test_curve_dot_becomes_bullet_glyph(self):
        """Tiny filled circles right before list lines are drawn bullets —
        they become '• ' prefixes; the line without one stays plain."""
        ops = [
            _circle(66, 643, 1.5),
            _text(75, 640, "Did a thing"),
            _circle(66, 627, 1.5),
            _text(75, 624, "Did another thing"),
            _text(75, 608, "Not a bullet"),
        ]
        doc = pdfdoc.parse_pdf(_pdf_bytes(ops))
        self.assertEqual(
            [l.text for l in doc.lines],
            ["• Did a thing", "• Did another thing", "Not a bullet"],
        )

    def test_drawn_square_and_hollow_bullets_keep_their_shape(self):
        ops = [
            "63 640 3 3 re f",
            _text(75, 640, "Square one"),
            "63 624 3 3 re f",
            _text(75, 624, "Square two"),
            _circle(66, 595, 1.5, paint="S"),
            _text(75, 592, "Hollow one"),
            _circle(66, 579, 1.5, paint="S"),
            _text(75, 576, "Hollow two"),
        ]
        texts = [l.text for l in pdfdoc.parse_pdf(_pdf_bytes(ops)).lines]
        self.assertEqual(
            texts,
            ["▪ Square one", "▪ Square two", "○ Hollow one", "○ Hollow two"],
        )

    def test_lone_dot_marks_a_sentence_not_a_short_field(self):
        """A one-item list still gets its bullet; a lone icon beside a
        short field (a city) doesn't."""
        ops = [
            _circle(66, 643, 1.5),
            _text(75, 640, "Shipped the billing rewrite two weeks early"),
            _circle(66, 403, 2.5),
            _text(75, 400, "Denver, CO"),
        ]
        texts = [l.text for l in pdfdoc.parse_pdf(_pdf_bytes(ops)).lines]
        self.assertEqual(
            texts,
            ["• Shipped the billing rewrite two weeks early", "Denver, CO"],
        )

    def test_short_item_after_a_long_wrapped_item_keeps_its_bullet(self):
        """A bullet that wraps onto several lines pushes the next dot well
        past the plain list gap; a short last item must still read as part
        of the list (not as a lone dot before short text)."""
        ops = [
            _circle(66, 643, 1.5),
            _text(75, 640, "Led a cross-functional team of six across"),
            _text(75, 626, "three regional offices and the migration to"),
            _text(75, 612, "a new point of sale system for every store"),
            _text(75, 598, "in the region, on time and under budget"),
            _circle(66, 587, 1.5),
            _text(75, 584, "Cut costs 12%"),
        ]
        texts = [l.text for l in pdfdoc.parse_pdf(_pdf_bytes(ops)).lines]
        self.assertEqual(texts[0][:2], "• ")
        self.assertEqual(texts[-1], "• Cut costs 12%")

    def test_list_running_over_a_page_break_keeps_its_last_bullet(self):
        """The first item wraps onto the next page, leaving the short last
        item alone at the top of it — still the same list."""
        page1 = [
            _circle(66, 87, 1.5),
            _text(75, 84, "Shipped the billing rewrite two weeks early"),
            _circle(66, 73, 1.5),
            _text(75, 70, "Led a cross-functional team of six across"),
            _text(75, 56, "three regional offices and the migration to"),
        ]
        page2 = [
            _text(75, 740, "a new point of sale system for every store"),
            _circle(66, 729, 1.5),
            _text(75, 726, "Cut costs 12%"),
            _text(60, 700, "EDUCATION", font="F2"),
        ]
        texts = [
            l.text for l in pdfdoc.parse_pdf(_pdf_pages_bytes([page1, page2])).lines
        ]
        self.assertIn("• Cut costs 12%", texts)

    def test_heading_between_dots_still_ends_the_list(self):
        """Only wrapped continuation lines bridge a long gap — a heading at
        the margin between a contact icon and a list keeps them apart."""
        ops = [
            _circle(66, 703, 2.0),
            _text(75, 700, "Denver, CO"),
            _text(60, 680, "EXPERIENCE", font="F2"),
            _text(60, 664, "Engineer - Acme"),
            _circle(66, 651, 1.5),
            _text(75, 648, "Shipped the billing rewrite"),
            _circle(66, 637, 1.5),
            _text(75, 634, "Cut costs 12%"),
        ]
        texts = [l.text for l in pdfdoc.parse_pdf(_pdf_bytes(ops)).lines]
        self.assertEqual(texts[0], "Denver, CO")
        self.assertIn("• Cut costs 12%", texts)

    def test_contact_icons_are_not_bullets(self):
        """5pt icons stacked beside email/phone/location lines are dot-
        shaped and repeat at one x, exactly like a list — the contact text
        gives them away (issue: '• jane@x.com')."""
        ops = []
        for i, text in enumerate(
            ["jane@x.com", "555-123-4567", "Denver, CO", "linkedin.com/in/jane"]
        ):
            y = 700 - i * 14
            ops.append(_circle(66.5, y + 3, 2.5))
            ops.append(_text(76, y, text))
        texts = [l.text for l in pdfdoc.parse_pdf(_pdf_bytes(ops)).lines]
        self.assertEqual(
            texts,
            ["jane@x.com", "555-123-4567", "Denver, CO", "linkedin.com/in/jane"],
        )

    def test_icon_shapes_that_arent_dots_are_ignored(self):
        """Thin bars (contact separators) and 8pt icons aren't bullets."""
        ops = [
            "64 638 1 6 re f",
            _text(75, 640, "Bar beside this line one"),
            "64 622 1 6 re f",
            _text(75, 624, "Bar beside this line two"),
            "60 604 8 8 re f",
            _text(75, 606, "Big icon beside this line"),
            "60 588 8 8 re f",
            _text(75, 590, "Big icon beside this one"),
        ]
        texts = [l.text for l in pdfdoc.parse_pdf(_pdf_bytes(ops)).lines]
        self.assertFalse(any(t.startswith(("•", "▪")) for t in texts), texts)

    def test_winansi_code_127_reads_as_bullet(self):
        """Some generators write "•" as code 127 (WinAnsi maps unused codes
        to the bullet); pdfminer leaves it as "(cid:127)"."""
        ops = [
            _text(72, 640, "\\177 Built the thing"),
            _text(72, 624, "\\177 Shipped it"),
        ]
        texts = [l.text for l in pdfdoc.parse_pdf(_pdf_bytes(ops)).lines]
        self.assertEqual(texts, ["• Built the thing", "• Shipped it"])

    def test_lines_carry_style_runs(self):
        """A bold company and an oblique title on one line keep separate
        runs (capture reads head/tail styles from them)."""
        ops = [
            "BT /F2 11 Tf 72 640 Td (Acme Corp) Tj /F3 11 Tf ( - Engineer) Tj ET",
            _text(450, 640, "Jan 2020 - Present"),
        ]
        line = pdfdoc.parse_pdf(_pdf_bytes(ops)).lines[0]
        self.assertEqual("".join(r.text for r in line.runs), line.text)
        # Whitespace rides with the run before it.
        self.assertEqual(line.runs[0].text.strip(), "Acme Corp")
        self.assertTrue(line.runs[0].style.bold)
        self.assertTrue(line.style_at(line.text.index("Engineer")).italic)
        date_run = line.run_at(line.text.index("Jan 2020"))
        self.assertFalse(date_run.style.bold or date_run.style.italic)
        self.assertAlmostEqual(date_run.x0, 450.0, delta=1.0)

    def test_localized_two_column_region_is_not_page_columns(self):
        """A small 2-col grid (skills) surrounded by full-width lines must
        not mark the whole page two-column."""
        ops = [_text(72, 740, "DANA PRESCOTT", font="F2", size=18)]
        for i in range(4):
            ops.append(_text(72, 640 - i * 14, f"wide content line {i}"))
        # Localized grid: ~3 rows in the middle of the page.
        for i in range(3):
            ops.append(_text(72, 560 - i * 14, f"skill {i}"))
            ops.append(_text(320, 560 - i * 14, f"skill right {i}"))
        for i in range(4):
            ops.append(_text(72, 440 - i * 14, f"more wide content {i}"))
        doc = pdfdoc.parse_pdf(_pdf_bytes(ops))
        self.assertEqual(pdfdoc.column_counts(doc), [1])


def _sidebar_ops(side_lines, main_lines=45, side="left", leading=14):
    """A sidebar of `side_lines` items beside a main column of
    `main_lines` sentences, rows on the same baselines."""
    side_x, main_x = (40, 200) if side == "left" else (430, 40)
    ops = []
    for i in range(main_lines):
        ops.append(
            _text(main_x, 740 - i * leading, f"Main column sentence {i} keeps going a while")
        )
    for i in range(side_lines):
        ops.append(_text(side_x, 740 - i * leading, f"Sidebar item {i}"))
    return ops


@unittest.skipUnless(HAS_PDFMINER, "pdfminer.six not installed")
class ReadingOrder(unittest.TestCase):
    """Same-row merging joins titles with floated dates and labels with
    values, but never fuses independent bands (finding A)."""

    def _assert_bands(self, texts, side_lines, main_lines=45):
        side = [t for t in texts if t.startswith("Sidebar")]
        main = [t for t in texts if t.startswith("Main")]
        self.assertEqual(len(side) + len(main), len(texts), "fused lines")
        self.assertEqual(side, [f"Sidebar item {i}" for i in range(side_lines)])
        self.assertEqual(
            main,
            [f"Main column sentence {i} keeps going a while" for i in range(main_lines)],
        )
        # One band entirely, then the other — never interleaved.
        bands = [t[:4] for t in texts]
        self.assertLessEqual(
            sum(1 for a, b in pairwise(bands) if a != b), 1, texts
        )

    def test_short_sidebars_never_fuse_with_main(self):
        # 12/15/16 lines beside 45 slipped under column_gutter's 25% rule
        # and fused row by row; 20 was detected even before.
        for side in ("left", "right"):
            for n in (3, 12, 15, 16, 20, 30):
                with self.subTest(side=side, lines=n):
                    texts = _texts(_sidebar_ops(n, side=side))
                    self._assert_bands(texts, n)

    def test_misaligned_sidebar_rows_stay_separate(self):
        ops = [
            _text(200, 740 - i * 14, f"Main column sentence {i} keeps going a while")
            for i in range(30)
        ] + [_text(40, 735 - i * 11, f"Sidebar item {i}", size=9) for i in range(14)]
        self._assert_bands(_texts(ops), 14, 30)

    def test_floated_dates_merge_beside_a_sidebar(self):
        ops = _sidebar_ops(10, main_lines=0)
        ops += [
            _text(200, 740, "Engineer - Acme", font="F2"),
            _text(480, 740, "2020 - 2024"),
            _text(200, 726, "Built the thing nobody else would touch"),
            _text(200, 712, "Analyst - Globex", font="F2"),
            _text(480, 712, "2016 - 2020"),
        ]
        texts = _texts(ops)
        self.assertIn("Engineer - Acme    2020 - 2024", texts)
        self.assertIn("Analyst - Globex    2016 - 2020", texts)
        self.assertFalse(any("Sidebar" in t and "-" in t for t in texts), texts)

    def test_skills_grid_then_entry(self):
        """A two-band skills grid reads as separate cells in row order (no
        page columns), and the entry right below still joins its date."""
        ops = [_text(72, 740, "Summary line that runs across the whole page width ok")]
        ops.append(_text(72, 720, "SKILLS", font="F2"))
        grid = [("Python", "Docker"), ("Rust", "Terraform"), ("SQL", "Kafka")]
        for i, (a, b) in enumerate(grid):
            ops.append(_text(72, 704 - i * 14, a))
            ops.append(_text(320, 704 - i * 14, b))
        ops.append(_text(72, 650, "EXPERIENCE", font="F2"))
        ops.append(_text(72, 634, "Engineer - Acme", font="F2"))
        ops.append(_text(470, 634, "Jan 2020 - Present"))
        ops.append(_text(72, 620, "Built the thing nobody else would touch, end to end"))
        doc = pdfdoc.parse_pdf(_pdf_bytes(ops))
        texts = [l.text for l in doc.lines]
        self.assertEqual(
            texts[1:9],
            ["SKILLS", "Python", "Docker", "Rust", "Terraform", "SQL", "Kafka", "EXPERIENCE"],
        )
        self.assertIn("Engineer - Acme    Jan 2020 - Present", texts)
        self.assertEqual(pdfdoc.column_counts(doc), [1])

    def test_label_column_merges_with_values(self):
        ops = [_text(72, 740, "JANE DOE", font="F2", size=18)]
        for i, (label, value) in enumerate(
            [("Address:", "Denver, CO"), ("Phone:", "555-1234"), ("Email:", "jane@x.com")]
        ):
            ops.append(_text(72, 716 - i * 14, label, font="F2"))
            ops.append(_text(140, 716 - i * 14, value))
        ops.append(_text(72, 650, "A full width summary sentence that crosses everything"))
        texts = _texts(ops)
        self.assertEqual(
            texts[1:4],
            ["Address:    Denver, CO", "Phone:    555-1234", "Email:    jane@x.com"],
        )

    def test_name_beside_stacked_contact(self):
        """A big name with a contact stack to its right: separate lines,
        name first, contacts in order."""
        ops = [_text(54, 712, "Jane Doe", font="F2", size=24)]
        for i, value in enumerate(["jane@x.com", "555-123-4567", "Denver, CO"]):
            ops.append(_text(400, 724 - i * 13, value))
        ops.append(_text(54, 660, "A full width summary sentence that crosses everything"))
        texts = _texts(ops)
        self.assertEqual(
            texts[:4], ["Jane Doe", "jane@x.com", "555-123-4567", "Denver, CO"]
        )

    def test_marker_column_drawn_apart_from_items(self):
        """List markers drawn as separate text objects, a gap away from
        their item text, still lead their line."""
        ops = []
        for i in range(3):
            ops.append(_text(74, 700 - i * 14, "-"))
            ops.append(_text(90, 700 - i * 14, f"Item number {i} in the list"))
        self.assertEqual(
            _texts(ops), [f"- Item number {i} in the list" for i in range(3)]
        )

    def test_two_line_entry_header(self):
        """Title + dates over company + location, both right-aligned."""
        ops = [
            _text(72, 700, "Software Engineer", font="F2"),
            _text(540 - 92.4, 700, "Jan 2020 - Present"),
            _text(72, 686, "Acme Corp", font="F3"),
            _text(540 - 56.3, 686, "Denver, CO"),
            _text(80, 672, "Built the thing nobody else would touch, end to end"),
        ]
        texts = _texts(ops)
        self.assertEqual(texts[0], "Software Engineer    Jan 2020 - Present")
        self.assertEqual(texts[1], "Acme Corp    Denver, CO")


class _StubFrag:
    def __init__(self, x0, top, h):
        self.x0, self.x1, self.top, self.bottom = x0, x0 + 40, top, top + h

    @property
    def cy(self):
        return (self.top + self.bottom) / 2

    @property
    def height(self):
        return self.bottom - self.top


def _reference_row_rows(frags):
    """The original O(n²) first-fit grouping _row_rows must match."""
    rows, centers = [], []
    for frag in sorted(frags, key=lambda f: (f.cy, f.x0)):
        for i, center in enumerate(centers):
            row_h = max(f.bottom - f.top for f in rows[i])
            h = max(row_h, frag.bottom - frag.top, 1.0)
            if abs(frag.cy - center) <= max(2.5, h * 0.45):
                rows[i].append(frag)
                centers[i] = (center * (len(rows[i]) - 1) + frag.cy) / len(rows[i])
                break
        else:
            rows.append([frag])
            centers.append(frag.cy)
    return rows


class RowRows(unittest.TestCase):
    def test_matches_first_fit_reference(self):
        """The windowed scan (finding E) groups exactly like the original
        scan-every-row loop — random pages with jitter, mixed sizes, near
        ties, and the occasional tall fragment."""
        import random

        for seed in range(300):
            rng = random.Random(seed)
            frags = []
            for _ in range(rng.randint(0, 120)):
                h = rng.choice([8, 10, 11, 12, 14, 24, 40])
                top = rng.choice([rng.uniform(0, 700), rng.randint(0, 60) * 12.0])
                frags.append(_StubFrag(rng.uniform(40, 500), top + rng.uniform(-3, 3), h))
            got = [[id(f) for f in row] for row in pdfdoc._row_rows(frags)]
            want = [[id(f) for f in row] for row in _reference_row_rows(frags)]
            self.assertEqual(got, want, f"seed {seed}")

    def test_scales_linearly_enough(self):
        import time

        frags = [_StubFrag(40 + (i % 3) * 200, (i // 3) * 12.0, 10) for i in range(6000)]
        start = time.perf_counter()
        rows = pdfdoc._row_rows(frags)
        self.assertEqual(len(rows), 2000)
        self.assertLess(time.perf_counter() - start, 1.0)


if __name__ == "__main__":
    unittest.main()
