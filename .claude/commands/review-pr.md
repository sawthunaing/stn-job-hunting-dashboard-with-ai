---
description: Review the current diff against project conventions
---

Review the current changes (`git diff` against the default branch, plus staged and unstaged changes).

Check specifically against `CLAUDE.md`:
- Pydantic schemas and `frontend/src/lib/api.ts` types still agree.
- New routes use `require_read` / `require_write` correctly (AI and mutations must use `require_write`).
- Tailored, employer-facing AI output uses `include_private=False`.
- New model columns come with manual SQL or a migration.
- No hard-coded model IDs, no secrets, no edits to `backend/app.broken/`.
- Docs and `BACKLOG.md` updated.

Then look for real bugs: error handling, null states in the UI, demo mode 403s.
Output findings ranked by severity with `file:line`. Leave out style nitpicks unless they break a convention.
