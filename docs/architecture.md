# Architecture

![Architecture](images/architecture.png)

## Components

```
Browser (Next.js 14 client)
   │  fetch + Bearer JWT (localStorage)
   ▼
FastAPI  :8000 ──► PostgreSQL 16 :5432
   │
   ├─► scraper.fetch_page(url)   httpx + BeautifulSoup → plain text
   ├─► ai.*                      Anthropic Messages API → JSON dicts
   └─► cv_export.build_docx/pdf  python-docx / reportlab
```

All three containers run on one host (local Docker or a single EC2 `t4g.small`).

## Request flow: "Add from URL"

1. `AddFromUrlModal` → `api.createFromUrl(url)` → `POST /jobs/from-url`
2. `scraper.fetch_page` strips scripts/nav/footer and returns readable text
3. `ai.extract_job_from_html` → Claude returns company, role, location, salary, description
4. A `Job` row is created with `status="New"` and `platform` inferred from the URL
5. The user then triggers `analyze`, `prep`, `research`, `tailor` separately (each is one Claude call)

## Data model

**`jobs`**: one row per posting.
- Listing: `company, role, location, work_type, platform, source_url, description, salary_min/max, currency`
- Tracking: `status` (`New|Applied|Interviewing|Offer|Rejected`), `notes, starred, applied_date`
- AI (JSON): `suitability` (int), `analysis`, `interview_prep`, `company_research`, `tailored_docs` (keyed by `cv|cover_letter|recruiter_email`)
- Timestamps: `created_at, updated_at, analyzed_at`

**`profile`**: a single row (`id=1`) that holds the user's CV in markdown sections plus
private targeting fields (`target_roles, target_salary, deal_breakers, private_notes`).
It is rendered into every AI prompt by `ai.render_profile`.

## Auth

Hand-rolled HS256 JWT (`auth.py`). One admin user from config. Two dependencies:
- `require_read`: open in demo mode, otherwise needs a valid token
- `require_write`: always 403 in demo mode, otherwise needs a valid token

## Configuration

`config.py` loads the first `config.json` found (`$CONFIG_PATH`, `./`, `/app/`, `backend/`),
then **environment variables override** it (field name uppercased, e.g. `ANTHROPIC_API_KEY`, `DATABASE_URL`).

## Key design choices

See the README "Why this design" table and the ADRs in [decisions/](decisions/).
