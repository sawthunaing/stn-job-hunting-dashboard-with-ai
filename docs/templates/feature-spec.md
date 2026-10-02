# Feature: <title>

> **For AI assistants:** fill every section, using real file paths, model fields and routes from this repo.
> Write "N/A" rather than deleting a section. Put unknowns in *Open questions*; do not guess.

- **Backlog ID:** B-###
- **Status:** Draft | Ready | In progress | Done
- **Owner:** <name>
- **Date:** YYYY-MM-DD

## 1. Problem
What user pain does this solve? One paragraph, from the job-seeker's point of view.

## 2. Goals / Non-goals
- Goals:
- Non-goals:

## 3. User flow
1. User does …
2. App shows …

## 4. Changes

### Data (`backend/app/models.py`)
| Table | Field | Type | Nullable | Notes |
|---|---|---|---|---|

Manual SQL / migration:
```sql
```

### API (`backend/app/main.py`, `schemas.py`)
| Method | Path | Auth (`read`/`write`) | Request | Response |
|---|---|---|---|---|

### AI (`backend/app/ai.py`)
Prompt spec: link to an `ai-prompt.md`-based section, or N/A.

### Frontend (`frontend/src/...`)
| File | Change |
|---|---|

## 5. Acceptance criteria
- [ ] Given …, when …, then …
- [ ] Demo mode: write actions return 403 and the UI shows the message
- [ ] Mobile (375px) layout works

## 6. Risks & edge cases
- Empty / null states, AI failure, scraper failure, cost impact

## 7. Test plan
- Automated:
- Manual:

## 8. Open questions
-
