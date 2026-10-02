---
description: Implement a backlog item end to end
argument-hint: B-###
---

Implement backlog item **$ARGUMENTS** from `BACKLOG.md`.

1. Read `CLAUDE.md` and the item. If the item is ambiguous, state your assumptions before coding.
2. Explore the files involved and check the item is still accurate (the code may have changed).
3. Use the matching project skill if one applies (`add-api-endpoint`, `add-ai-feature`, `add-db-column`, `frontend-tab`).
4. Make the smallest change that meets the acceptance criteria. Follow the conventions in CLAUDE.md.
5. Run `/check` (or the equivalent commands) and fix any failures.
6. Update docs in `docs/` and README if the behaviour is user-facing.
7. In `BACKLOG.md`, tick the item and move it to **Done** with today's date.
8. Summarise: what changed (files), how it was verified, and any follow-ups. Add follow-ups to the Inbox.
