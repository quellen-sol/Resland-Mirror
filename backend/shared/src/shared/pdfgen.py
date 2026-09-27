"""Minimal PDF renderer — the pdf sibling of `docgen.render_docx`.

There is no PDF library or document converter in this environment, so this
writes PDF 1.4 content streams directly with the base-14 Type1 fonts.
Captured typefaces map onto the nearest base family (Inter → Helvetica,
Times-ish → Times, mono → Courier) and layout mirrors render_docx: same
margins, section order, roles, separators, bullet glyph + indent, and
right-floated dates. Word wrapping uses the AFM width tables bundled below,
so the output paginates and aligns the way the captured layout implies.
"""

from __future__ import annotations

import io
from dataclasses import replace

from .docgen import (
    ROLE_BODY,
    ROLE_BULLET,
    ROLE_CONTACT,
    ROLE_ENTRY_SUB,
    ROLE_ENTRY_TITLE,
    ROLE_LINK,
    ROLE_LOCATION,
    ROLE_NAME,
    ROLE_PROJECT_BODY,
    ROLE_PROJECT_SUB,
    ROLE_PROJECT_TITLE,
    ROLE_SECTION_HEADER,
    SECTION_EDUCATION,
    SECTION_EXPERIENCE,
    SECTION_PROJECTS,
    SECTION_SKILLS,
    SECTION_SUMMARY,
    DEFAULT_SECTION_TITLES,
    SKILLS_LAYOUT_GROUPED,
    FormatProfile,
    ResumeContent,
    RoleStyle,
    _dates,
    _overlay_link,
)

_PAGE_W = 612.0
_PAGE_H = 792.0
# Gutter between text columns, mirroring Word's default 0.25".
_COL_GUTTER_PT = 18.0

_SERIF_WORDS = ("times", "serif", "roman", "georgia", "garamond", "cambria", "book")
_MONO_WORDS = ("courier", "mono", "consol", "menlo", "monaco")

# (regular, bold, italic, bold-italic) per family.
_FAMILIES = {
    "times": ("Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic"),
    "courier": ("Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique"),
    "helvetica": (
        "Helvetica",
        "Helvetica-Bold",
        "Helvetica-Oblique",
        "Helvetica-BoldOblique",
    ),
}

# Characters cp1252 can't carry, mapped to the nearest printable twin.
_TEXT_FIX = {
    "‑": "-",  # U+2011 non-breaking hyphen
    "‒": "-",  # U+2012 figure dash
    "―": "—",  # U+2015 horizontal bar
    "\u202f": " ",  # narrow no-break space
    "\u00a0": " ",
    "ﬁ": "fi",  # ligatures
    "ﬂ": "fl",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
}


def _family_of(font_name: str | None) -> str:
    n = (font_name or "").lower()
    if any(w in n for w in _SERIF_WORDS):
        return "times"
    if any(w in n for w in _MONO_WORDS):
        return "courier"
    return "helvetica"


def _res_name(style: RoleStyle) -> str:
    fam = _FAMILIES[_family_of(style.font_name)]
    idx = (1 if style.bold else 0) + (2 if style.italic else 0)
    return fam[idx]


def _pdf_text(text: str) -> bytes:
    for k, v in _TEXT_FIX.items():
        text = text.replace(k, v)
    raw = text.encode("cp1252", "replace")
    return (
        raw.replace(b"\\", b"\\\\")
        .replace(b"(", b"\\(")
        .replace(b")", b"\\)")
    )


def _rgb(style: RoleStyle) -> tuple[float, float, float]:
    if not style.color:
        return (0.0, 0.0, 0.0)
    return (
        int(style.color[0:2], 16) / 255.0,
        int(style.color[2:4], 16) / 255.0,
        int(style.color[4:6], 16) / 255.0,
    )


def _build_widths() -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for name, raw in _WIDTHS_RAW.items():
        table: dict[str, int] = {}
        for entry in raw.split(","):
            if entry:
                k, v = entry.split(":")
                table[chr(int(k, 16))] = int(v)
        out[name] = table
    return out


_WIDTHS: dict[str, dict[str, int]] | None = None


def _text_width(text: str, res: str, size_pt: float) -> float:
    global _WIDTHS
    if _WIDTHS is None:
        _WIDTHS = _build_widths()
    table = _WIDTHS[res]
    units = sum(table.get(ch, 556) for ch in text)
    return units * size_pt / 1000.0


class _Page:
    def __init__(self):
        self.ops: list[bytes] = []

    def text(self, x: float, y: float, res: str, size: float, rgb, s: bytes):
        r, g, b = rgb
        self.ops.append(
            b"BT /"
            + res.encode()
            + b" %.2f Tf %.3f %.3f %.3f rg %.2f %.2f Td (" % (size, r, g, b, x, y)
            + s
            + b") Tj ET"
        )

    def hline(self, x0: float, x1: float, y: float, width: float, rgb):
        r, g, b = rgb
        self.ops.append(
            b"%.2f w %.3f %.3f %.3f RG %.2f %.2f m %.2f %.2f l S"
            % (width, r, g, b, x0, y, x1, y)
        )


