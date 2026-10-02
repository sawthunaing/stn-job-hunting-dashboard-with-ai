---
description: Review the current diff against project conventions, plus Claude Code's /code-review bug hunt
argument-hint: "[low|medium|high|xhigh|max]"
---

Review the current changes (`git diff` against the default branch, plus staged and unstaged changes)
in two passes, then merge the results into one report.

## Pass 1: project conventions

Check specifically against `CLAUDE.md`:
- Pydantic schemas and `frontend/src/lib/api.ts` types still agree.
- New routes use `require_read` / `require_write` correctly (AI and mutations must use `require_write`).
- Tailored, employer-facing AI output uses `include_private=False`.
- New model columns come with manual SQL or a migration.
- No hard-coded model IDs, no secrets, no edits to `backend/app.broken/`.
- Docs and `BACKLOG.md` updated.

Then look for real bugs: error handling, null states in the UI, demo mode 403s.

## Pass 2: Claude Code bug hunt

Invoke the built-in `code-review` skill with the Skill tool on the same diff. Pass `$ARGUMENTS`
through as its effort level if one was given; otherwise use `medium`. Do not use `--fix` or
`--comment`: this command only reports.

## Report

Combine both passes into one list ranked by severity, with `file:line` for each finding.
Drop duplicates (keep the clearer wording) and tag each finding `[convention]` or `[bug]`.
Leave out style nitpicks unless they break a convention.
