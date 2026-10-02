# Development

## Setup

```bash
cp backend/config.example.json backend/config.json
# set anthropic_api_key, admin_username, admin_password, jwt_secret
docker compose up -d --build
```

- Frontend: http://localhost:3000 (hot reload from `frontend/src`)
- API: http://localhost:8000 (`/docs` for Swagger). **No hot reload**; run `docker compose up -d --build api` after backend edits.
- DB: `localhost:5432`, user/pass/db `trajectory`

First run: log in, fill in `/profile`, then add a job via **+ Add**.

## Running without Docker

```bash
# backend
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload   # needs a reachable Postgres in database_url

# frontend
cd frontend && npm ci && npm run dev
```

## Checks

```bash
python -m compileall -q backend/app
cd frontend && npm run lint && npx tsc --noEmit && npm run build
```

There is no automated test suite yet (BACKLOG B-005). `/check` runs the above.

## Manual schema changes

`init_db()` only creates missing tables. Record every column change here until migrations land (B-004):

| Date | SQL |
|---|---|
| — | _(none yet)_ |

Apply with: `docker compose exec db psql -U trajectory -d trajectory -c "<sql>"`

## Troubleshooting

| Symptom | Fix |
|---|---|
| Every request returns 401 "admin password not configured" | Set `admin_password` in `config.json` (the default value is rejected) |
| AI routes return 500 "ANTHROPIC_API_KEY not set" | Set `anthropic_api_key` or the `ANTHROPIC_API_KEY` env var |
| "Claude returned non-JSON" | Usually truncation; raise `max_output_tokens` for that function |
| Add-from-URL gives an empty/garbage job | Page is JS-rendered; add the job manually and paste the description (B-012) |
| Backend change has no effect | Rebuild: `docker compose up -d --build api` |
