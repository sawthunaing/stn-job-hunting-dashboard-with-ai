# 0001. Migrate AI provider from OpenAI to Anthropic Claude

- **Status:** Accepted
- **Date:** 2026 (commit `26eb616`)

## Context

The backend originally used OpenAI GPT-5 family models and needed per-model
"quirk detection" (`max_tokens` vs `max_completion_tokens`, temperature and JSON mode support).

## Decision

Use Anthropic Claude via the `anthropic` SDK for all AI features. Keep the public
function signatures and output JSON shapes in `ai.py` unchanged so `main.py` and the frontend need no changes.

## Consequences

- ✅ Removes the quirk-detection layer; the Messages API is consistent across models.
- ✅ Model swap is a config change (`anthropic_model`).
- ⚠️ No JSON-mode flag: JSON is enforced by prompt plus fence stripping (see BACKLOG B-010 for a sturdier approach).
- ⚠️ README and some comments still describe OpenAI (B-003). Legacy `openai_*` settings remain (B-008).
- `backend/app.broken/` holds the pre-migration snapshot (B-007).
