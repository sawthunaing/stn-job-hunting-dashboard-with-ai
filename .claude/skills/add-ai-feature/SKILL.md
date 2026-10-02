---
name: add-ai-feature
description: Use when adding a new Claude-powered capability (new prompt and AI function in backend/app/ai.py, a route, a JSON column, and a frontend tab), or substantially changing an existing one.
---

# Add an AI feature

1. **Spec the prompt** with `docs/templates/ai-prompt.md`: inputs, exact output JSON schema,
   guardrails, and 2–3 eval cases. Save it under `docs/specs/`.
2. **Prompt + function** in `backend/app/ai.py`:
   - Add a `FOO_SYSTEM = """..."""` constant that includes the JSON schema as an example object.
   - Add `def foo(db: Session, ...) -> dict[str, Any]` that builds the user message with
     `_load_profile(db, include_private=...)` and returns `_call_json(FOO_SYSTEM, user, max_output_tokens=...)`.
   - Use `include_private=False` if any part of the output may be sent to an employer.
3. **Storage**: prefer a JSON column on `Job`. A new column needs the `add-db-column` skill.
4. **Route**: `POST /jobs/{job_id}/foo` with `require_write`, following `analyze` / `prep` in `main.py`.
5. **Frontend**: add a TS interface for the JSON shape, an `api.foo()` method, and render it
   (see the `frontend-tab` skill). Handle the `null` (not generated yet) state with a "Generate" button.
6. **Docs**: add the feature and its JSON shape to `docs/ai.md`.
7. **Never** hard-code a model ID; use `settings.anthropic_model`.
