# Task prompt template

Copy this, fill it in, and paste it to Claude (or run `/implement B-###` for backlog items).

```
## Goal
<one sentence: what should be true when this is done>

## Context
- Backlog item: B-### (or N/A)
- Relevant files: <paths>
- Related docs: CLAUDE.md, docs/<file>.md

## Requirements
1.
2.

## Constraints
- Follow CLAUDE.md conventions (schemas ↔ api.ts in sync, require_read/require_write, privacy rule)
- No new dependencies unless justified
- Do not touch backend/app.broken/ or any secrets

## Acceptance criteria
- [ ]
- [ ] /check passes

## Output
- Summary of changed files
- How you verified it
- Follow-ups added to the BACKLOG Inbox
```
