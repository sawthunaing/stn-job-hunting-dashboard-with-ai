"""Render a tailored CV (markdown) into .docx or .pdf.

Layout (A4, narrow margins, serif body, two-column, S-40):
  Header     left-aligned name (19pt bold) + accent-coloured headline/tagline
             + contact line with clickable e-mail / LinkedIn / GitHub / website
  Region A   two columns: Summary + Skills (left) | Education + Certifications
             + Find Online (right)
  Experience full width, unchanged entry/bullet style, company name accented
  Region B   two columns: Projects (left) | Key Achievements (right)
  Section    bold CAPS heading with a short accent-coloured rule underneath
  Entry      Title bold black / Company bold accent / Dates+Location muted,
             one line each (falls back to a single bold line with no pipes,
             e.g. Key Achievements)
  Bullets    "•" at 0.25in, text at 0.5in
  Skills     "**Category:** value" renders as an accent label line + value
             line + thin rule, one per category

Which heading goes in which region is decided by name (see _bucket_key), so
older stored CVs (single "Skills, Languages, ..." heading, no Certifications/
Key Achievements sections) still render - they just leave some regions empty.

The tailored body comes from the AI as markdown (see ai.py for the contract).
The DOCX uses python-docx with Cambria, which ships with Word; the two
columns are a borderless 1x2 table. The PDF is typeset by Typst (external
`typst` binary, see PDF section below) and embeds the bundled Lora font
(SIL OFL, app/fonts); the two columns use Typst's grid().
"""
from __future__ import annotations
import io
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_KV_RE = re.compile(r"^\*\*([^*]+?):\*\*\s*(.*)$")

FONTS_DIR = Path(__file__).resolve().parent / "fonts"
DOCX_FONT = "Cambria"

# Page / type metrics, in points unless noted.
MARGIN_SIDE_IN = 0.375
MARGIN_TOP_IN = 0.4
MARGIN_BOTTOM_IN = 0.4
NAME_PT, CONTACT_PT, HEADING_PT, ENTRY_PT, BODY_PT = 19, 7.5, 11, 9, 9
BULLET_INDENT_IN, BULLET_TEXT_IN = 0.25, 0.5

ACCENT_HEX = "2563EB"   # section rules, company names, category labels
MUTED_HEX = "595959"    # dates/location meta line under an entry
RULE_HEX = "CCCCCC"     # thin separator under each skills category

PAGE_WIDTH_IN, PAGE_HEIGHT_IN = 8.27, 11.69
CONTENT_WIDTH_IN = PAGE_WIDTH_IN - 2 * MARGIN_SIDE_IN
COLUMN_GUTTER_IN = 0.2
REGION_A_LEFT_FRAC = 0.62  # Summary/Skills column share of the gutter-free width


def _split_bold(text: str) -> list[tuple[str, bool]]:
    runs: list[tuple[str, bool]] = []
    pos = 0
    for m in _BOLD_RE.finditer(text):
        if m.start() > pos:
            runs.append((text[pos:m.start()], False))
        runs.append((m.group(1), True))
        pos = m.end()
    if pos < len(text):
        runs.append((text[pos:], False))
    return runs or [("", False)]


