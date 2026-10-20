"""Render a tailored CV (markdown) into .docx or .pdf.

Layout (A4, narrow margins, serif body):
  Header     centred name (19pt bold) + centred contact line (7.5pt) with
             clickable e-mail / LinkedIn / GitHub / website links
  Section    bold CAPS heading with a thin rule underneath
  Entry      one bold line:  Title | Organisation | Dates | Location
  Bullets    "•" at 0.25in, text at 0.5in
  Label rows "**Certifications:** ..." as a label column + hanging value

The tailored body comes from the AI as markdown (see ai.py for the contract).
The DOCX uses python-docx with Cambria, which ships with Word. The PDF is
typeset by Typst (external `typst` binary, see PDF section below) and embeds
the bundled Lora font (SIL OFL, app/fonts).
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


def _prepare(profile, content_md: str) -> tuple[str, list[dict[str, Any]]]:
    name = (getattr(profile, "full_name", None) or "").strip() or "Curriculum Vitae"
    blocks = _parse_blocks(content_md)
    if blocks and blocks[0]["kind"] == "h1" and blocks[0]["text"].lower() in (name.lower(), ""):
        blocks = blocks[1:]
    return name, blocks


# ---- DOCX -----------------------------------------------------------------

def _docx_hyperlink(paragraph, url: str, text: str, size_pt: float):
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
    color = OxmlElement("w:color"); color.set(qn("w:val"), "0563C1")
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


def _docx_bottom_border(paragraph, size_eighths: int = 6):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size_eighths))
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "000000")
    pbdr.append(bottom)
    paragraph._p.get_or_add_pPr().append(pbdr)


def build_docx(profile, content_md: str) -> bytes:
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT

    name, blocks = _prepare(profile, content_md)

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)
    sec.left_margin = sec.right_margin = Inches(MARGIN_SIDE_IN)
    sec.top_margin, sec.bottom_margin = Inches(MARGIN_TOP_IN), Inches(MARGIN_BOTTOM_IN)

    normal = doc.styles["Normal"]
    normal.font.name = DOCX_FONT
    normal.font.size = Pt(BODY_PT)

    BLACK = RGBColor(0, 0, 0)

    def add_runs(p, text, *, bold=False, size=BODY_PT):
        for seg, sb in _split_bold(text):
            r = p.add_run(seg)
            r.font.name = DOCX_FONT
            r.bold = bold or sb
            r.font.size = Pt(size)
            r.font.color.rgb = BLACK

    def spacing(p, before=0, after=4, line=1.35):
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.line_spacing = line

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_runs(p, name, bold=True, size=NAME_PT)
    spacing(p, 0, 1, 1.0)

    contact = _contact_parts(profile)
    if contact:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for i, (label, text, href) in enumerate(contact):
            if i:
                add_runs(p, " | ", size=CONTACT_PT)
            if label:
                add_runs(p, label, size=CONTACT_PT)
            if href:
                _docx_hyperlink(p, href, text, CONTACT_PT)
            else:
                add_runs(p, text, size=CONTACT_PT)
        spacing(p, 0, 4, 1.0)

    for b in blocks:
        kind = b["kind"]
        if kind in ("h1", "h2"):
            p = doc.add_paragraph()
            add_runs(p, b["text"].upper(), bold=True, size=HEADING_PT)
            _docx_bottom_border(p)
            p.paragraph_format.keep_with_next = True
            spacing(p, 14, 6, 1.0)
        elif kind == "entry":
            p = doc.add_paragraph()
            add_runs(p, b["text"], bold=True, size=ENTRY_PT)
            p.paragraph_format.keep_with_next = True
            spacing(p, 10, 6)
        elif kind == "bullets":
            for it in b["items"]:
                p = doc.add_paragraph(style="List Bullet")
                p.paragraph_format.left_indent = Inches(BULLET_TEXT_IN)
                p.paragraph_format.first_line_indent = Inches(-(BULLET_TEXT_IN - BULLET_INDENT_IN))
                add_runs(p, it)
                spacing(p, 0, 5)
        elif kind == "kvs":
            col = max(len(label) for label, _ in b["items"]) * 5.6 + 8
            for label, value in b["items"]:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Pt(col)
                p.paragraph_format.first_line_indent = Pt(-col)
                p.paragraph_format.tab_stops.add_tab_stop(Pt(col), WD_TAB_ALIGNMENT.LEFT)
                add_runs(p, label, bold=True)
                p.add_run("\t")
                add_runs(p, value)
                spacing(p, 0, 5)
        else:
            p = doc.add_paragraph()
            add_runs(p, b["text"])
            spacing(p, 0, 6)

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


def _typst_source(profile, content_md: str) -> str:
    name, blocks = _prepare(profile, content_md)

    lines = [
        f'#set page(paper: "a4", margin: (left: {MARGIN_SIDE_IN}in, right: {MARGIN_SIDE_IN}in, '
        f"top: {MARGIN_TOP_IN}in, bottom: {MARGIN_BOTTOM_IN}in))",
        f'#set text(font: "{TYPST_FONT_FAMILY}", size: {BODY_PT}pt)',
        "#set par(justify: false, leading: 0.95em, spacing: 0pt)",
        f"#set list(marker: [•], indent: {BULLET_INDENT_IN}in, "
        f"body-indent: {BULLET_TEXT_IN - BULLET_INDENT_IN}in, spacing: 0.7em)",
        "",
        f'#align(center)[#text(size: {NAME_PT}pt, weight: "bold")[{_typst_escape(name)}]]',
    ]

    contact_line = _typst_contact_line(profile)
    if contact_line:
        lines.append(f"#v(1pt)")
        lines.append(f"#align(center)[#text(size: {CONTACT_PT}pt)[{contact_line}]]")
    lines.append("#v(4pt, weak: true)")

    for b in blocks:
        kind = b["kind"]
        if kind in ("h1", "h2"):
            lines.append("#v(14pt)")
            lines.append(f'#text(size: {HEADING_PT}pt, weight: "bold")[{_typst_escape(b["text"].upper())}]')
            lines.append("#v(2pt)")
            lines.append("#rect(width: 100%, height: 0.75pt, fill: black, stroke: none, inset: 0pt)")
            lines.append("#v(6pt, weak: true)")
        elif kind == "entry":
            lines.append("#v(10pt)")
            lines.append(f'#text(size: {ENTRY_PT}pt, weight: "bold")[{_typ(b["text"])}]')
            lines.append("#v(6pt, weak: true)")
        elif kind == "bullets":
            lines.extend(f"- {_typ(it)}" for it in b["items"])
            lines.append("#v(6pt, weak: true)")
        elif kind == "kvs":
            cells = []
            for label, value in b["items"]:
                cells.append(f"[*{_typst_escape(label)}*]")
                cells.append(f"[{_typ(value)}]")
            table_src = (
                "#table(columns: (auto, 1fr), stroke: none, inset: 0pt, "
                "column-gutter: 8pt, row-gutter: 5pt,\n  "
                + ",\n  ".join(cells)
                + ",\n)"
            )
            lines.append(table_src)
            lines.append("#v(6pt, weak: true)")
        else:
            lines.append(f"#text(size: {BODY_PT}pt)[{_typ(b['text'])}]")
            lines.append("#v(8pt, weak: true)")

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