class _Flow:
    """Vertical cursor over pages/columns: `space` descends, rolling to the
    next column or page when the bottom margin is crossed."""

    def __init__(self, fmt: FormatProfile):
        self.fmt = fmt
        m = fmt.page_margins_in
        self.mtop = m["top"] * 72
        self.mbottom = m["bottom"] * 72
        self.mleft = m["left"] * 72
        self.mright = m["right"] * 72
        self.cols = max(1, int(fmt.columns or 1))
        full = _PAGE_W - self.mleft - self.mright
        self.col_w = (full - _COL_GUTTER_PT * (self.cols - 1)) / self.cols
        self.pages: list[_Page] = []
        self.font_res: dict[str, str] = {}  # base-14 face -> F<n> resource key
        self.page: _Page
        self.col = 0
        self.y = 0.0
        self._new_page()

    def res(self, style: RoleStyle) -> str:
        """The /F<n> resource key for this run's base-14 face."""
        face = _res_name(style)
        if face not in self.font_res:
            self.font_res[face] = f"F{len(self.font_res) + 1}"
        return self.font_res[face]

    @property
    def left(self) -> float:
        return self.mleft + self.col * (self.col_w + _COL_GUTTER_PT)

    @property
    def right(self) -> float:
        return self.left + self.col_w

    def _new_page(self):
        self.page = _Page()
        self.pages.append(self.page)
        self.col = 0
        self.y = _PAGE_H - self.mtop

    def ensure(self, height: float):
        if self.y - height < self.mbottom:
            if self.col < self.cols - 1:
                self.col += 1
                self.y = _PAGE_H - self.mtop
            else:
                self._new_page()

    def descend(self, dy: float):
        self.y -= dy


def _line_height(style: RoleStyle) -> float:
    size = style.size_pt or 11.0
    return size * (style.line_spacing or 1.2)


def _atoms(runs: list[tuple[str, RoleStyle]]) -> list[tuple[str, RoleStyle]]:
    return [
        (word, style)
        for text, style in runs
        for word in text.split()
    ]


def _wrap(
    atoms: list[tuple[str, RoleStyle]], avail: float
) -> list[list[tuple[str, RoleStyle]]]:
    """Greedy word wrap — atoms keep their own style so mixed runs
    (a bold label next to plain items) wrap correctly."""
    lines: list[list[tuple[str, RoleStyle]]] = [[]]
    cur_w = 0.0
    for word, style in atoms:
        res = _res_name(style)
        size = style.size_pt or 11.0
        w = _text_width(word, res, size)
        space_w = (
            _text_width(" ", _res_name(lines[-1][-1][1]), lines[-1][-1][1].size_pt or 11.0)
            if lines[-1]
            else 0.0
        )
        if cur_w + space_w + w > avail and lines[-1]:
            lines.append([])
            cur_w, space_w = 0.0, 0.0
        lines[-1].append((word, style))
        cur_w += space_w + w
    return lines


def _line_width(atoms: list[tuple[str, RoleStyle]]) -> float:
    total = 0.0
    for i, (word, style) in enumerate(atoms):
        total += _text_width(word, _res_name(style), style.size_pt or 11.0)
        if i < len(atoms) - 1:
            total += _text_width(" ", _res_name(style), style.size_pt or 11.0)
    return total


def _draw_atoms(
    flow: _Flow, atoms: list[tuple[str, RoleStyle]], x: float, y: float
) -> float:
    """Draw one wrapped line run-by-run; returns the x where it ends."""
    cx = x
    for word, style in atoms:
        face = _res_name(style)
        size = style.size_pt or 11.0
        rgb = _rgb(style)
        flow.page.text(cx, y, flow.res(style), size, rgb, _pdf_text(word))
        w = _text_width(word, face, size)
        if style.underline:
            flow.page.hline(cx, cx + w, y - 1.0, max(size * 0.06, 0.5), rgb)
        cx += w + _text_width(" ", face, size)
    return cx


def _para(flow: _Flow, runs: list[tuple[str, RoleStyle]], style: RoleStyle):
    """One wrapped paragraph: space_before, wrapped lines at the column
    edge (or centered/right per the role's alignment), space_after."""
    flow.ensure(0)
    flow.descend(style.space_before_pt or 0.0)
    leading = _line_height(style)
    avail = flow.right - flow.left
    for line in _wrap(_atoms(runs), avail):
        flow.ensure(leading)
        flow.descend(leading)
        w = _line_width(line)
        if style.alignment == "center":
            x = flow.left + max(0.0, (avail - w) / 2)
        elif style.alignment == "right":
            x = flow.right - w
        else:
            x = flow.left
        _draw_atoms(flow, line, x, flow.y)
    flow.descend(style.space_after_pt or 0.0)


