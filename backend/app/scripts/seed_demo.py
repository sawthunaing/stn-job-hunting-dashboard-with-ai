"""Seed the demo Postgres with curated jobs + pre-computed AI analyses.

Usage on EC2 (after demo stack is up):
    cd ~/trajectory
    sudo docker compose -p trajectory-demo -f docker-compose.demo.yml exec api python -m app.scripts.seed_demo

What it does:
1. Truncates the jobs and tailored_docs (everything except profile)
2. Inserts/updates the Profile row with Saw's real CV info (no private notes)
3. Inserts 6 curated jobs (mix of real-style + obviously-fake)
4. For each job, calls the AI to produce: analysis, prep guide, tailored CV
5. Saves all results to the DB

Cost: ~$2-3 of OpenAI usage one-time.

If something breaks mid-run, re-running is safe - it wipes and starts over.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

# Allow running as a module: python -m app.scripts.seed_demo
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy.orm import Session
from sqlalchemy import text

from app import models, ai
from app.db import SessionLocal, init_db


# ---------------------------------------------------------------------------
# Profile - based on Saw Thu Naing's actual CV (public-safe, no private notes)
# ---------------------------------------------------------------------------
PROFILE_DATA = {
    "full_name": "Saw Thu Naing",
    "headline": "Senior Software Engineer · 10+ years FinTech / Distributed Systems",
    "email": "demo@example.com",  # NOT real - this is a public demo
    "phone": "+44 ...",
    "location": "London, UK",
    "linkedin": "https://www.linkedin.com/in/saw-thu-naing/",
    "github": "https://github.com/sawthunaing",
    "website": "",
    "about": (
        "Senior Software Engineer with 10+ years of experience designing, "
        "developing, and maintaining secure, high-scale systems across FinTech, "
        "payments, banking, government workflows, and streaming platforms. "
        "Deep expertise in C#, ASP.NET, .NET Core / .NET 8, RESTful APIs, "
        "microservices, distributed systems, and Microsoft SQL Server "
        "performance optimisation."
    ),
    "skills_text": (
        "C#, ASP.NET, .NET Core, .NET 6/8, Java, Spring Boot, Angular, "
        "JavaScript, TypeScript, MSSQL, MySQL, PostgreSQL, Redis, MongoDB, "
        "AWS (ECS, Lambda, RDS, S3, ECR, SNS, SQS, Secrets Manager), Azure, "
        "GCP, Docker, Kubernetes, GitHub Actions, CI/CD, Microservices, "
        "API Gateway, Distributed Systems, Payment Gateways, EMV QR, "
        "VISA/Mastercard integration, Digital Wallets, Core Banking"
    ),
    "experience_text": (
        "**Software Engineer** — Synergy Logic, London / Remote (Sept 2025 – Present)\n"
        "- RESTful APIs in .NET 8 integrating SQL Server, Redis, AWS services for SaaS\n"
        "- Reduced payment microservice errors by ~30%\n"
        "\n"
        "**Senior Developer** — Shwe Digit, Myanmar / Remote (May 2021 – Aug 2025)\n"
        "- Customs Department APIs in .NET Framework 4.6 MVC and SQL Server\n"
        "- Built configurable JSON-driven API simulator using .NET 6/8\n"
        "\n"
        "**Technical Lead — FinTech** — Abank, Myanmar (Jun 2021 – Aug 2023)\n"
        "- Custom API Gateway with Ocelot on .NET Core 7 + PostgreSQL + Nginx\n"
        "- Dynamic Bill Payment platform using SOA architecture\n"
        "- Cross-border remittance integration with Dee Money\n"
        "\n"
        "**Senior Backend Engineer** — Codigo Mobile (Spotv), Singapore / Remote (Dec 2023 – Dec 2024)\n"
        "- Live sports streaming platform for 5 countries on .NET Core 6 + Docker + AWS ECS\n"
        "- Centralised data migration cutting costs by ~40%\n"
        "\n"
        "**Technical Lead — FinTech** — uab bank, Myanmar (May 2020 – Apr 2021)\n"
        "- uabpay payment gateway end-to-end\n"
        "\n"
        "**Senior Software Engineer — FinTech** — ACE Data System Co Ltd, Myanmar (Sep 2017 – Apr 2021)\n"
        "- Led OnePay wallet system for Asia Green Development Bank\n"
        "- Internet Banking for Ayeyarwaddy Farmers Development Bank"
    ),
    "education_text": (
        "**BSc (Hons) Business IT** — University of Greenwich, London, UK (Oct 2013 – Mar 2015)\n"
        "**BA English** — Dagon University, Myanmar (Mar 2009 – Mar 2012)"
    ),
    "certifications_text": (
        "- **Google Professional Cloud Architect**\n"
        "- **AWS Certified Solutions Architect — Associate**\n"
        "- Atlassian Jira Fundamentals certificate"
    ),
    "target_titles": "Senior Software Engineer, Lead Engineer, Staff Engineer, Backend Engineer, Software Architect",
    "target_locations": "London, UK · Remote (UK)",
    "min_salary_gbp": 80000,
    "ideal_salary_gbp": 100000,
    "deal_breakers": "",  # Public-safe, omit private notes
    "preferred_industries": "FinTech, payments, banking, distributed systems, B2B SaaS",
    "work_auth_status": "Full UK right to work",
}


# ---------------------------------------------------------------------------
# Demo jobs — mix of real-style positions and obviously fake exemplars.
# These are crafted to showcase different score bands (some excellent, some
# borderline, some low) so the AI's analysis looks discriminating.
# ---------------------------------------------------------------------------
DEMO_JOBS = [
    {
        # OBVIOUSLY FAKE - Acme Corp — high score, .NET FinTech (perfect fit)
        "company": "Acme Corp",
        "role": "Senior Backend Engineer (.NET / FinTech)",
        "location": "London, UK",
        "work_type": "Hybrid (3 days/week)",
        "platform": "LinkedIn",
        "source_url": "https://example.com/jobs/acme-senior-backend",
        "currency": "GBP",
        "salary_min": 90,
        "salary_max": 110,
        "status": "Applied",
        "starred": True,
        "description": (
            "Acme Corp is hiring a Senior Backend Engineer to join our payments "
            "platform team in London. We are building the next generation of our "
            "high-throughput payment gateway processing >1M transactions per day.\n\n"
            "**You will:**\n"
            "- Design and build RESTful microservices in C# / .NET 8 hosted on AWS\n"
            "- Optimise SQL Server queries for high-volume transactional workloads\n"
            "- Integrate with VISA and Mastercard card schemes\n"
            "- Mentor junior engineers and lead architectural decisions\n"
            "- Work with Redis, SQS, S3, ECR, Secrets Manager\n\n"
            "**You have:**\n"
            "- 7+ years C# / .NET experience\n"
            "- Strong SQL Server skills, query optimisation\n"
            "- Production AWS experience (ECS, Lambda, RDS)\n"
            "- Experience with payment systems or card scheme integration (VISA, Mastercard)\n"
            "- Microservices and distributed systems background\n"
            "- Strong written communication\n\n"
            "**Nice to have:** Experience with Ocelot API Gateway, EMV QR, digital wallets.\n\n"
            "Salary £90k-£110k + bonus + benefits. London hybrid (3 days in office near Liverpool Street)."
        ),
    },
    {
        # OBVIOUSLY FAKE - Globex — medium-high score, Java/Spring (partial fit)
        "company": "Globex Inc",
        "role": "Lead Backend Engineer (Java / Spring Boot)",
        "location": "Remote (UK)",
        "work_type": "Remote",
        "platform": "Otta",
        "source_url": "https://example.com/jobs/globex-lead-backend",
        "currency": "GBP",
        "salary_min": 95,
        "salary_max": 120,
        "status": "Interviewing",
        "starred": True,
        "description": (
            "Globex is a B2B SaaS company hiring a Lead Backend Engineer for our "
            "core platform team. Fully remote, UK-based.\n\n"
            "**You will:**\n"
            "- Architect Java / Spring Boot microservices on Kubernetes\n"
            "- Lead a team of 4 engineers, set technical direction\n"
            "- Drive code quality and engineering standards\n"
            "- Work with PostgreSQL, Kafka, Redis\n"
            "- Deploy on AWS EKS\n\n"
            "**You have:**\n"
            "- 8+ years backend engineering, lead/architect experience\n"
            "- Strong Java / Spring Boot background\n"
            "- Production Kubernetes operating experience\n"
            "- Experience leading engineering teams\n"
            "- Polyglot mindset welcome (you'll work alongside Go and Rust services)\n\n"
            "Salary £95k-£120k + RSUs. Fully remote within UK."
        ),
    },
    {
        # OBVIOUSLY FAKE - Stark Industries — low score, frontend-heavy (mismatch)
        "company": "Stark Industries",
        "role": "Senior Frontend Engineer (React)",
        "location": "London, UK",
        "work_type": "On-site",
        "platform": "Indeed",
        "source_url": "https://example.com/jobs/stark-senior-frontend",
        "currency": "GBP",
        "salary_min": 70,
        "salary_max": 85,
        "status": "Rejected",
        "starred": False,
        "description": (
            "Stark Industries is hiring a Senior Frontend Engineer to lead our "
            "consumer-facing web applications.\n\n"
            "**You will:**\n"
            "- Build pixel-perfect UI in React / Next.js / TypeScript\n"
            "- Own design system and component library\n"
            "- Work closely with product designers in Figma\n"
            "- Lead accessibility and performance initiatives\n"
            "- Mentor frontend engineers\n\n"
            "**You have:**\n"
            "- 6+ years React / TypeScript experience\n"
            "- Strong CSS, Tailwind, design system experience\n"
            "- Performance profiling and optimisation experience\n"
            "- WCAG / accessibility expertise\n"
            "- Figma fluency\n\n"
            "On-site 5 days/week in central London. Salary £70k-£85k."
        ),
    },
    {
        # SOFT-FAKE — sounds like a real FinTech, generic name
        "company": "Northbank Digital",
        "role": "Staff Software Engineer (Payments Platform)",
        "location": "London, UK",
        "work_type": "Hybrid (2 days/week)",
        "platform": "Company website",
        "source_url": "https://example.com/jobs/northbank-staff-engineer",
        "currency": "GBP",
        "salary_min": 110,
        "salary_max": 140,
        "status": "Applied",
        "starred": True,
        "description": (
            "Northbank Digital is the digital banking arm of Northbank Group. We're "
            "hiring a Staff Software Engineer to architect our next-generation payments "
            "platform.\n\n"
            "**You will:**\n"
            "- Set technical direction for the payments platform (Open Banking, SEPA, BACS)\n"
            "- Lead architecture across 30+ microservices in .NET 8 and Go\n"
            "- Drive engineering excellence: testing, observability, deployment\n"
            "- Mentor 6 senior engineers across the platform team\n"
            "- Work across AWS, Kubernetes, Kafka, Postgres, Redis\n"
            "- Collaborate with product, risk, compliance, and operations leaders\n\n"
            "**You have:**\n"
            "- 10+ years software engineering experience\n"
            "- Deep .NET / C# background, polyglot welcome\n"
            "- Production payments / banking systems experience\n"
            "- Strong system design and architecture skills\n"
            "- Track record leading engineers and shipping at scale\n"
            "- AWS (ECS, EKS, Lambda, RDS), Kafka, Redis\n\n"
            "**Nice to have:** Open Banking experience, knowledge of UK regulatory landscape, "
            "VISA/Mastercard integrations.\n\n"
            "Salary £110k-£140k + 25% bonus + RSUs + benefits. Hybrid 2 days/week in London."
        ),
    },
    {
        # SOFT-FAKE — start-up FinTech
        "company": "Helix Pay",
        "role": "Senior Backend Engineer (FinTech, .NET)",
        "location": "London, UK",
        "work_type": "Hybrid",
        "platform": "AngelList",
        "source_url": "https://example.com/jobs/helix-pay-senior",
        "currency": "GBP",
        "salary_min": 85,
        "salary_max": 105,
        "status": "New",
        "starred": False,
        "description": (
            "Helix Pay is an early-stage FinTech building cross-border remittance "
            "infrastructure. Pre-Series-A, 12 engineers.\n\n"
            "**You will:**\n"
            "- Build payment processing services in .NET 8 with PostgreSQL\n"
            "- Integrate partner banking APIs and card schemes\n"
            "- Own areas end-to-end: design, build, deploy, run\n"
            "- Help shape technical culture as one of the early senior hires\n\n"
            "**You have:**\n"
            "- 6+ years backend experience with C# / .NET\n"
            "- Production payment systems experience strongly preferred\n"
            "- Experience integrating partner / card scheme APIs\n"
            "- Comfort with ambiguity and start-up pace\n"
            "- AWS production experience\n\n"
            "Salary £85k-£105k + 0.1-0.5% equity. Hybrid: 1-2 days in office."
        ),
    },
    {
        # SOFT-FAKE — adjacent but missing core skills
        "company": "Vortex Streaming",
        "role": "Senior Backend Engineer (Go / Streaming)",
        "location": "Remote (UK)",
        "work_type": "Remote",
        "platform": "Hacker News",
        "source_url": "https://example.com/jobs/vortex-go-streaming",
        "currency": "GBP",
        "salary_min": 90,
        "salary_max": 115,
        "status": "New",
        "starred": False,
        "description": (
            "Vortex Streaming runs live video infrastructure serving 50M concurrent "
            "viewers. Hiring a Senior Backend Engineer for our streaming platform team.\n\n"
            "**You will:**\n"
            "- Build high-throughput Go services for live video ingest and distribution\n"
            "- Optimise for latency at the edge across global CDN\n"
            "- Work with Kubernetes, Kafka, Cassandra at significant scale\n"
            "- On-call rotation for production infrastructure\n\n"
            "**You have:**\n"
            "- 5+ years experience writing production Go services\n"
            "- Strong distributed systems background\n"
            "- Experience operating high-scale infrastructure (10k+ RPS)\n"
            "- Comfort with Kubernetes, Kafka, observability tooling\n\n"
            "**Nice to have:** Live streaming, video codec, or CDN experience.\n\n"
            "Salary £90k-£115k. Fully remote within UK."
        ),
    },
]


def seed():
    print(f"[seed] Initialising DB schema...")
    init_db()
    db: Session = SessionLocal()
    try:
        # 1. Wipe existing demo data
        print(f"[seed] Wiping existing data...")
        db.execute(text("TRUNCATE TABLE jobs RESTART IDENTITY CASCADE"))
        db.execute(text("DELETE FROM profile"))
        db.commit()

        # 2. Insert profile
        print(f"[seed] Inserting profile...")
        profile = models.Profile(id=1, **PROFILE_DATA)
        db.add(profile)
        db.commit()

        # 3. Insert jobs + run AI on each
        for i, job_data in enumerate(DEMO_JOBS, start=1):
            print(f"\n[seed] [{i}/{len(DEMO_JOBS)}] {job_data['company']} - {job_data['role']}")

            job = models.Job(**job_data)
            db.add(job)
            db.commit()
            db.refresh(job)

            # Run AI: analysis
            try:
                print(f"  ├─ Running suitability analysis...")
                result = ai.analyze_job(db, job.description, job.role, job.company)
                job.suitability = result.get("score")
                job.matched_skills = result.get("matched_skills", [])
                job.missing_skills = result.get("missing_skills", [])
                job.reasoning = result.get("reasoning", "")
                job.salary_alignment = result.get("salary_alignment", "")
                job.red_flags = result.get("red_flags", [])
                from datetime import datetime
                job.analyzed_at = datetime.utcnow()
                db.commit()
                print(f"  │  └─ Score: {job.suitability}/100")
            except Exception as e:
                print(f"  │  └─ FAILED: {e}")
                continue

            # Run AI: prep
            try:
                print(f"  ├─ Generating interview prep...")
                prep_result = ai.prep_interview(db, job.description, job.role, job.company)
                job.interview_prep = prep_result
                db.commit()
                print(f"  │  └─ Done.")
            except Exception as e:
                print(f"  │  └─ FAILED: {e}")

            # Run AI: tailored CV (only for top-scoring jobs to save cost)
            if job.suitability and job.suitability >= 70:
                try:
                    print(f"  └─ Generating tailored CV...")
                    cv_result = ai.tailor_doc(db, job.description, job.role, job.company, "cv")
                    docs = job.tailored_docs or {}
                    docs["cv"] = cv_result
                    job.tailored_docs = docs
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(job, "tailored_docs")
                    db.commit()
                    print(f"     └─ ATS match: {cv_result.get('ats_match_pct')}%")
                except Exception as e:
                    print(f"     └─ FAILED: {e}")
            else:
                print(f"  └─ Skipping tailored CV (score < 70)")

            # Tiny delay to avoid rate limits
            time.sleep(0.5)

        # 4. Summary
        print(f"\n[seed] Done!")
        total_jobs = db.query(models.Job).count()
        analyzed = db.query(models.Job).filter(models.Job.suitability.isnot(None)).count()
        print(f"[seed]   Jobs in DB: {total_jobs}")
        print(f"[seed]   With AI scores: {analyzed}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
