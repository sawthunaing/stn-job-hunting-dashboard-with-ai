# Backlog

The single source of truth for planned work. Claude reads this before starting
any task (see `CLAUDE.md`).

**Item format:** `B-###` · priority `P0` (broken) / `P1` (next) / `P2` (later) / `P3` (idea) · size `S` / `M` / `L`.
Use `docs/templates/backlog-item.md` for the full item format when an item needs detail.
When an item is done, tick it and move it to **Done** with the date and PR link.

---

## 🔥 Now (P0 / P1)

- [ ] **B-001 · P0 · S: Wire up the tailored-CV download endpoint**
  - `cv_export` is imported in `backend/app/main.py`, but no route exists. The frontend
    (`frontend/src/lib/api.ts` → `downloadCV`) calls `GET /jobs/{id}/cv?format=pdf|docx`.
  - The paste-in snippet `MAIN_PY_ADDITION.py` defines `/jobs/{id}/cv/download`, which is a **path mismatch**.
    Pick one path (recommend `/jobs/{id}/cv`, so the frontend does not change) and add it to `main.py`.
  - Then delete `MAIN_PY_ADDITION.py` and `FRONTEND_CV_DOWNLOAD.tsx` from the repo root.
  - Acceptance: downloading a tailored CV from the Tailored CV tab yields a valid .pdf and .docx.

- [ ] **B-002 · P1 · S: Fix error handling in `downloadCV`**
  - In `api.ts`, the `throw` inside `try { JSON.parse }` is caught by its own `catch`, so
    `detail` from the API is replaced by the raw response text. Parse first, throw outside the try.

- [ ] **B-003 · P1 · S: Update README for the Claude migration**
  - README still describes OpenAI / GPT-5, model-quirk detection and OpenAI cost tables.
    Update the stack badge, AI section, cost table, and "How to run" (Anthropic key).
  - Also fix the stale "OpenAI key" comments in `docker-compose.yml` and `backend/docker-compose.yml`.

- [ ] **B-004 · P1 · M: Add database migrations (Alembic)**
  - `init_db()` only runs `create_all`, so new columns on existing tables need a manual `ALTER`.
  - Add Alembic with a baseline revision matching the current `models.py`, and run migrations on startup or deploy.

- [ ] **B-005 · P1 · M: Backend test suite**
  - Add `pytest` + `httpx` TestClient. Cover auth (login, read/write and demo mode), job CRUD,
    and AI routes with `ai._call_json` mocked. SQLite or a Postgres test container.

## 📋 Next (P2)

- [ ] **B-006 · P2 · S: CI workflow**: GitHub Actions running backend compile + pytest and
      frontend lint, `tsc --noEmit`, and build on every PR.
- [ ] **B-007 · P2 · S: Remove `backend/app.broken/`** once B-001 is confirmed working (it is a pre-migration snapshot).
- [ ] **B-008 · P2 · S: Remove legacy `openai_*` settings** from `config.py` after confirming no deployed `config.json` relies on them
      (Pydantic ignores unknown keys by default, so removal is safe).
- [ ] **B-009 · P2 · S: Restore or document the demo stack**: README and commits reference
      `docker-compose.demo.yml` and a seed script that are not in the tree (`backend/app/scripts/` is empty).
- [ ] **B-010 · P2 · M: Robust AI JSON output**: replace "return only JSON" prompting with Claude
      tool use / structured output so `_call_json` never fails on malformed JSON; add retry once on parse failure.
- [ ] **B-011 · P2 · S: Prompt caching for the profile block**: the rendered profile is sent on every call;
      mark it as a cacheable system block to cut cost and latency.
- [ ] **B-012 · P2 · M: Scraper hardening**: JS-rendered pages (LinkedIn, Workday) often return empty text.
      Detect thin content and return a clear 422 asking the user to paste the description.
- [ ] **B-013 · P2 · S: `datetime.utcnow()` deprecation**: switch to timezone-aware `datetime.now(UTC)`;
      `@app.on_event("startup")` → lifespan handler.

## 💡 Later / ideas (P3)

- [ ] **B-014 · P3 · M: Follow-up reminders**: due dates per job plus an overview widget.
- [ ] **B-015 · P3 · M: Cover-letter and recruiter-email export** (reuse `cv_export`).
- [ ] **B-016 · P3 · L: Multi-user support**: per-user `Profile`/`Job` ownership, OAuth (see README "production" table).
- [ ] **B-017 · P3 · S: Automated nightly Postgres backups to S3.**
- [ ] **B-018 · P3 · M: Per-request AI cost and token logging**, shown in the UI.

## 📥 Inbox (untriaged)

<!-- Add new items here with /backlog add "<idea>"; triage moves them above. -->

- [ ] **B-019 · P2 · S: Validate `doc_type` and AI errors at the API**: `TailorRequest.doc_type` is a free `str`;
      an unknown value raises `ValueError` in `ai.tailor_doc` and returns a 500. Use `Literal[...]` (gives a 422),
      and map `ValueError`/Anthropic errors in AI routes to a clean 502 with a message.

## ✅ Done

<!-- - [x] **B-000 · …** (YYYY-MM-DD, PR link) -->
