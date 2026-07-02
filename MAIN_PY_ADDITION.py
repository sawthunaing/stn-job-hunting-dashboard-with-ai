# =============================================================================
# ADD THIS TO backend/app/main.py
# =============================================================================

# 1. At the top with the other imports, add:
#
#       import io
#       from fastapi.responses import StreamingResponse
#       from . import cv_export
#
#    (you already import `models, schemas, ai, scraper, auth` - just add the
#     three lines above; `cv_export` is the new module.)


# 2. Add this endpoint anywhere among the AI routes (e.g. right after the
#    `tailor` endpoint):

@app.get("/jobs/{job_id}/cv/download")
def download_cv(
    job_id: int,
    format: str = "pdf",
    db: Session = Depends(get_db),
    _: str = Depends(auth.require_read),
):
    """Download the AI-tailored CV for a job as a styled .docx or .pdf.

    The tailored CV must have been generated first (POST /jobs/{id}/tailor
    with doc_type="cv"). The body markdown is rendered with a header built
    from the user's profile so the output matches the master CV layout.
    """
    job = db.get(models.Job, job_id)
    if not job:
        raise HTTPException(404, "not found")

    docs = job.tailored_docs or {}
    cv = docs.get("cv")
    if not cv or not cv.get("content"):
        raise HTTPException(400, "No tailored CV has been generated for this job yet")

    profile = db.get(models.Profile, 1)
    content_md = cv["content"]

    # Safe filename from company name
    safe_company = "".join(
        c for c in (job.company or "company") if c.isalnum() or c in " -_"
    ).strip().replace(" ", "_") or "company"
    base = f"CV_{safe_company}"

    fmt = (format or "pdf").lower()
    if fmt == "docx":
        data = cv_export.build_docx(profile, content_md)
        media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"{base}.docx"
    elif fmt == "pdf":
        data = cv_export.build_pdf(profile, content_md)
        media = "application/pdf"
        filename = f"{base}.pdf"
    else:
        raise HTTPException(400, "format must be 'docx' or 'pdf'")

    return StreamingResponse(
        io.BytesIO(data),
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
