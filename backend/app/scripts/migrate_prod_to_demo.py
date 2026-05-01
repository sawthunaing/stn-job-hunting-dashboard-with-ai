"""Migrate REAL production data into the public DEMO database, sanitised.

Workflow:
  Production DB (your private app)
    │  read-only export
    ▼
  In-memory data shaping:
    - Anonymise company names (mapping below)
    - Wipe job.notes
    - Wipe profile.email, phone, target_salary, deal_breakers, private_notes
    - Replace contact info with public-safe demo values
    - Reset job IDs (so demo always starts at 1)
  ▼
  Demo DB (public-facing) wipe + insert
  ▼
  Top-up with 2-3 obviously-fake jobs (Acme, Globex etc) for showcase variety

Run on EC2:
  cd ~/trajectory
  sudo docker compose -p trajectory-demo -f docker-compose.demo.yml \
    exec api python -m app.scripts.migrate_prod_to_demo

The script reads the PROD DB by connecting from the demo container to the
prod-network db. To make this work, we need the demo api container to be
attached to the prod compose network for the duration of this migration.
The runner script handles that - see SETUP_DEMO.md for details.

If something breaks mid-run, re-running is safe: it wipes + restarts.
"""
from __future__ import annotations
import os
import sys
import re
from datetime import datetime
from pathlib import Path

# Make `app.` importable when running as -m
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.attributes import flag_modified

from app import models
from app.db import SessionLocal as DemoSession, init_db


# ---------------------------------------------------------------------------
# CONFIGURATION - edit if needed before running
# ---------------------------------------------------------------------------

# DSN of the PRODUCTION database. Resolved via Docker network bridging
# (the demo api container is attached to the prod network for this script).
# The db hostname in the prod compose is "db" (default), and the prod compose
# project name is "trajectory" so the actual container name is "trajectory-db".
# We try both hostnames so the script works whether you bridge networks or
# expose the prod db on the host.
PROD_DB_CANDIDATES = [
    os.environ.get("PROD_DATABASE_URL"),
    "postgresql+psycopg://trajectory:" + os.environ.get("PROD_DB_PASSWORD", "trajectory") + "@trajectory-db:5432/trajectory",
    "postgresql+psycopg://trajectory:" + os.environ.get("PROD_DB_PASSWORD", "trajectory") + "@db:5432/trajectory",
]

# Anonymisation map - real → public-safe display name.
# Edit this to control how YOUR specific applied-to companies show up in the demo.
COMPANY_ANONYMISATION = {
    # FinTech / banks
    "goldman sachs": "Major Investment Bank",
    "jpmorgan": "Major Investment Bank",
    "morgan stanley": "Major Investment Bank",
    "barclays": "Major UK Bank",
    "hsbc": "Major UK Bank",
    "natwest": "Major UK Bank",
    "lloyds": "Major UK Bank",
    "stripe": "Global FinTech",
    "revolut": "Challenger Bank",
    "monzo": "Challenger Bank",
    "starling": "Challenger Bank",
    "wise": "Cross-border Payments",
    "checkout.com": "Payments Platform",
    "adyen": "Payments Platform",
    # Big tech
    "google": "Big Tech",
    "amazon": "Big Tech",
    "meta": "Big Tech",
    "facebook": "Big Tech",
    "microsoft": "Big Tech",
    "apple": "Big Tech",
    "netflix": "Streaming Platform",
    # Synergy is your current employer - more careful here
    "synergy logic": "Tech Consultancy",
}

# Fake "filler" companies for jobs whose company isn't in the map.
# Cycled by hash(company) so the same real company always maps to the same fake.
FILLER_COMPANIES = [
    "Atlas Software",
    "Beacon Technologies",
    "Crescent Digital",
    "Delta Systems",
    "Echo Labs",
    "Falcon Tech",
    "Granite Engineering",
    "Helios Platform",
    "Iridium Software",
    "Junction Technologies",
]

