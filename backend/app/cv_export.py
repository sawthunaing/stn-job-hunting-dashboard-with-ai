"""Render a tailored CV (markdown) into .docx or .pdf.

Layout (A4, narrow margins, serif body):
  Header     centred name (19pt bold) + centred contact line (7.5pt) with
             clickable e-mail / LinkedIn / GitHub / website links
  Section    bold CAPS heading with a thin rule underneath
  Entry      one bold line:  Title | Organisation | Dates | Location
  Bullets    "•" at 0.25in, text at 0.5in
  Label rows "**Certifications:** ..." as a label column + hanging value

The tailored body comes from the AI as markdown (see ai.py for the contract).
Pure-Python: python-docx + reportlab. The PDF embeds the bundled Lora font
(SIL OFL, app/fonts); the DOCX uses Cambria, which ships with Word.
"""
from __future__ import annotations
import io
import re
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

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

    def spacing(p, before=0, after=2, line=1.1):
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
            spacing(p, 7, 4, 1.0)
        elif kind == "entry":
            p = doc.add_paragraph()
            add_runs(p, b["text"], bold=True, size=ENTRY_PT)
            p.paragraph_format.keep_with_next = True
            spacing(p, 6, 3)
        elif kind == "bullets":
            for it in b["items"]:
                p = doc.add_paragraph(style="List Bullet")
                p.paragraph_format.left_indent = Inches(BULLET_TEXT_IN)
                p.paragraph_format.first_line_indent = Inches(-(BULLET_TEXT_IN - BULLET_INDENT_IN))
                add_runs(p, it)
                spacing(p, 0, 2)
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
                spacing(p, 0, 2)
        else:
            p = doc.add_paragraph()
            add_runs(p, b["text"])
            spacing(p, 0, 4)

    buf = io.BytesIO(); doc.save(buf); return buf.getvalue()


# ---- PDF ------------------------------------------------------------------

def _register_pdf_fonts() -> tuple[str, str, str, str]:
    """Register Lora if bundled; otherwise fall back to the built-in Times."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.fonts import addMapping

    names = {"Regular": "CVSerif", "Bold": "CVSerif-Bold",
             "Italic": "CVSerif-Italic", "BoldItalic": "CVSerif-BoldItalic"}
    files = {k: FONTS_DIR / f"Lora-{k}.ttf" for k in names}
    if not all(f.exists() for f in files.values()):
        return "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic"
    for k, face in names.items():
        if face not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(face, str(files[k])))
    addMapping("CVSerif", 0, 0, names["Regular"])
    addMapping("CVSerif", 1, 0, names["Bold"])
    addMapping("CVSerif", 0, 1, names["Italic"])
    addMapping("CVSerif", 1, 1, names["BoldItalic"])
    return names["Regular"], names["Bold"], names["Italic"], names["BoldItalic"]


def build_pdf(profile, content_md: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.colors import black, HexColor
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.platypus import (
        BaseDocTemplate, PageTemplate, Frame, Paragraph, Table, TableStyle,
        KeepTogether, HRFlowable,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    F, FB, _, _ = _register_pdf_fonts()
    name, blocks = _prepare(profile, content_md)
    ss = getSampleStyleSheet()

    def style(sid, **kw):
        return ParagraphStyle(sid, parent=ss["Normal"], textColor=black, **kw)

    name_s = style("N", fontName=FB, fontSize=NAME_PT, leading=NAME_PT + 4, alignment=TA_CENTER, spaceAfter=1)
    contact_s = style("C", fontName=F, fontSize=CONTACT_PT, leading=CONTACT_PT + 3, alignment=TA_CENTER, spaceAfter=4)
    h2_s = style("H2", fontName=FB, fontSize=HEADING_PT, leading=HEADING_PT + 3, spaceBefore=7)
    entry_s = style("E", fontName=FB, fontSize=ENTRY_PT, leading=ENTRY_PT + 3.5, spaceBefore=6, spaceAfter=3)
    body_s = style("B", fontName=F, fontSize=BODY_PT, leading=BODY_PT + 3.3, alignment=TA_LEFT, spaceAfter=3)
    bullet_s = style("BU", fontName=F, fontSize=BODY_PT, leading=BODY_PT + 3.3, spaceAfter=2,
                     leftIndent=BULLET_TEXT_IN * inch, bulletIndent=BULLET_INDENT_IN * inch,
                     bulletFontName=F, bulletFontSize=BODY_PT)

    def rl(text: str) -> str:
        out = []
        for seg, b in _split_bold(text):
            seg = escape(seg)
            out.append(f"<b>{seg}</b>" if b else seg)
        return "".join(out)

    page_w = A4[0]
    margin_x = MARGIN_SIDE_IN * inch
    content_w = page_w - 2 * margin_x

    story = [Paragraph(rl(name), name_s)]

    contact = _contact_parts(profile)
    if contact:
        bits = []
        for label, text, href in contact:
            if href:
                bits.append(f'{escape(label)}<link href="{escape(href, {chr(34): "&quot;"})}" color="#0563C1">'
                            f'<u>{escape(text)}</u></link>')
            else:
                bits.append(escape(label + text))
        story.append(Paragraph(" | ".join(bits), contact_s))

    for b in blocks:
        kind = b["kind"]
        if kind in ("h1", "h2"):
            story.append(KeepTogether([
                Paragraph(rl(b["text"].upper()), h2_s),
                HRFlowable(width="100%", thickness=0.75, color=black, spaceBefore=1, spaceAfter=3),
            ]))
        elif kind == "entry":
            story.append(Paragraph(rl(b["text"]), entry_s))
        elif kind == "bullets":
            for it in b["items"]:
                story.append(Paragraph(rl(it), bullet_s, bulletText="•"))
        elif kind == "kvs":
            col = max(stringWidth(label, FB, BODY_PT) for label, _ in b["items"]) + 8
            rows = [[Paragraph(f"<b>{escape(label)}</b>", body_s), Paragraph(rl(value), body_s)]
                    for label, value in b["items"]]
            tbl = Table(rows, colWidths=[col, content_w - col])
            tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(tbl)
        else:
            story.append(Paragraph(rl(b["text"]), body_s))

    page_w, page_h = A4
    top, bottom = MARGIN_TOP_IN * inch, MARGIN_BOTTOM_IN * inch
    frame = Frame(margin_x, bottom, content_w, page_h - top - bottom,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=A4, title=f"{name} - CV", author=name,
                          pageTemplates=[PageTemplate(id="cv", frames=[frame])])
    doc.build(story)
    return buf.getvalue()
