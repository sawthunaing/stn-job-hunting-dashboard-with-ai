"""FastAPI application."""
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from . import models, schemas, ai, scraper, auth, cv_renderer
from .config import settings
from .db import get_db, init_db


app = FastAPI(title="Ko Saw's Job Hunting Dashboard API", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin] if settings.cors_origin != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


# =================== AUTH ===================

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    expires_in_hours: int


@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    if not auth.authenticate(payload.username, payload.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    token = auth.issue_token(payload.username)
    return LoginResponse(token=token, username=payload.username, expires_in_hours=settings.jwt_ttl_hours)


@app.get("/auth/me")
def me(username: str = Depends(auth.require_auth)):
    return {"username": username}


@app.get("/health")
def health():
    return {"ok": True, "ts": datetime.utcnow().isoformat()}


# =================== PROFILE ===================

@app.get("/profile", response_model=schemas.ProfileSchema)
def get_profile(db: Session = Depends(get_db), _: str = Depends(auth.require_auth)):
    p = db.get(models.Profile, 1)
    if p is None:
        return schemas.ProfileSchema()
    return p


@app.put("/profile", response_model=schemas.ProfileSchema)
def upsert_profile(
    payload: schemas.ProfileSchema,
    db: Session = Depends(get_db),
    _: str = Depends(auth.require_auth),
):
    p = db.get(models.Profile, 1)
    data = payload.model_dump(exclude={"updated_at"}, exclude_unset=False)
    if p is None:
        p = models.Profile(id=1, **data)
        db.add(p)
    else:
        for k, v in data.items():
            setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


# =================== JOBS ===================

@app.get("/jobs", response_model=list[schemas.JobListItem])
def list_jobs(
    status_filter: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    _: str = Depends(auth.require_auth),
):
    query = db.query(models.Job)
    if status_filter and status_filter != "All":
        query = query.filter(models.Job.status == status_filter)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (models.Job.company.ilike(like)) | (models.Job.role.ilike(like))
        )
    return query.order_by(desc(models.Job.created_at)).all()


@app.get("/jobs/{job_id}", response_model=schemas.JobDetail)
def get_job(job_id: int, db: Session = Depends(get_db), _: str = Depends(auth.require_auth)):
    job = db.get(models.Job, job_id)
    if not job:
        raise HTTPException(404, "not found")
    return job


