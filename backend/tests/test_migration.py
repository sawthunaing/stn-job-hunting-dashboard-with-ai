import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from pathlib import Path

from app import db


def test_migration_upgrades_pre_existing_jobs_table(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path}/old.db"
    engine = sa.create_engine(url)
    with engine.begin() as c:
        c.execute(sa.text("CREATE TABLE jobs (id INTEGER PRIMARY KEY, company VARCHAR(200), role VARCHAR(300))"))
    monkeypatch.setattr("app.config.settings.database_url", url)

    backend = Path(db.__file__).resolve().parent.parent
    cfg = Config(str(backend / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend / "migrations"))
    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")  # idempotent

    insp = sa.inspect(engine)
    cols = {c["name"] for c in insp.get_columns("jobs")}
    assert {"source", "external_id"} <= cols
    assert "ix_jobs_source_external_id" in {i["name"] for i in insp.get_indexes("jobs")}
