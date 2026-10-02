"""Add source and external_id to jobs for imports from external boards.

Revision ID: 0001
Revises:

init_db() runs create_all first, so fresh databases already have these columns
and existing ones (created before this migration) get them here. Every step is
guarded so the migration is safe to run in either state.
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

INDEX = "ix_jobs_source_external_id"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    cols = {c["name"] for c in insp.get_columns("jobs")}
    if "source" not in cols:
        op.add_column("jobs", sa.Column("source", sa.String(50), nullable=True))
    if "external_id" not in cols:
        op.add_column("jobs", sa.Column("external_id", sa.String(100), nullable=True))
    if INDEX not in {i["name"] for i in insp.get_indexes("jobs")}:
        op.create_index(INDEX, "jobs", ["source", "external_id"], unique=True)


def downgrade() -> None:
    op.drop_index(INDEX, table_name="jobs")
    op.drop_column("jobs", "external_id")
    op.drop_column("jobs", "source")