def _parse_blocks(md: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    bullets: list[str] = []
    kvs: list[tuple[str, str]] = []

    def flush():
        nonlocal bullets, kvs
        if bullets:
            blocks.append({"kind": "bullets", "items": bullets})
            bullets = []
        if kvs:
            blocks.append({"kind": "kvs", "items": kvs})
            kvs = []

    for raw in md.replace("\r\n", "\n").split("\n"):
        s = raw.strip()
        if not s:
            flush(); continue
        if s.startswith("### "):
            flush()
            # Older stored CVs use " @@ " before the dates; show it as a pipe.
            blocks.append({"kind": "entry", "text": s[4:].strip().replace(" @@ ", " | ")})
        elif s.startswith("## "):
            flush(); blocks.append({"kind": "h2", "text": s[3:].strip()})
        elif s.startswith("# "):
            flush(); blocks.append({"kind": "h1", "text": s[2:].strip()})
        elif s.startswith(("- ", "* ")):
            if kvs:
                flush()
            bullets.append(s[2:].strip())
        elif re.match(r"^\d+\.\s", s):
            bullets.append(re.sub(r"^\d+\.\s", "", s))
        elif _KV_RE.match(s):
            if bullets:
                flush()
            m = _KV_RE.match(s)
            kvs.append((m.group(1).strip() + ":", m.group(2).strip()))
        else:
            flush(); blocks.append({"kind": "para", "text": s})
    flush()
    return blocks


def _url(value: str) -> str:
    v = value.strip()
    return v if re.match(r"^[a-z][a-z0-9+.-]*:", v, re.I) else f"https://{v}"


def _contact_parts(p) -> list[tuple[str, str, str | None]]:
    """Return [(label, text, href|None)] in display order."""
    g = lambda name: (getattr(p, name, None) or "").strip()
    parts: list[tuple[str, str, str | None]] = []
    if g("email"):
        parts.append(("Email: ", g("email"), f"mailto:{g('email')}"))
    if g("phone"):
        parts.append(("Mobile: ", g("phone"), None))
    if g("linkedin"):
        parts.append(("", "LinkedIn", _url(g("linkedin"))))
    if g("github"):
        parts.append(("", "GitHub", _url(g("github"))))
    if g("website"):
        parts.append(("", "Website", _url(g("website"))))
    if g("location"):
        parts.append(("Location: ", g("location"), None))
    return parts


def _social_links(p) -> list[tuple[str, str]]:
    """(display text, href) for website/LinkedIn/GitHub only, for the Find Online block."""
    return [(text, href) for label, text, href in _contact_parts(p) if href and label == ""]


def _prepare(profile, content_md: str) -> tuple[str, list[dict[str, Any]]]:
    name = (getattr(profile, "full_name", None) or "").strip() or "Curriculum Vitae"
    blocks = _parse_blocks(content_md)
    if blocks and blocks[0]["kind"] == "h1" and blocks[0]["text"].lower() in (name.lower(), ""):
        blocks = blocks[1:]
    return name, blocks


# ---- Section bucketing (for the two-column regions) ------------------------

def _bucket_key(heading: str) -> str:
    """Which region a '## ' heading's content belongs in."""
    t = heading.strip().lower()
    if t.startswith("summary"):
        return "left_a"
    if t.startswith("skills"):
        return "left_a"
    if t.startswith("education"):
        return "right_a"
    if t.startswith("certif"):
        return "right_a"
    if t.startswith("work experience") or t.startswith("experience"):
        return "experience"
    if t.startswith("projects"):
        return "left_b"
    if "achievement" in t:
        return "right_b"
    return "other"


def _bucket_blocks(blocks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group parsed blocks by region. Unknown/legacy headings fall into 'other'
    (rendered full-width) so nothing from an older stored CV is silently dropped."""
    buckets: dict[str, list[dict[str, Any]]] = {
        "left_a": [], "right_a": [], "experience": [], "left_b": [], "right_b": [], "other": [],
    }
    current = "other"
    for b in blocks:
        if b["kind"] in ("h1", "h2"):
            current = _bucket_key(b["text"])
        buckets[current].append(b)
    return buckets


# ---- DOCX -----------------------------------------------------------------

def _docx_hyperlink(paragraph, url: str, text: str, size_pt: float, color_hex: str = "0563C1"):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.opc.constants import RELATIONSHIP_TYPE as RT

    r_id = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        fonts.set(qn(attr), DOCX_FONT)
    color = OxmlElement("w:color"); color.set(qn("w:val"), color_hex)
    underline = OxmlElement("w:u"); underline.set(qn("w:val"), "single")
    sz = OxmlElement("w:sz"); sz.set(qn("w:val"), str(int(size_pt * 2)))
    for el in (fonts, color, underline, sz):
        rpr.append(el)
    run.append(rpr)
    t = OxmlElement("w:t"); t.text = text
    t.set(qn("xml:space"), "preserve")
    run.append(t)
    link.append(run)
    paragraph._p.append(link)


def _docx_bottom_border(paragraph, size_eighths: int = 6, color_hex: str = "000000"):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size_eighths))
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color_hex)
    pbdr.append(bottom)
    paragraph._p.get_or_add_pPr().append(pbdr)


def _docx_strip_table_borders(table):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "none")
        el.set(qn("w:sz"), "0")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "auto")
        borders.append(el)
    tbl_pr.append(borders)


class _CellSink:
    """Wraps a table cell so add_paragraph() reuses its existing empty first
    paragraph once, instead of leaving a stray blank line at the column top."""

    def __init__(self, cell):
        self._cell = cell
        self._used_first = False

    def add_paragraph(self):
        if not self._used_first:
            self._used_first = True
            return self._cell.paragraphs[0]
        return self._cell.add_paragraph()


def build_docx(profile, content_md: str) -> bytes:
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT

    name, blocks = _prepare(profile, content_md)
    buckets = _bucket_blocks(blocks)

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(PAGE_WIDTH_IN), Inches(PAGE_HEIGHT_IN)
    sec.left_margin = sec.right_margin = Inches(MARGIN_SIDE_IN)
    sec.top_margin, sec.bottom_margin = Inches(MARGIN_TOP_IN), Inches(MARGIN_BOTTOM_IN)

    normal = doc.styles["Normal"]
    normal.font.name = DOCX_FONT
    normal.font.size = Pt(BODY_PT)

    BLACK = RGBColor(0, 0, 0)
    ACCENT = RGBColor.from_string(ACCENT_HEX)
    MUTED = RGBColor.from_string(MUTED_HEX)

    def add_runs(p, text, *, bold=False, size=BODY_PT, color=BLACK):
        for seg, sb in _split_bold(text):
            r = p.add_run(seg)
            r.font.name = DOCX_FONT
            r.bold = bold or sb
            r.font.size = Pt(size)
            r.font.color.rgb = color

    def spacing(p, before=0, after=4, line=1.35):
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.line_spacing = line

    def render_blocks(sink, blocks: list[dict[str, Any]]):
        for b in blocks:
            kind = b["kind"]
            if kind in ("h1", "h2"):
                p = sink.add_paragraph()
                add_runs(p, b["text"].upper(), bold=True, size=HEADING_PT)
                _docx_bottom_border(p, size_eighths=10, color_hex=ACCENT_HEX)
                p.paragraph_format.keep_with_next = True
                spacing(p, 14, 6, 1.0)
            elif kind == "entry":
                parts = [x.strip() for x in b["text"].split(" | ") if x.strip()]
                p = sink.add_paragraph()
                add_runs(p, parts[0] if parts else b["text"], bold=True, size=ENTRY_PT)
                p.paragraph_format.keep_with_next = True
                spacing(p, 10, 1 if len(parts) > 1 else 6)
                if len(parts) > 1:
                    p2 = sink.add_paragraph()
                    add_runs(p2, parts[1], bold=True, size=ENTRY_PT, color=ACCENT)
                    p2.paragraph_format.keep_with_next = True
                    spacing(p2, 0, 1 if len(parts) > 2 else 6)
                if len(parts) > 2:
                    p3 = sink.add_paragraph()
                    add_runs(p3, " · ".join(parts[2:]), size=CONTACT_PT, color=MUTED)
                    p3.paragraph_format.keep_with_next = True
                    spacing(p3, 0, 6)
            elif kind == "bullets":
                for it in b["items"]:
                    p = sink.add_paragraph()
                    p.style = doc.styles["List Bullet"]
                    p.paragraph_format.left_indent = Inches(BULLET_TEXT_IN)
                    p.paragraph_format.first_line_indent = Inches(-(BULLET_TEXT_IN - BULLET_INDENT_IN))
                    add_runs(p, it)
                    spacing(p, 0, 5)
            elif kind == "kvs":
                for label, value in b["items"]:
                    p = sink.add_paragraph()
                    add_runs(p, label, bold=True, color=ACCENT)
                    spacing(p, 6, 1)
                    p2 = sink.add_paragraph()
                    add_runs(p2, value)
                    spacing(p2, 0, 6)
            else:
                p = sink.add_paragraph()
                add_runs(p, b["text"])
                spacing(p, 0, 6)

    def render_two_col(left_blocks, right_blocks, right_extra=None):
        if not (left_blocks or right_blocks or right_extra):
            return
        gutter_free = CONTENT_WIDTH_IN - COLUMN_GUTTER_IN
        left_w = gutter_free * REGION_A_LEFT_FRAC if left_blocks or right_blocks else gutter_free
        right_w = CONTENT_WIDTH_IN - left_w
        table = doc.add_table(rows=1, cols=2)
        table.autofit = False
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        layout = OxmlElement("w:tblLayout"); layout.set(qn("w:type"), "fixed")
        table._tbl.tblPr.append(layout)
        _docx_strip_table_borders(table)
        left_cell, right_cell = table.rows[0].cells
        left_cell.width, right_cell.width = Inches(left_w), Inches(right_w)
        render_blocks(_CellSink(left_cell), left_blocks)
        render_blocks(_CellSink(right_cell), right_blocks)
        if right_extra:
            render_blocks(_CellSink(right_cell), right_extra)

    p = doc.add_paragraph()
    add_runs(p, name, bold=True, size=NAME_PT)
    spacing(p, 0, 1, 1.0)

    headline = (getattr(profile, "headline", None) or "").strip()
    if headline:
        p = doc.add_paragraph()
        add_runs(p, headline, color=ACCENT)
        spacing(p, 0, 3, 1.1)

    contact = _contact_parts(profile)
    if contact:
        p = doc.add_paragraph()
        for i, (label, text, href) in enumerate(contact):
            if i:
                add_runs(p, " | ", size=CONTACT_PT)
            if label:
                add_runs(p, label, size=CONTACT_PT)
            if href:
                _docx_hyperlink(p, href, text, CONTACT_PT)
            else:
                add_runs(p, text, size=CONTACT_PT)
        spacing(p, 0, 10, 1.0)

    if buckets["other"]:
        render_blocks(doc, buckets["other"])

    find_online: list[dict[str, Any]] = []
    social = _social_links(profile)
    if social:
        find_online.append({"kind": "h2", "text": "Find Online"})
        find_online.append({"kind": "bullets", "items": [text for text, _ in social]})
    render_two_col(buckets["left_a"], buckets["right_a"], right_extra=find_online)

    render_blocks(doc, buckets["experience"])

    render_two_col(buckets["left_b"], buckets["right_b"])

    buf = io.BytesIO(); doc.save(buf); return buf.getvalue()


# ---- PDF (Typst) -----------------------------------------------------------

TYPST_BIN = "typst"
TYPST_FONT_FAMILY = "Lora"

_TYPST_ESCAPE_RE = re.compile(r"[\\#*_`$<>@\[\]~/=]")


def _typst_escape(text: str) -> str:
    """Escape characters Typst's markup/content mode treats as special."""
    return _TYPST_ESCAPE_RE.sub(lambda m: "\\" + m.group(0), text)


def _typ(text: str) -> str:
    """Escape text for Typst, re-applying **bold** runs as Typst strong emphasis."""
    out = []
    for seg, bold in _split_bold(text):
        seg = _typst_escape(seg)
        out.append(f"*{seg}*" if bold else seg)
    return "".join(out)


def _typst_contact_line(profile) -> str:
    bits = []
    for label, text, href in _contact_parts(profile):
        shown = _typst_escape(label) + _typst_escape(text)
        bits.append(f'#link("{href}")[{shown}]' if href else shown)
    return " | ".join(bits)


def _typst_heading(text: str) -> list[str]:
    return [
        "#v(14pt)",
        f'#text(size: {HEADING_PT}pt, weight: "bold")[{_typst_escape(text.upper())}]',
        "#v(2pt)",
        f'#rect(width: 26pt, height: 2pt, fill: rgb("#{ACCENT_HEX}"), stroke: none, inset: 0pt)',
        "#v(6pt, weak: true)",
    ]


def _typst_render_blocks(blocks: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for b in blocks:
        kind = b["kind"]
        if kind in ("h1", "h2"):
            lines.extend(_typst_heading(b["text"]))
        elif kind == "entry":
            parts = [x.strip() for x in b["text"].split(" | ") if x.strip()]
            pieces = []
            if parts:
                pieces.append(f'#text(size: {ENTRY_PT}pt, weight: "bold")[{_typ(parts[0])}]')
            if len(parts) > 1:
                pieces.append(
                    f'#text(size: {ENTRY_PT}pt, weight: "bold", fill: rgb("#{ACCENT_HEX}"))[{_typ(parts[1])}]'
                )
            if len(parts) > 2:
                meta = " · ".join(parts[2:])
                pieces.append(f'#text(size: {CONTACT_PT}pt, fill: rgb("#{MUTED_HEX}"))[{_typ(meta)}]')
            lines.append("#v(10pt)")
            for i, piece in enumerate(pieces):
                if i:
                    lines.append("#linebreak()")
                lines.append(piece)
            lines.append("#v(6pt, weak: true)")
        elif kind == "bullets":
            lines.extend(f"- {_typ(it)}" for it in b["items"])
            lines.append("#v(6pt, weak: true)")
        elif kind == "kvs":
            for label, value in b["items"]:
                lines.append(f'#text(weight: "bold", fill: rgb("#{ACCENT_HEX}"))[{_typst_escape(label)}]')
                lines.append("#v(1pt, weak: true)")
                lines.append(f"#text[{_typ(value)}]")
                lines.append("#v(2pt, weak: true)")
                lines.append(f'#rect(width: 100%, height: 0.5pt, fill: rgb("#{RULE_HEX}"), stroke: none, inset: 0pt)')
                lines.append("#v(5pt, weak: true)")
        else:
            lines.append(f"#text(size: {BODY_PT}pt)[{_typ(b['text'])}]")
            lines.append("#v(8pt, weak: true)")
    return lines


def _typst_find_online(profile) -> list[str]:
    social = _social_links(profile)
    if not social:
        return []
    lines = list(_typst_heading("Find Online"))
    for text, href in social:
        lines.append(f'#link("{href}")[→ {_typst_escape(text)}]')
        lines.append("#v(4pt, weak: true)")
    return lines


def _typst_grid(left_lines: list[str], right_lines: list[str], columns: str) -> str:
    left_src = "\n".join(left_lines)
    right_src = "\n".join(right_lines)
    return f"#grid(columns: {columns}, column-gutter: {COLUMN_GUTTER_IN}in,\n[\n{left_src}\n],\n[\n{right_src}\n])"


def _typst_source(profile, content_md: str) -> str:
    name, blocks = _prepare(profile, content_md)
    buckets = _bucket_blocks(blocks)

    lines = [
        f'#set page(paper: "a4", margin: (left: {MARGIN_SIDE_IN}in, right: {MARGIN_SIDE_IN}in, '
        f"top: {MARGIN_TOP_IN}in, bottom: {MARGIN_BOTTOM_IN}in))",
        f'#set text(font: "{TYPST_FONT_FAMILY}", size: {BODY_PT}pt)',
        "#set par(justify: false, leading: 0.95em, spacing: 0pt)",
        f"#set list(marker: [•], indent: {BULLET_INDENT_IN}in, "
        f"body-indent: {BULLET_TEXT_IN - BULLET_INDENT_IN}in, spacing: 0.7em)",
        "",
        f'#text(size: {NAME_PT}pt, weight: "bold")[{_typst_escape(name)}]',
    ]

    headline = (getattr(profile, "headline", None) or "").strip()
    if headline:
        lines.append("#v(5pt)")
        lines.append(f'#text(size: {CONTACT_PT + 2}pt, fill: rgb("#{ACCENT_HEX}"))[{_typst_escape(headline)}]')

    contact_line = _typst_contact_line(profile)
    if contact_line:
        lines.append("#v(4pt)")
        lines.append(f"#text(size: {CONTACT_PT}pt)[{contact_line}]")
    lines.append("#v(8pt, weak: true)")

    if buckets["other"]:
        lines.extend(_typst_render_blocks(buckets["other"]))

    left_a = _typst_render_blocks(buckets["left_a"])
    right_a = _typst_render_blocks(buckets["right_a"]) + _typst_find_online(profile)
    if left_a or right_a:
        lines.append(_typst_grid(left_a, right_a, f"({REGION_A_LEFT_FRAC * 100}%, 1fr)"))

    lines.extend(_typst_render_blocks(buckets["experience"]))

    left_b = _typst_render_blocks(buckets["left_b"])
    right_b = _typst_render_blocks(buckets["right_b"])
    if left_b or right_b:
        lines.append(_typst_grid(left_b, right_b, "(1fr, 1fr)"))

    return "\n".join(lines) + "\n"


def build_pdf(profile, content_md: str) -> bytes:
    """Render the CV to PDF by compiling a generated Typst source with the `typst` CLI."""
    source = _typst_source(profile, content_md)

    with tempfile.TemporaryDirectory(prefix="cv-typst-") as tmp:
        tmp_path = Path(tmp)
        typ_path = tmp_path / "cv.typ"
        pdf_path = tmp_path / "cv.pdf"
        typ_path.write_text(source, encoding="utf-8")

        proc = subprocess.run(
            [TYPST_BIN, "compile", "--font-path", str(FONTS_DIR), str(typ_path), str(pdf_path)],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"typst compile failed: {(proc.stderr or proc.stdout).strip()}")
        return pdf_path.read_bytes()
