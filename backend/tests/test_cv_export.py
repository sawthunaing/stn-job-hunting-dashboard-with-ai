import io
import zipfile
from types import SimpleNamespace as NS

from docx import Document

from app import cv_export

PROFILE = NS(full_name="Jane Doe", email="jane@example.com", phone="+44 7000 000000",
             linkedin="linkedin.com/in/jane", github=None, website=None, location="London, UK")

MD = """## Summary
**Backend Engineer** who ships.

## Work Experience
### Engineer | Acme | 2020 – Present | London, UK
- Did **great** things

## Skills, Languages, Professional Memberships, & Certificates
**Certifications:** AWS SAA
**Skills:** Python, Go
"""


def test_parse_entries_and_label_rows():
    kinds = [b["kind"] for b in cv_export._parse_blocks(MD)]
    assert kinds == ["h2", "para", "h2", "entry", "bullets", "h2", "kvs"]
    kvs = cv_export._parse_blocks(MD)[-1]["items"]
    assert kvs == [("Certifications:", "AWS SAA"), ("Skills:", "Python, Go")]


def test_legacy_at_at_separator_becomes_pipe():
    entry = cv_export._parse_blocks("### Dev • Acme @@ 2020 - Present")[0]
    assert entry["text"] == "Dev • Acme | 2020 - Present"


def test_docx_has_clickable_contact_links_and_sections():
    doc = Document(io.BytesIO(cv_export.build_docx(PROFILE, MD)))
    texts = [p.text for p in doc.paragraphs]
    assert texts[0] == "Jane Doe"
    assert "SUMMARY" in texts and "WORK EXPERIENCE" in texts
    with zipfile.ZipFile(io.BytesIO(cv_export.build_docx(PROFILE, MD))) as z:
        rels = z.read("word/_rels/document.xml.rels").decode()
    assert "mailto:jane@example.com" in rels and "https://linkedin.com/in/jane" in rels


def test_pdf_builds_and_embeds_bundled_font():
    pdf = cv_export.build_pdf(PROFILE, MD)
    assert pdf.startswith(b"%PDF") and b"Lora" in pdf
