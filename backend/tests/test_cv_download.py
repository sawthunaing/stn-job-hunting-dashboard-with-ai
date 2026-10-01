from app import models
from app.db import SessionLocal


def _job_with_cv(content="## Professional Summary\nBuilder of things.\n\n## Professional Experience\n### Engineer • Acme, London @@ 2020 - Present\n- Did **great** things"):
    with SessionLocal() as db:
        job = models.Job(company="Acme Ltd.", role="Engineer", tailored_docs={"cv": {"content": content}} if content else None)
        db.add(job)
        db.commit()
        return job.id


def test_download_pdf_and_docx(client):
    jid = _job_with_cv()
    pdf = client.get(f"/jobs/{jid}/cv?format=pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    assert 'filename="CV_Acme_Ltd.pdf"' in pdf.headers["content-disposition"]
    docx = client.get(f"/jobs/{jid}/cv?format=docx")
    assert docx.status_code == 200 and docx.content.startswith(b"PK")


def test_download_errors(client):
    assert client.get("/jobs/999999/cv").status_code == 404
    assert client.get(f"/jobs/{_job_with_cv(content=None)}/cv").status_code == 400
    assert client.get(f"/jobs/{_job_with_cv()}/cv?format=txt").status_code == 400