@app.post("/jobs", response_model=schemas.JobDetail, status_code=201)
def create_job(
    payload: schemas.JobCreate,
    db: Session = Depends(get_db),
    _: str = Depends(auth.require_auth),
):
    job = models.Job(**payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@app.post("/jobs/from-url", response_model=schemas.JobDetail, status_code=201)
async def create_from_url(
    payload: schemas.JobFromUrl,
    db: Session = Depends(get_db),
    _: str = Depends(auth.require_auth),
):
    try:
        page_text = await scraper.fetch_page(payload.url)
    except Exception as e:
        raise HTTPException(400, f"fetch failed: {e}")

    extracted = ai.extract_job_from_html(page_text, payload.url)

    job = models.Job(
        company=extracted.get("company") or "Unknown",
        role=extracted.get("role") or "Unknown",
        location=extracted.get("location"),
        work_type=extracted.get("work_type"),
        platform=_infer_platform(payload.url),
        source_url=payload.url,
        description=extracted.get("description"),
        salary_min=extracted.get("salary_min"),
        salary_max=extracted.get("salary_max"),
        currency=extracted.get("currency") or "GBP",
        status="New",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@app.patch("/jobs/{job_id}", response_model=schemas.JobDetail)
def update_job(
    job_id: int,
    payload: schemas.JobUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(auth.require_auth),
):
    job = db.get(models.Job, job_id)
    if not job:
        raise HTTPException(404, "not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(job, k, v)
    db.commit()
    db.refresh(job)
    return job


@app.delete("/jobs/{job_id}", status_code=204)
def delete_job(job_id: int, db: Session = Depends(get_db), _: str = Depends(auth.require_auth)):
    job = db.get(models.Job, job_id)
    if not job:
        raise HTTPException(404, "not found")
    db.delete(job)
    db.commit()


# =================== AI ROUTES ===================

@app.post("/jobs/{job_id}/analyze", response_model=schemas.JobDetail)
def analyze(job_id: int, db: Session = Depends(get_db), _: str = Depends(auth.require_auth)):
    job = db.get(models.Job, job_id)
    if not job:
        raise HTTPException(404, "not found")
    if not job.description:
        raise HTTPException(400, "job has no description to analyze")

    result = ai.analyze_job(db, job.description, job.role, job.company, job.location)
    job.suitability = result.get("suitability")
    job.analysis = result
    job.analyzed_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job


@app.post("/jobs/{job_id}/prep", response_model=schemas.JobDetail)
def prep(job_id: int, db: Session = Depends(get_db), _: str = Depends(auth.require_auth)):
    job = db.get(models.Job, job_id)
    if not job:
        raise HTTPException(404, "not found")
    if not job.description:
        raise HTTPException(400, "job has no description")
    job.interview_prep = ai.generate_prep(db, job.description, job.role, job.company)
    db.commit()
    db.refresh(job)
    return job


@app.post("/jobs/{job_id}/research", response_model=schemas.JobDetail)
def research(job_id: int, db: Session = Depends(get_db), _: str = Depends(auth.require_auth)):
    job = db.get(models.Job, job_id)
    if not job:
        raise HTTPException(404, "not found")
    job.company_research = ai.research_company(db, job.company, job.role)
    db.commit()
    db.refresh(job)
    return job


@app.post("/jobs/{job_id}/tailor", response_model=schemas.JobDetail)
def tailor(
    job_id: int,
    payload: schemas.TailorRequest,
    db: Session = Depends(get_db),
    _: str = Depends(auth.require_auth),
):
    job = db.get(models.Job, job_id)
    if not job:
        raise HTTPException(404, "not found")
    if not job.description:
        raise HTTPException(400, "job has no description")

    result = ai.tailor_doc(db, job.description, job.role, job.company, payload.doc_type)
    docs = dict(job.tailored_docs or {})
    docs[payload.doc_type] = result
    job.tailored_docs = docs
    db.commit()
    db.refresh(job)
    return job


@app.get("/jobs/{job_id}/cv")
def download_cv(
    job_id: int,
    format: str = "pdf",
    db: Session = Depends(get_db),
    _: str = Depends(auth.require_auth),
):
    """Download the AI-tailored CV as PDF or DOCX.

    The user must have generated a tailored CV first (via POST /jobs/{id}/tailor
    with doc_type='cv'). Identity (name, contact) is read from the Profile
    table; body content comes from the saved AI markdown.
    """
    fmt = format.lower().strip()
    if fmt not in ("pdf", "docx"):
        raise HTTPException(400, "format must be 'pdf' or 'docx'")

    job = db.get(models.Job, job_id)
    if not job:
        raise HTTPException(404, "job not found")

    docs = job.tailored_docs or {}
    cv_doc = docs.get("cv") if isinstance(docs, dict) else None
    if not cv_doc or not cv_doc.get("content"):
        raise HTTPException(
            400,
            "Tailored CV not generated yet. Click 'Generate' on the Tailored CV tab first."
        )

    profile = db.get(models.Profile, 1)
    md = cv_doc["content"]

    if fmt == "pdf":
        binary = cv_renderer.render_pdf(profile, md)
        media_type = "application/pdf"
    else:
        binary = cv_renderer.render_docx(profile, md)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    filename = cv_renderer.build_filename(profile, job.company, job.role, fmt)
    return Response(
        content=binary,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _infer_platform(url: str) -> str:
    u = url.lower()
    if "linkedin" in u: return "LinkedIn"
    if "greenhouse" in u: return "Greenhouse"
    if "lever.co" in u: return "Lever"
    if "ashbyhq" in u: return "Ashby"
    if "indeed" in u: return "Indeed"
    if "workable" in u: return "Workable"
    return "Direct"