# A few obviously-fake bonus jobs to mix in (showcases score-band variety).
# These are added on TOP of the migrated real ones.
BONUS_FAKE_JOBS = [
    {
        "company": "Acme Corp",
        "role": "Senior Backend Engineer (.NET / FinTech)",
        "location": "London, UK",
        "work_type": "Hybrid",
        "platform": "LinkedIn",
        "currency": "GBP",
        "salary_min": 90,
        "salary_max": 110,
        "status": "Applied",
        "starred": True,
        "description": (
            "Acme Corp is hiring a Senior Backend Engineer for our payments "
            "platform team. Build .NET 8 microservices on AWS, integrate with "
            "VISA and Mastercard, optimise SQL Server for high throughput. "
            "7+ years C#/.NET, strong AWS, payment systems experience required."
        ),
    },
    {
        "company": "Globex Inc",
        "role": "Lead Backend Engineer (Java / Spring Boot)",
        "location": "Remote (UK)",
        "work_type": "Remote",
        "platform": "Otta",
        "currency": "GBP",
        "salary_min": 95,
        "salary_max": 120,
        "status": "Interviewing",
        "starred": True,
        "description": (
            "B2B SaaS hiring a Lead Backend Engineer. Java/Spring Boot on "
            "Kubernetes, lead 4 engineers, set technical direction. 8+ years "
            "backend, strong Java background, K8s experience required."
        ),
    },
]

