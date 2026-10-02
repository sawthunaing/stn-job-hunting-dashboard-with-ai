---
name: add-db-column
description: Use when adding, renaming, or changing a field on the Job or Profile SQLAlchemy models (backend/app/models.py), which requires coordinated schema, migration, and frontend updates.
---

# Add a DB column

There are no migrations yet (BACKLOG B-004). `init_db()` only creates **missing tables**,
so a new column on an existing table is not added automatically.

1. Add the `Mapped[...]` field to `backend/app/models.py`. Use `Optional[...]` and nullable
   so existing rows remain valid.
2. Add it to the relevant Pydantic schemas in `backend/app/schemas.py`
   (`JobBase` / `JobUpdate` / `JobDetail` / `JobListItem`, or `ProfileSchema`).
3. Mirror it in `frontend/src/lib/api.ts` interfaces.
4. Write the manual SQL and put it in the PR description and `docs/development.md` → "Manual schema changes":
   ```sql
   ALTER TABLE jobs ADD COLUMN IF NOT EXISTS follow_up_at TIMESTAMP NULL;
   ```
   Apply locally with: `docker compose exec db psql -U trajectory -d trajectory -c "<sql>"`.
5. If Alembic exists by then (B-004 done), generate a revision instead of steps 4's manual SQL.
