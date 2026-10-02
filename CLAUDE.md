# CLAUDE.md

Guidance for Claude Code (and other AI assistants) working in this repository.
Read this first, then `BACKLOG.md` for what to work on and `SKILLS.md` for
the reusable workflows.

## What this project is

**Job Hunting AI**: a single-user, self-hosted job application dashboard.
Paste a job URL, and the app scrapes it, extracts structured fields with Claude,
scores fit against the user's profile (0–100), writes a tailored CV, cover letter
and recruiter email, prepares interview questions, and tracks the pipeline
(New → Applied → Interviewing → Offer / Rejected).

## Stack

| Layer    | Tech |
|----------|------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind, SWR, lucide-react, framer-motion |
| Backend  | FastAPI, SQLAlchemy 2.0, Pydantic v2, Python 3.12 |
| AI       | Anthropic Claude via the `anthropic` SDK (`backend/app/ai.py`) |
| DB       | PostgreSQL 16 (Docker) |
| Export   | `python-docx` and `reportlab` (`backend/app/cv_export.py`) |
| Infra    | Docker Compose; AWS EC2 `t4g.small` (ARM) provisioned with Terraform (`infra/main.tf`) |

## Repository map

```
backend/app/
  main.py        FastAPI routes (auth, profile, jobs, AI actions)
  ai.py          All Claude calls: prompts (*_SYSTEM constants) + _call_json helper
  models.py      SQLAlchemy models: Job, Profile (single row, id=1)
  schemas.py     Pydantic request/response models
  auth.py        Hand-rolled HS256 JWT; require_read / require_write dependencies
  config.py      Settings: config.json first, then env vars (UPPERCASE field names) override
  db.py          Engine, session, init_db() (create_all, no migrations)
  scraper.py     httpx + BeautifulSoup page-to-text
  cv_export.py   Tailored CV markdown → .docx / .pdf
backend/app.broken/   Old snapshot from before the Claude migration. Do not edit or import it.
frontend/src/
  app/           Pages: / (overview), /applications, /profile, /login
  components/    Sidebar, modals, tabs/ (Analysis, Description, InterviewPrep, TailoredCV)
  lib/api.ts     Typed API client + TS types mirroring backend schemas
infra/main.tf    EC2, security group, EIP
docs/            Architecture, API, AI, development and deployment docs, ADRs, templates
.claude/         Slash commands (commands/) and project skills (skills/)
```

Root-level `MAIN_PY_ADDITION.py` and `FRONTEND_CV_DOWNLOAD.tsx` are paste-in
snippets, not live code. See BACKLOG item **B-001**.

## Commands

```bash
# Full local stack (db :5432, api :8000, frontend :3000)
cp backend/config.example.json backend/config.json   # then fill in keys/passwords
docker compose up -d --build
docker compose logs -f api

# Backend changes need a rebuild (no hot reload in the api container)
docker compose up -d --build api

# Frontend checks
cd frontend && npm ci && npm run lint && npx tsc --noEmit && npm run build

# Backend quick checks (no test suite yet; see BACKLOG)
cd backend && python -m compileall -q app

# Production (on EC2)
sudo docker compose -f docker-compose.prod.yml up -d --build
```

## Conventions and rules

- **Backend and frontend contract.** If you change a Pydantic schema in `schemas.py`,
  update the matching TS interface in `frontend/src/lib/api.ts` in the same change.
- **AI calls go through `ai._call_json`.** Every AI feature is a `*_SYSTEM` prompt
  plus a function that builds the user message and returns a parsed dict. Keep the
  JSON shape stable, because the frontend tabs render it directly. Document any
  shape change in `docs/ai.md`.
- **Profile privacy.** `render_profile(include_private=False)` must be used for any
  output the user will send to employers (tailored docs). Private fields
  (`target_salary`, `deal_breakers`, `private_notes`) must never leak into them.
- **Auth.** Read endpoints use `Depends(auth.require_read)`. Mutating and AI
  endpoints use `Depends(auth.require_write)`. Demo mode depends on this split.
- **Schema changes.** There are no migrations: `init_db()` only creates missing
  tables. A new column on an existing table needs a manual `ALTER TABLE` (document
  it in the PR / `docs/development.md`) until migrations land (BACKLOG **B-004**).
- **AI-derived data lives in JSON columns** (`analysis`, `interview_prep`,
  `company_research`, `tailored_docs`) so shapes can change without migrations.
- **Secrets.** Never commit `backend/config.json`, `.env*`, or `infra/terraform.tfvars`.
  Only edit the `*.example.json` files.
- **Model IDs** come from `settings.anthropic_model`. Do not hard-code them in code.
- Match the existing style: short module docstrings, section banner comments in
  `main.py`, type hints, no new dependencies without a reason in the PR.
- Use British English in user-facing copy and default currency `GBP`.

## Definition of done

1. Code compiles: `python -m compileall backend/app` and `npx tsc --noEmit` in `frontend/`.
2. `npm run lint` passes for frontend changes.
3. Backend and frontend types agree.
4. Docs updated (`docs/`, README if user-facing) and the BACKLOG item ticked / moved.
5. No secrets, no edits to `app.broken/`.

## Working with the backlog

- `BACKLOG.md` is the source of truth for planned work. Item IDs look like `B-###`.
- Use `/backlog` to triage and `/implement B-###` to work an item end to end.
- New ideas go to the **Inbox** section using `docs/templates/backlog-item.md`.
