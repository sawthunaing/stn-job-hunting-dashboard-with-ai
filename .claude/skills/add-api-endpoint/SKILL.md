---
name: add-api-endpoint
description: Use when adding or changing a FastAPI route in backend/app/main.py, including its Pydantic schema and the matching TypeScript client in frontend/src/lib/api.ts.
---

# Add an API endpoint

1. **Schema**: add request/response models to `backend/app/schemas.py`
   (`model_config = ConfigDict(from_attributes=True)` if returning ORM objects, as the existing schemas do).
2. **Route**: add it to `backend/app/main.py` under the right section banner
   (`AUTH`, `PROFILE`, `JOBS`, `AI ROUTES`).
   - Read-only: `_: str = Depends(auth.require_read)`
   - Mutating or AI-calling: `_: str = Depends(auth.require_write)` (blocked in demo mode)
   - Look up with `db.get(models.Job, job_id)` and `raise HTTPException(404, "not found")` when it is missing.
3. **Client**: add a method to the `api` object in `frontend/src/lib/api.ts` using `req<T>()`,
   and add or extend the TS interfaces so they mirror the Pydantic shape exactly (nullable means `| null`).
4. **Docs**: add the route to `docs/api.md`.
5. **Verify**: `python -m compileall -q backend/app`, then `cd frontend && npx tsc --noEmit`.
   If the stack is running: `docker compose up -d --build api` and exercise the route with curl and a Bearer token.
