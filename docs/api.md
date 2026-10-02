# API reference

Base URL: `http://localhost:8000` (local). Interactive docs: `/docs` (Swagger), `/redoc`.
Auth: `Authorization: Bearer <token>` from `POST /auth/login`.

Legend: 🌐 public · 👁 `require_read` (open in demo mode) · ✏️ `require_write` (403 in demo mode)

## Auth & meta

| Method | Path | Auth | Body → Response |
|---|---|---|---|
| POST | `/auth/login` | 🌐 | `{username, password}` → `{token, username, expires_in_hours}` |
| GET | `/auth/me` | 👁 | → `{username}` |
| GET | `/health` | 🌐 | → `{ok, ts}` |
| GET | `/demo-info` | 🌐 | → `{demo_mode}` |

## Profile

| Method | Path | Auth | Body → Response |
|---|---|---|---|
| GET | `/profile` | 👁 | → `ProfileSchema` (empty if not set) |
| PUT | `/profile` | ✏️ | `ProfileSchema` → `ProfileSchema` (upsert row id=1) |

## Jobs

| Method | Path | Auth | Body → Response |
|---|---|---|---|
| GET | `/jobs?status_filter=&q=` | 👁 | → `JobListItem[]` (newest first; `q` matches company/role) |
| GET | `/jobs/{id}` | 👁 | → `JobDetail` |
| POST | `/jobs` | ✏️ | `JobCreate` → `JobDetail` (201) |
| POST | `/jobs/from-url` | ✏️ | `{url}` → `JobDetail` (201); scrape + Claude extraction |
| PATCH | `/jobs/{id}` | ✏️ | `JobUpdate` (partial) → `JobDetail` |
| DELETE | `/jobs/{id}` | ✏️ | → 204 |

## AI actions (each is one Claude call)

| Method | Path | Auth | Writes to | Notes |
|---|---|---|---|---|
| POST | `/jobs/{id}/analyze` | ✏️ | `analysis`, `suitability`, `analyzed_at` | 400 if no description |
| POST | `/jobs/{id}/prep` | ✏️ | `interview_prep` | 400 if no description |
| POST | `/jobs/{id}/research` | ✏️ | `company_research` | |
| POST | `/jobs/{id}/tailor` | ✏️ | `tailored_docs[doc_type]` | body `{doc_type: "cv"\|"cover_letter"\|"recruiter_email"}` |

## Planned

| Method | Path | Status |
|---|---|---|
| GET | `/jobs/{id}/cv?format=pdf\|docx` | **Not implemented yet.** The frontend already calls it. See BACKLOG B-001 |

Schemas live in `backend/app/schemas.py`; TS mirrors in `frontend/src/lib/api.ts`.
