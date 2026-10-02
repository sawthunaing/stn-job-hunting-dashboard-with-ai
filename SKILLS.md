# Skills & Commands

An index of the reusable AI workflows in this repo. Claude Code loads these automatically:

- **Skills** (`.claude/skills/<name>/SKILL.md`) are step-by-step playbooks Claude
  picks up when a task matches their description.
- **Commands** (`.claude/commands/<name>.md`) are slash commands you type, e.g. `/implement B-001`.

## Project skills

| Skill | Use when | File |
|---|---|---|
| `add-api-endpoint` | Adding or changing a FastAPI route plus its schema and TS client | `.claude/skills/add-api-endpoint/SKILL.md` |
| `add-ai-feature` | Adding a new Claude-powered capability (prompt, function, route, tab) | `.claude/skills/add-ai-feature/SKILL.md` |
| `add-db-column` | Adding or changing fields on `Job` or `Profile` | `.claude/skills/add-db-column/SKILL.md` |
| `frontend-tab` | Adding or changing a per-job tab in the job detail view | `.claude/skills/frontend-tab/SKILL.md` |

## Slash commands

| Command | What it does |
|---|---|
| `/backlog [add "<idea>" \| triage \| next]` | View, add to, or triage `BACKLOG.md` |
| `/implement B-###` | Implement a backlog item end to end: plan, code, check, update docs and backlog |
| `/spec <feature idea>` | Write a feature spec in `docs/specs/` from `docs/templates/feature-spec.md` |
| `/adr <decision title>` | Record an architecture decision in `docs/decisions/` |
| `/check` | Run the project's verification checks (compile, lint, typecheck, build) |
| `/review-pr` | Review the current diff against the CLAUDE.md conventions |
| `/tune-prompt <analysis\|prep\|research\|tailor\|extract>` | Iterate on a Claude system prompt in `ai.py` safely |

## Templates (for AI-structured work)

All in `docs/templates/`:

| Template | Purpose |
|---|---|
| `feature-spec.md` | Problem, scope, API/data/UI changes, acceptance criteria |
| `backlog-item.md` | Detailed backlog entry |
| `bug-report.md` | Repro steps, expected vs actual, suspected area |
| `adr.md` | Architecture Decision Record |
| `ai-prompt.md` | Spec for a Claude prompt: inputs, output JSON schema, guardrails, eval cases |
| `task-prompt.md` | A structured prompt to hand to Claude for any task |

## Adding a new skill or command

1. Skill: create `.claude/skills/<kebab-name>/SKILL.md` with `name` and `description` frontmatter.
   The description decides when Claude uses it, so say *when* it applies.
2. Command: create `.claude/commands/<name>.md`; `$ARGUMENTS` is replaced by what follows the command.
3. Add a row to the tables above.