# Public-safe profile values (replaces real contact info)
DEMO_SAFE_PROFILE_OVERRIDES = {
    "email": "demo@example.com",
    "phone": "+44 ... (private)",
    "target_salary": "",       # wiped
    "deal_breakers": "",       # wiped
    "private_notes": "",       # wiped
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def anonymise_company(real_name: str) -> str:
    """Map real company name → public-safe display name."""
    if not real_name:
        return "Unknown Company"
    key = real_name.lower().strip()
    # Direct map hit
    if key in COMPANY_ANONYMISATION:
        return COMPANY_ANONYMISATION[key]
    # Partial match (e.g. "Goldman Sachs International" matches "goldman sachs")
    for known_key, mapped in COMPANY_ANONYMISATION.items():
        if known_key in key:
            return mapped
    # Fallback - deterministic filler so the same real company always maps the same way
    return FILLER_COMPANIES[hash(key) % len(FILLER_COMPANIES)]


def scrub_text(text_val: str | None) -> str | None:
    """Strip company-revealing strings from free-text fields (description, AI output).
    Best-effort - we replace any known mapped company with its anonymised version.
    """
    if not text_val:
        return text_val
    out = text_val
    for known_key, mapped in COMPANY_ANONYMISATION.items():
        # Case-insensitive whole-word-ish replacement
        pattern = re.compile(re.escape(known_key), re.IGNORECASE)
        out = pattern.sub(mapped, out)
    return out


def find_prod_engine():
    """Try the candidate DSNs and return the first one that connects."""
    last_err = None
    for dsn in PROD_DB_CANDIDATES:
        if not dsn:
            continue
        try:
            engine = create_engine(dsn)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[migrate]   Connected to PROD via: {dsn.split('@')[-1]}")
            return engine
        except Exception as e:
            last_err = e
            print(f"[migrate]   Tried {dsn.split('@')[-1]}: {type(e).__name__}")
    raise RuntimeError(
        f"Could not connect to PROD DB via any candidate. Last error: {last_err}\n"
        f"Set PROD_DATABASE_URL env var or PROD_DB_PASSWORD."
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def migrate():
    print("[migrate] Starting prod → demo migration")
    print("[migrate] Step 1: connect to PROD DB...")
    prod_engine = find_prod_engine()
    ProdSession = sessionmaker(bind=prod_engine)

    # Read PROD data
    with ProdSession() as prod_db:
        prod_jobs = prod_db.query(models.Job).order_by(models.Job.id).all()
        prod_profile = prod_db.query(models.Profile).first()
        print(f"[migrate]   Found {len(prod_jobs)} jobs in PROD")
        if prod_profile:
            print(f"[migrate]   Found profile: {prod_profile.full_name}")

        # Snapshot data we need (so we can use it after closing the prod session)
        prod_jobs_data = []
        for j in prod_jobs:
            prod_jobs_data.append({
                "company": j.company,
                "role": j.role,
                "location": j.location,
                "work_type": j.work_type,
                "platform": j.platform,
                "source_url": j.source_url,
                "description": j.description,
                "salary_min": j.salary_min,
                "salary_max": j.salary_max,
                "currency": j.currency,
                "status": j.status,
                "notes": j.notes,  # will be wiped
                "starred": j.starred,
                "applied_date": j.applied_date,
                "suitability": j.suitability,
                "analysis": j.analysis,
                "interview_prep": j.interview_prep,
                "company_research": j.company_research,
                "tailored_docs": j.tailored_docs,
                "created_at": j.created_at,
                "updated_at": j.updated_at,
                "analyzed_at": j.analyzed_at,
            })

        prod_profile_data = None
        if prod_profile:
            prod_profile_data = {
                "full_name": prod_profile.full_name,
                "headline": prod_profile.headline,
                "location": prod_profile.location,
                "email": prod_profile.email,
                "phone": prod_profile.phone,
                "website": prod_profile.website,
                "linkedin": prod_profile.linkedin,
                "github": prod_profile.github,
                "hackerrank": prod_profile.hackerrank,
                "title": prod_profile.title,
                "summary": prod_profile.summary,
                "experience": prod_profile.experience,
                "skills": prod_profile.skills,
                "education": prod_profile.education,
                "achievements": prod_profile.achievements,
                "target_roles": prod_profile.target_roles,
                "target_salary": prod_profile.target_salary,
                "deal_breakers": prod_profile.deal_breakers,
                "private_notes": prod_profile.private_notes,
            }

    # Step 2: wipe demo DB and write sanitised data
    print("\n[migrate] Step 2: writing to DEMO DB...")
    init_db()  # ensure schema exists
    with DemoSession() as demo_db:
        # Wipe existing
        demo_db.execute(text("TRUNCATE TABLE jobs RESTART IDENTITY CASCADE"))
        demo_db.execute(text("DELETE FROM profile"))
        demo_db.commit()

        # Write profile (sanitised)
        if prod_profile_data:
            sanitised = dict(prod_profile_data)
            sanitised.update(DEMO_SAFE_PROFILE_OVERRIDES)
            demo_profile = models.Profile(id=1, **sanitised)
            demo_db.add(demo_profile)
            demo_db.commit()
            print(f"[migrate]   Profile inserted (email/phone/targets/notes wiped)")

        # Write jobs (sanitised + anonymised)
        anon_count = 0
        kept_count = 0
        for jd in prod_jobs_data:
            real_company = jd["company"]
            anon_company = anonymise_company(real_company)
            if anon_company != real_company:
                anon_count += 1
            else:
                kept_count += 1

            # Build sanitised payload
            sanitised_job = {
                "company": anon_company,
                "role": jd["role"],
                "location": jd["location"],
                "work_type": jd["work_type"],
                "platform": jd["platform"],
                "source_url": None,                          # wipe - leaks platform/recruiter
                "description": scrub_text(jd["description"]),  # scrub company mentions
                "salary_min": jd["salary_min"],
                "salary_max": jd["salary_max"],
                "currency": jd["currency"],
                "status": jd["status"],
                "notes": None,                               # wipe entirely
                "starred": jd["starred"],
                "applied_date": jd["applied_date"],
                "suitability": jd["suitability"],
                "analysis": jd["analysis"],                  # AI analysis - kept
                "interview_prep": jd["interview_prep"],
                "company_research": None,                    # wipe - might contain real co name
                "tailored_docs": jd["tailored_docs"],
                "created_at": jd["created_at"],
                "updated_at": jd["updated_at"],
                "analyzed_at": jd["analyzed_at"],
            }
            demo_db.add(models.Job(**sanitised_job))
        demo_db.commit()
        print(f"[migrate]   Migrated {len(prod_jobs_data)} real jobs")
        print(f"[migrate]   ({anon_count} companies anonymised, {kept_count} fell to filler names)")

        # Step 3: top up with bonus fake jobs
        print(f"\n[migrate] Step 3: adding {len(BONUS_FAKE_JOBS)} bonus fake jobs...")
        for bj in BONUS_FAKE_JOBS:
            demo_db.add(models.Job(**bj))
        demo_db.commit()

        # Summary
        total = demo_db.query(models.Job).count()
        analyzed = demo_db.query(models.Job).filter(models.Job.suitability.isnot(None)).count()
        print(f"\n[migrate] Done.")
        print(f"[migrate]   Demo DB total jobs: {total}")
        print(f"[migrate]   With AI scores: {analyzed}")
        print(f"[migrate]   Without scores (bonus fake jobs may need analysis): {total - analyzed}")
        print(f"\nNext: visit http://51.24.16.185:3001 to verify.")
        print(f"Optional: re-run AI on bonus jobs by visiting them in the demo... ")
        print(f"    actually you can't (demo mode = read-only). Run seed_demo.py to ")
        print(f"    re-seed if you want bonus jobs analysed.")


if __name__ == "__main__":
    migrate()
