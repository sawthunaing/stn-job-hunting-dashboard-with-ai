---
description: Run the project's verification checks
---

Run these checks from the repo root and report a pass/fail table. Fix failures that come from
your own changes; report others without fixing them.

```bash
python -m compileall -q backend/app
cd frontend && (test -d node_modules || npm ci) && npm run lint && npx tsc --noEmit
```

If a backend test suite exists (`backend/tests/`), also run `cd backend && pytest -q`.
For larger frontend changes, also run `cd frontend && npm run build`.
Also confirm: no changes under `backend/app.broken/`, and no secrets (`config.json`, `.env*`, `terraform.tfvars`) staged.
