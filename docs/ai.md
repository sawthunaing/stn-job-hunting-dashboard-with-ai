# AI integration

All Claude calls live in `backend/app/ai.py`.

## How a call works

`_call_json(system, user, max_output_tokens)`:
1. Appends "respond with ONLY a single valid JSON object" to the system prompt
2. Calls `client().messages.create(model=settings.anthropic_model, temperature=0.4, ...)`
3. Joins the text blocks, strips stray markdown fences, `json.loads`, and raises `ValueError` on bad JSON

Model is configured via `anthropic_model` in `config.json` / `ANTHROPIC_MODEL` env.

## Features and JSON contracts

The frontend renders these shapes directly (types in `frontend/src/lib/api.ts`). **Changing a shape is a breaking change.**

| Function | Prompt | Profile | Max tokens | Output shape |
|---|---|---|---|---|
| `extract_job_from_html` | `EXTRACT_SYSTEM` | none | 4000 | company, role, location, work_type, salary_min/max, currency, description |
| `analyze_job` | `ANALYSIS_SYSTEM` | private ✅ | 2500 | `Analysis`: suitability, summary, strengths[], gaps[], market_salary, negotiation |
| `generate_prep` | `PREP_SYSTEM` | private ✅ | 3500 | `InterviewPrep`: technical[{q,why,framework}], behavioral[{q,why}] |
| `research_company` | `RESEARCH_SYSTEM` | none | 1500 | `CompanyResearch`: culture, market, recent[{date,item}], talking_points[] |
| `tailor_doc` | `TAILOR_SYSTEM` | **public only** ❌ | 4000 | `TailoredDoc`: content (markdown), ats_match_pct, keywords_matched/missing, suggestions |

## Privacy rule

Tailored documents go to employers, so `tailor_doc` uses `render_profile(include_private=False)`.
Target salary, deal-breakers and private notes must **never** appear in tailored output.
The private section is also labelled "do NOT include in tailored docs" inside prompts that do see it.

## Writing or changing a prompt

Use `docs/templates/ai-prompt.md` and the `/tune-prompt` command. Keep the output schema
inside the prompt as an example JSON object, as the existing prompts do.

## Prompt changelog

| Date | Prompt | Change | Why |
|---|---|---|---|
| — | all | Migrated from OpenAI to Anthropic Claude; JSON shapes unchanged | See ADR 0001 |
