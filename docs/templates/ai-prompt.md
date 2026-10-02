# AI prompt spec: <feature>

> **For AI assistants:** a prompt in `backend/app/ai.py` is a contract with the frontend.
> Define the output schema first, then write the prompt.

- **Function:** `ai.<name>(db, ...)`
- **System prompt constant:** `<NAME>_SYSTEM`
- **Model:** `settings.anthropic_model` (do not hard-code)
- **max_output_tokens:** <n>
- **Profile:** `include_private=True` | `False` (must be `False` if any output reaches an employer) | not used

## Inputs
| Name | Source | Notes |
|---|---|---|
| description | `Job.description` | may be long; truncate if > N chars |

## Output JSON schema
```json
{
  "field": "type and meaning"
}
```
TS interface in `frontend/src/lib/api.ts`:
```ts
export interface Foo { }
```

## Guardrails
- Return only JSON, with every key present (empty arrays rather than missing keys)
- Never invent employers, dates or qualifications the profile does not contain
- British English; currency defaults to GBP

## Eval cases
| # | Input summary | Expected properties of output |
|---|---|---|
| 1 | Strong match senior .NET role | suitability ≥ 75, no fabricated skills |
| 2 | Empty profile | low score, summary says profile missing |
| 3 | | |

## Draft prompt
```
You are …
Respond with a JSON object:
{ … }
```