def _entry_header(
    flow: _Flow,
    title: str,
    tail: str | None,
    dates: str,
    fmt: FormatProfile,
    title_role: str = ROLE_ENTRY_TITLE,
    sub_role: str = ROLE_ENTRY_SUB,
):
    """Mirror of docgen._entry_header: title + tail via the captured
    separator, dates floated at the right edge on the same line."""
    title_style = fmt.roles.get(title_role, fmt.role(ROLE_ENTRY_TITLE))
    sub_style = fmt.roles.get(sub_role, fmt.role(ROLE_ENTRY_SUB))
    sep = fmt.entry_title_separator
    if tail and fmt.entry_title_tail_sub:
        runs = [(title, title_style), (f"{sep}{tail}", sub_style)]
    elif tail:
        runs = [(f"{title}{sep}{tail}", title_style)]
    else:
        runs = [(title, title_style)]

    flow.ensure(0)
    flow.descend(title_style.space_before_pt or 0.0)
    leading = _line_height(title_style)
    avail = flow.right - flow.left
    wrapped = _wrap(_atoms(runs), avail)
    first = wrapped[0] if wrapped else []
    dates_own_line = False
    if fmt.dates_on_title_line and dates:
        dates_w = _text_width(
            dates, _res_name(sub_style), sub_style.size_pt or 11.0
        )
        first_w = _line_width(first)
        if first_w + dates_w + 12.0 > avail:
            # Not enough room to float — drop dates to their own line.
            wrapped.append([(dates, sub_style)])
            dates_own_line = True
            float_right = False
        else:
            float_right = True
    else:
        float_right = False
    for i, line in enumerate(wrapped):
        flow.ensure(leading)
        flow.descend(leading)
        if dates_own_line and i == len(wrapped) - 1:
            _draw_atoms(flow, line, flow.right - _line_width(line), flow.y)
        else:
            _draw_atoms(flow, line, flow.left, flow.y)
        if i == 0 and float_right:
            face = _res_name(sub_style)
            size = sub_style.size_pt or 11.0
            dates_w = _text_width(dates, face, size)
            x = flow.right - dates_w
            rgb = _rgb(sub_style)
            flow.page.text(
                x, flow.y, flow.res(sub_style), size, rgb, _pdf_text(dates)
            )
            if sub_style.underline:
                flow.page.hline(
                    x, flow.right, flow.y - 1.0, max(size * 0.06, 0.5), rgb
                )
    flow.descend(title_style.space_after_pt or 0.0)
    if not fmt.dates_on_title_line and dates:
        _para(flow, [(dates, sub_style)], sub_style)


def _bullet(flow: _Flow, text: str, fmt: FormatProfile):
    style = fmt.role(ROLE_BULLET)
    indent_pt = (fmt.bullet_left_indent_in or 0.0) * 72.0
    glyph = f"{fmt.bullet_glyph} " if fmt.bullet_glyph else ""
    flow.ensure(0)
    flow.descend(style.space_before_pt or 0.0)
    leading = _line_height(style)
    avail = flow.right - (flow.left + indent_pt)
    for line in _wrap(_atoms([(f"{glyph}{text}", style)]), avail):
        flow.ensure(leading)
        flow.descend(leading)
        _draw_atoms(flow, line, flow.left + indent_pt, flow.y)
    flow.descend(style.space_after_pt or 0.0)


def _section_header(flow: _Flow, section: str, fmt: FormatProfile):
    # The docx path reproduces blank paragraphs; here they are one blank
    # body-height descent each.
    for _ in range(fmt.section_blank_lines.get(section, 0)):
        flow.ensure(0)
        flow.descend(_line_height(fmt.role(ROLE_BODY)))
    title = fmt.section_titles.get(section) or DEFAULT_SECTION_TITLES[section]
    _para(
        flow,
        [(title, fmt.section_header_roles.get(section, fmt.role(ROLE_SECTION_HEADER)))],
        fmt.section_header_roles.get(section, fmt.role(ROLE_SECTION_HEADER)),
    )


def render_pdf(content: ResumeContent, fmt: FormatProfile) -> bytes:
    """Rebuild a resume PDF from canonical content through a FormatProfile —
    the pdf counterpart of render_docx."""
    flow = _Flow(fmt)

    header = content.header
    if header.name:
        style = fmt.role(ROLE_NAME)
        _para(flow, [(header.name, style)], style)
    contact_style = fmt.role(ROLE_CONTACT)
    contact_bits = [bit for bit in [header.email, header.phone] if bit]
    if not fmt.location_on_own_line and header.location:
        contact_bits.append(header.location)
    contact_bits.extend(bit for bit in header.links if bit)
    if contact_bits:
        link_style = fmt.roles.get(ROLE_LINK)
        runs: list[tuple[str, RoleStyle]] = []
        for i, bit in enumerate(contact_bits):
            if i:
                runs.append((f"{fmt.contact_separator}", contact_style))
            style = (
                _overlay_link(contact_style, link_style)
                if link_style and bit in set(header.links)
                else contact_style
            )
            runs.append((bit, style))
        _para(flow, runs, contact_style)
    if fmt.location_on_own_line and header.location:
        style = fmt.role(ROLE_LOCATION)
        _para(flow, [(header.location, style)], style)

    body_style = fmt.role(ROLE_BODY)
    sub_style = fmt.role(ROLE_ENTRY_SUB)

    for section_key in fmt.section_order:
        if section_key == SECTION_SUMMARY and content.summary:
            _section_header(flow, section_key, fmt)
            _para(flow, [(content.summary, body_style)], body_style)

        elif section_key == SECTION_EXPERIENCE and content.experiences:
            _section_header(flow, section_key, fmt)
            for exp in content.experiences:
                _entry_header(
                    flow,
                    exp.title,
                    exp.company,
                    _dates(exp.start_date, exp.end_date, fmt),
                    fmt,
                )
                for bullet in exp.bullets:
                    _bullet(flow, bullet, fmt)

        elif section_key == SECTION_SKILLS and content.skill_groups:
            _section_header(flow, section_key, fmt)
            if fmt.skills_layout == SKILLS_LAYOUT_GROUPED:
                for group in content.skill_groups:
                    runs = []
                    if group.category:
                        label_style = (
                            replace(body_style, bold=True)
                            if fmt.skills_category_bold
                            else body_style
                        )
                        runs.append(
                            (
                                f"{group.category}{fmt.skills_category_separator}",
                                label_style,
                            )
                        )
                    runs.append((", ".join(group.skills), body_style))
                    _para(flow, runs, body_style)
            else:
                flat = [s for g in content.skill_groups for s in g.skills]
                _para(flow, [(", ".join(flat), body_style)], body_style)

        elif section_key == SECTION_EDUCATION and content.education:
            _section_header(flow, section_key, fmt)
            for edu in content.education:
                _entry_header(
                    flow,
                    edu.degree,
                    edu.institution,
                    _dates(edu.start_date, edu.end_date, fmt),
                    fmt,
                )
                if edu.field_of_study:
                    _para(flow, [(edu.field_of_study, sub_style)], sub_style)
                if edu.description:
                    _para(flow, [(edu.description, body_style)], body_style)

        elif section_key == SECTION_PROJECTS and content.projects:
            _section_header(flow, section_key, fmt)
            proj_body = fmt.roles.get(ROLE_PROJECT_BODY, body_style)
            proj_sub = fmt.roles.get(ROLE_PROJECT_SUB, sub_style)
            for proj in content.projects:
                dates = _dates(proj.start_date, proj.end_date, fmt)
                if fmt.project_dates_inline:
                    tail = (
                        f"{proj.link}{fmt.entry_title_separator}{dates}"
                        if proj.link and not fmt.project_link_on_own_line
                        else dates
                    )
                    _entry_header(
                        flow,
                        proj.name,
                        tail,
                        "",
                        fmt,
                        title_role=ROLE_PROJECT_TITLE,
                        sub_role=ROLE_PROJECT_SUB,
                    )
                else:
                    tail = proj.link if not fmt.project_link_on_own_line else None
                    _entry_header(
                        flow,
                        proj.name,
                        tail,
                        dates,
                        fmt,
                        title_role=ROLE_PROJECT_TITLE,
                        sub_role=ROLE_PROJECT_SUB,
                    )
                if fmt.project_link_on_own_line and proj.link:
                    link_style = fmt.roles.get(ROLE_LINK)
                    style = (
                        _overlay_link(proj_sub, link_style)
                        if link_style
                        else proj_sub
                    )
                    _para(flow, [(proj.link, style)], style)
                if proj.description:
                    _para(flow, [(proj.description, proj_body)], proj_body)

    return _assemble(flow.pages, flow.font_res)


def _assemble(pages: list[_Page], font_res: dict[str, str]) -> bytes:
    """Object graph: catalog → pages → page/content pairs → fonts. Only the
    base-14 faces actually used get resources."""
    used = list(font_res.items())  # [(face, "F1"), ...]
    if not used:
        used = [("Helvetica", "F1")]

    font_first = 3 + len(pages) * 2

    objs: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"",  # pages tree — filled below
    ]
    kids: list[str] = []
    for i, page in enumerate(pages):
        page_num = 3 + i * 2
        kids.append(f"{page_num} 0 R")
        res_dict = " ".join(
            f"/{res} {font_first + j} 0 R" for j, (_, res) in enumerate(used)
        )
        objs.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {_PAGE_W:.0f} "
            f"{_PAGE_H:.0f}] /Resources << /Font << {res_dict} >> >> "
            f"/Contents {page_num + 1} 0 R >>".encode()
        )
        body = b"\n".join(page.ops)
        objs.append(
            b"<< /Length "
            + str(len(body)).encode()
            + b" >>\nstream\n"
            + body
            + b"\nendstream"
        )
    objs[1] = (
        f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>"
    ).encode()
    global _WIDTHS
    if _WIDTHS is None:
        _WIDTHS = _build_widths()
    for j, (name, _res) in enumerate(used):
        # Explicit /Widths — without it extractors can't size glyphs and
        # every char collapses to zero advance.
        widths = _WIDTHS[name]
        arr = " ".join(
            str(widths.get(bytes([b]).decode("cp1252", "replace"), 556))
            for b in range(32, 256)
        )
        objs.append(
            f"<< /Type /Font /Subtype /Type1 /BaseFont /{name} "
            f"/Encoding /WinAnsiEncoding /FirstChar 32 /LastChar 255 "
            f"/Widths [{arr}] "
            f"/FontDescriptor << /Type /FontDescriptor /FontName /{name} "
            f"/Flags 32 /FontBBox [-166 -225 1000 931] /ItalicAngle 0 "
            f"/Ascent 718 /Descent -207 /CapHeight 718 /StemV 80 >> >>".encode()
        )

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


# AFM width tables (per-1000em units) for the base-14 fonts, packed as
# "hexcode:width," strings — latin-1 coverage plus the punctuation resumes
# actually carry (dashes, quotes, bullets, …).
_WIDTHS_RAW = {
    "Helvetica": "20:278,21:278,22:355,23:556,24:556,25:889,26:667,27:191,28:333,29:333,2a:389,2b:584,2c:278,2d:333,2e:278,2f:278,30:556,31:556,32:556,33:556,34:556,35:556,36:556,37:556,38:556,39:556,3a:278,3b:278,3c:584,3d:584,3e:584,3f:556,40:1015,41:667,42:667,43:722,44:722,45:667,46:611,47:778,48:722,49:278,4a:500,4b:667,4c:556,4d:833,4e:722,4f:778,50:667,51:778,52:722,53:667,54:611,55:722,56:667,57:944,58:667,59:667,5a:611,5b:278,5c:278,5d:278,5e:469,5f:556,60:333,61:556,62:556,63:500,64:556,65:556,66:278,67:556,68:556,69:222,6a:222,6b:500,6c:222,6d:833,6e:556,6f:556,70:556,71:556,72:333,73:500,74:278,75:556,76:500,77:722,78:500,79:500,7a:500,7b:334,7c:260,7d:334,7e:584,2022:350,2013:556,2014:1000,2018:222,2019:222,201c:333,201d:333,2026:1000,b7:278,2039:333,203a:333,ab:556,bb:556,e9:556,e8:556,ea:556,eb:556,e1:556,e0:556,e2:556,e4:556,ed:278,ec:278,ee:278,ef:278,f3:556,f2:556,f4:556,f6:556,fa:556,f9:556,fb:556,fc:556,e7:500,f1:556,c9:667,c8:667,c1:667,c0:667,d6:778,dc:722,d1:722,b0:400,ae:737,a9:737,2122:1000,",
    "Helvetica-Bold": "20:278,21:333,22:474,23:556,24:556,25:889,26:722,27:238,28:333,29:333,2a:389,2b:584,2c:278,2d:333,2e:278,2f:278,30:556,31:556,32:556,33:556,34:556,35:556,36:556,37:556,38:556,39:556,3a:333,3b:333,3c:584,3d:584,3e:584,3f:611,40:975,41:722,42:722,43:722,44:722,45:667,46:611,47:778,48:722,49:278,4a:556,4b:722,4c:611,4d:833,4e:722,4f:778,50:667,51:778,52:722,53:667,54:611,55:722,56:667,57:944,58:667,59:667,5a:611,5b:333,5c:278,5d:333,5e:584,5f:556,60:333,61:556,62:500,63:556,64:611,65:556,66:333,67:611,68:611,69:278,6a:278,6b:556,6c:278,6d:889,6e:611,6f:611,70:611,71:611,72:389,73:556,74:333,75:611,76:556,77:778,78:556,79:556,7a:500,7b:389,7c:280,7d:389,7e:584,2022:350,2013:556,2014:1000,2018:278,2019:278,201c:500,201d:500,2026:1000,b7:278,2039:333,203a:333,ab:556,bb:556,e9:556,e8:556,ea:556,eb:556,e1:556,e0:556,e2:556,e4:556,ed:278,ec:278,ee:278,ef:278,f3:611,f2:611,f4:611,f6:611,fa:611,f9:611,fb:611,fc:611,e7:556,f1:611,c9:667,c8:667,c1:722,c0:722,d6:778,dc:722,d1:722,b0:400,ae:737,a9:737,2122:1000,",
    "Helvetica-Oblique": "20:278,21:278,22:355,23:556,24:556,25:889,26:667,27:191,28:333,29:333,2a:389,2b:584,2c:278,2d:333,2e:278,2f:278,30:556,31:556,32:556,33:556,34:556,35:556,36:556,37:556,38:556,39:556,3a:278,3b:278,3c:584,3d:584,3e:584,3f:556,40:1015,41:667,42:667,43:722,44:722,45:667,46:611,47:778,48:722,49:278,4a:500,4b:667,4c:556,4d:833,4e:722,4f:778,50:667,51:778,52:722,53:667,54:611,55:722,56:667,57:944,58:667,59:667,5a:611,5b:278,5c:278,5d:278,5e:469,5f:556,60:333,61:556,62:556,63:500,64:556,65:556,66:278,67:556,68:556,69:222,6a:222,6b:500,6c:222,6d:833,6e:556,6f:556,70:556,71:556,72:333,73:500,74:278,75:556,76:500,77:722,78:500,79:500,7a:500,7b:334,7c:260,7d:334,7e:584,2022:350,2013:556,2014:1000,2018:222,2019:222,201c:333,201d:333,2026:1000,b7:278,2039:333,203a:333,ab:556,bb:556,e9:556,e8:556,ea:556,eb:556,e1:556,e0:556,e2:556,e4:556,ed:278,ec:278,ee:278,ef:278,f3:556,f2:556,f4:556,f6:556,fa:556,f9:556,fb:556,fc:556,e7:500,f1:556,c9:667,c8:667,c1:667,c0:667,d6:778,dc:722,d1:722,b0:400,ae:737,a9:737,2122:1000,",
    "Helvetica-BoldOblique": "20:278,21:333,22:474,23:556,24:556,25:889,26:722,27:238,28:333,29:333,2a:389,2b:584,2c:278,2d:333,2e:278,2f:278,30:556,31:556,32:556,33:556,34:556,35:556,36:556,37:556,38:556,39:556,3a:333,3b:333,3c:584,3d:584,3e:584,3f:611,40:975,41:722,42:722,43:722,44:722,45:667,46:611,47:778,48:722,49:278,4a:556,4b:722,4c:611,4d:833,4e:722,4f:778,50:667,51:778,52:722,53:667,54:611,55:722,56:667,57:944,58:667,59:667,5a:611,5b:333,5c:278,5d:333,5e:584,5f:556,60:333,61:556,62:500,63:556,64:611,65:556,66:333,67:611,68:611,69:278,6a:278,6b:556,6c:278,6d:889,6e:611,6f:611,70:611,71:611,72:389,73:556,74:333,75:611,76:556,77:778,78:556,79:556,7a:500,7b:389,7c:280,7d:389,7e:584,2022:350,2013:556,2014:1000,2018:278,2019:278,201c:500,201d:500,2026:1000,b7:278,2039:333,203a:333,ab:556,bb:556,e9:556,e8:556,ea:556,eb:556,e1:556,e0:556,e2:556,e4:556,ed:278,ec:278,ee:278,ef:278,f3:611,f2:611,f4:611,f6:611,fa:611,f9:611,fb:611,fc:611,e7:556,f1:611,c9:667,c8:667,c1:722,c0:722,d6:778,dc:722,d1:722,b0:400,ae:737,a9:737,2122:1000,",
    "Times-Roman": "20:250,21:333,22:408,23:500,24:500,25:833,26:778,27:180,28:333,29:333,2a:500,2b:564,2c:250,2d:333,2e:250,2f:278,30:500,31:500,32:500,33:500,34:500,35:500,36:500,37:500,38:500,39:500,3a:278,3b:278,3c:564,3d:564,3e:564,3f:444,40:921,41:722,42:667,43:667,44:722,45:611,46:556,47:722,48:722,49:333,4a:389,4b:722,4c:611,4d:889,4e:722,4f:722,50:556,51:722,52:667,53:556,54:611,55:722,56:722,57:944,58:722,59:722,5a:611,5b:333,5c:278,5d:333,5e:469,5f:500,60:333,61:444,62:500,63:444,64:500,65:444,66:333,67:500,68:500,69:278,6a:278,6b:500,6c:278,6d:778,6e:500,6f:500,70:500,71:500,72:333,73:389,74:278,75:500,76:500,77:722,78:500,79:500,7a:444,7b:480,7c:200,7d:480,7e:541,2022:350,2013:500,2014:1000,2018:333,2019:333,201c:444,201d:444,2026:1000,b7:250,2039:333,203a:333,ab:500,bb:500,e9:444,e8:444,ea:444,eb:444,e1:444,e0:444,e2:444,e4:444,ed:278,ec:278,ee:278,ef:278,f3:500,f2:500,f4:500,f6:500,fa:500,f9:500,fb:500,fc:500,e7:444,f1:500,c9:611,c8:611,c1:722,c0:722,d6:722,dc:722,d1:722,b0:400,ae:760,a9:760,2122:980,",
    "Times-Bold": "20:250,21:333,22:555,23:500,24:500,25:1000,26:833,27:278,28:333,29:333,2a:500,2b:570,2c:250,2d:333,2e:250,2f:278,30:500,31:500,32:500,33:500,34:500,35:500,36:500,37:500,38:500,39:500,3a:333,3b:333,3c:570,3d:570,3e:570,3f:500,40:930,41:722,42:667,43:722,44:722,45:667,46:611,47:778,48:778,49:389,4a:500,4b:778,4c:667,4d:944,4e:722,4f:778,50:611,51:778,52:722,53:556,54:667,55:722,56:722,57:1000,58:667,59:722,5a:667,5b:333,5c:278,5d:333,5e:581,5f:500,60:333,61:500,62:500,63:444,64:500,65:444,66:333,67:500,68:556,69:278,6a:333,6b:556,6c:278,6d:833,6e:556,6f:500,70:500,71:500,72:389,73:389,74:278,75:500,76:444,77:667,78:500,79:444,7a:389,7b:394,7c:220,7d:394,7e:520,2022:350,2013:500,2014:1000,2018:333,2019:333,201c:500,201d:500,2026:1000,b7:250,2039:333,203a:333,ab:500,bb:500,e9:444,e8:444,ea:444,eb:444,e1:500,e0:500,e2:500,e4:500,ed:278,ec:278,ee:278,ef:278,f3:500,f2:500,f4:500,f6:500,fa:556,f9:556,fb:556,fc:556,e7:444,f1:556,c9:667,c8:667,c1:722,c0:722,d6:722,dc:722,d1:722,b0:400,ae:747,a9:747,2122:1000,",
    "Times-Italic": "20:250,21:333,22:420,23:500,24:500,25:833,26:778,27:214,28:333,29:333,2a:500,2b:675,2c:250,2d:333,2e:250,2f:278,30:500,31:500,32:500,33:500,34:500,35:500,36:500,37:500,38:500,39:500,3a:333,3b:333,3c:675,3d:675,3e:675,3f:500,40:920,41:611,42:611,43:667,44:722,45:611,46:611,47:722,48:722,49:333,4a:444,4b:667,4c:556,4d:833,4e:667,4f:722,50:611,51:722,52:611,53:500,54:556,55:722,56:611,57:833,58:611,59:556,5a:556,5b:389,5c:278,5d:389,5e:422,5f:500,60:333,61:444,62:500,63:444,64:500,65:444,66:278,67:500,68:500,69:278,6a:278,6b:444,6c:278,6d:722,6e:500,6f:500,70:500,71:500,72:389,73:389,74:278,75:500,76:444,77:667,78:444,79:444,7a:389,7b:400,7c:275,7d:400,7e:541,2022:350,2013:500,2014:889,2018:333,2019:333,201c:556,201d:556,2026:889,b7:250,2039:333,203a:333,ab:500,bb:500,e9:444,e8:444,ea:444,eb:444,e1:444,e0:444,e2:444,e4:444,ed:278,ec:278,ee:278,ef:278,f3:500,f2:500,f4:500,f6:500,fa:500,f9:500,fb:500,fc:500,e7:444,f1:500,c9:611,c8:611,c1:611,c0:611,d6:722,dc:722,d1:667,b0:400,ae:760,a9:760,2122:980,",
    "Times-BoldItalic": "20:250,21:389,22:555,23:500,24:500,25:833,26:778,27:278,28:333,29:333,2a:500,2b:570,2c:250,2d:333,2e:250,2f:278,30:500,31:500,32:500,33:500,34:500,35:500,36:500,37:500,38:500,39:500,3a:333,3b:333,3c:570,3d:570,3e:570,3f:500,40:930,41:667,42:667,43:667,44:722,45:667,46:667,47:722,48:778,49:389,4a:500,4b:667,4c:611,4d:889,4e:722,4f:778,50:611,51:722,52:667,53:556,54:611,55:722,56:667,57:889,58:667,59:611,5a:611,5b:333,5c:278,5d:333,5e:570,5f:500,60:333,61:500,62:500,63:444,64:500,65:444,66:333,67:500,68:556,69:278,6a:278,6b:500,6c:278,6d:778,6e:556,6f:500,70:500,71:500,72:389,73:389,74:278,75:500,76:444,77:667,78:500,79:444,7a:389,7b:348,7c:220,7d:348,7e:570,2022:350,2013:500,2014:1000,2018:333,2019:333,201c:500,201d:500,2026:1000,b7:250,2039:333,203a:333,ab:500,bb:500,e9:444,e8:444,ea:444,eb:444,e1:500,e0:500,e2:500,e4:500,ed:278,ec:278,ee:278,ef:278,f3:500,f2:500,f4:500,f6:500,fa:500,f9:500,fb:500,fc:500,e7:444,f1:500,c9:667,c8:667,c1:722,c0:722,d6:778,dc:722,d1:722,b0:400,ae:747,a9:747,2122:1000,",
    "Courier": "20:600,21:600,22:600,23:600,24:600,25:600,26:600,27:600,28:600,29:600,2a:600,2b:600,2c:600,2d:600,2e:600,2f:600,30:600,31:600,32:600,33:600,34:600,35:600,36:600,37:600,38:600,39:600,3a:600,3b:600,3c:600,3d:600,3e:600,3f:600,40:600,41:600,42:600,43:600,44:600,45:600,46:600,47:600,48:600,49:600,4a:600,4b:600,4c:600,4d:600,4e:600,4f:600,50:600,51:600,52:600,53:600,54:600,55:600,56:600,57:600,58:600,59:600,5a:600,5b:600,5c:600,5d:600,5e:600,5f:600,60:600,61:600,62:600,63:600,64:600,65:600,66:600,67:600,68:600,69:600,6a:600,6b:600,6c:600,6d:600,6e:600,6f:600,70:600,71:600,72:600,73:600,74:600,75:600,76:600,77:600,78:600,79:600,7a:600,7b:600,7c:600,7d:600,7e:600,2022:600,2013:600,2014:600,2018:600,2019:600,201c:600,201d:600,2026:600,b7:600,2039:600,203a:600,ab:600,bb:600,e9:600,e8:600,ea:600,eb:600,e1:600,e0:600,e2:600,e4:600,ed:600,ec:600,ee:600,ef:600,f3:600,f2:600,f4:600,f6:600,fa:600,f9:600,fb:600,fc:600,e7:600,f1:600,c9:600,c8:600,c1:600,c0:600,d6:600,dc:600,d1:600,b0:600,ae:600,a9:600,2122:600,",
    "Courier-Bold": "20:600,21:600,22:600,23:600,24:600,25:600,26:600,27:600,28:600,29:600,2a:600,2b:600,2c:600,2d:600,2e:600,2f:600,30:600,31:600,32:600,33:600,34:600,35:600,36:600,37:600,38:600,39:600,3a:600,3b:600,3c:600,3d:600,3e:600,3f:600,40:600,41:600,42:600,43:600,44:600,45:600,46:600,47:600,48:600,49:600,4a:600,4b:600,4c:600,4d:600,4e:600,4f:600,50:600,51:600,52:600,53:600,54:600,55:600,56:600,57:600,58:600,59:600,5a:600,5b:600,5c:600,5d:600,5e:600,5f:600,60:600,61:600,62:600,63:600,64:600,65:600,66:600,67:600,68:600,69:600,6a:600,6b:600,6c:600,6d:600,6e:600,6f:600,70:600,71:600,72:600,73:600,74:600,75:600,76:600,77:600,78:600,79:600,7a:600,7b:600,7c:600,7d:600,7e:600,2022:600,2013:600,2014:600,2018:600,2019:600,201c:600,201d:600,2026:600,b7:600,2039:600,203a:600,ab:600,bb:600,e9:600,e8:600,ea:600,eb:600,e1:600,e0:600,e2:600,e4:600,ed:600,ec:600,ee:600,ef:600,f3:600,f2:600,f4:600,f6:600,fa:600,f9:600,fb:600,fc:600,e7:600,f1:600,c9:600,c8:600,c1:600,c0:600,d6:600,dc:600,d1:600,b0:600,ae:600,a9:600,2122:600,",
    "Courier-Oblique": "20:600,21:600,22:600,23:600,24:600,25:600,26:600,27:600,28:600,29:600,2a:600,2b:600,2c:600,2d:600,2e:600,2f:600,30:600,31:600,32:600,33:600,34:600,35:600,36:600,37:600,38:600,39:600,3a:600,3b:600,3c:600,3d:600,3e:600,3f:600,40:600,41:600,42:600,43:600,44:600,45:600,46:600,47:600,48:600,49:600,4a:600,4b:600,4c:600,4d:600,4e:600,4f:600,50:600,51:600,52:600,53:600,54:600,55:600,56:600,57:600,58:600,59:600,5a:600,5b:600,5c:600,5d:600,5e:600,5f:600,60:600,61:600,62:600,63:600,64:600,65:600,66:600,67:600,68:600,69:600,6a:600,6b:600,6c:600,6d:600,6e:600,6f:600,70:600,71:600,72:600,73:600,74:600,75:600,76:600,77:600,78:600,79:600,7a:600,7b:600,7c:600,7d:600,7e:600,2022:600,2013:600,2014:600,2018:600,2019:600,201c:600,201d:600,2026:600,b7:600,2039:600,203a:600,ab:600,bb:600,e9:600,e8:600,ea:600,eb:600,e1:600,e0:600,e2:600,e4:600,ed:600,ec:600,ee:600,ef:600,f3:600,f2:600,f4:600,f6:600,fa:600,f9:600,fb:600,fc:600,e7:600,f1:600,c9:600,c8:600,c1:600,c0:600,d6:600,dc:600,d1:600,b0:600,ae:600,a9:600,2122:600,",
    "Courier-BoldOblique": "20:600,21:600,22:600,23:600,24:600,25:600,26:600,27:600,28:600,29:600,2a:600,2b:600,2c:600,2d:600,2e:600,2f:600,30:600,31:600,32:600,33:600,34:600,35:600,36:600,37:600,38:600,39:600,3a:600,3b:600,3c:600,3d:600,3e:600,3f:600,40:600,41:600,42:600,43:600,44:600,45:600,46:600,47:600,48:600,49:600,4a:600,4b:600,4c:600,4d:600,4e:600,4f:600,50:600,51:600,52:600,53:600,54:600,55:600,56:600,57:600,58:600,59:600,5a:600,5b:600,5c:600,5d:600,5e:600,5f:600,60:600,61:600,62:600,63:600,64:600,65:600,66:600,67:600,68:600,69:600,6a:600,6b:600,6c:600,6d:600,6e:600,6f:600,70:600,71:600,72:600,73:600,74:600,75:600,76:600,77:600,78:600,79:600,7a:600,7b:600,7c:600,7d:600,7e:600,2022:600,2013:600,2014:600,2018:600,2019:600,201c:600,201d:600,2026:600,b7:600,2039:600,203a:600,ab:600,bb:600,e9:600,e8:600,ea:600,eb:600,e1:600,e0:600,e2:600,e4:600,ed:600,ec:600,ee:600,ef:600,f3:600,f2:600,f4:600,f6:600,fa:600,f9:600,fb:600,fc:600,e7:600,f1:600,c9:600,c8:600,c1:600,c0:600,d6:600,dc:600,d1:600,b0:600,ae:600,a9:600,2122:600,",
}
