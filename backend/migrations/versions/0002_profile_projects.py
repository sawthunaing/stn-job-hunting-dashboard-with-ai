"""Add projects to profile for a dedicated CV Projects section.

Revision ID: 0002
Revises: 0001

init_db() runs create_all first, so fresh databases already have this column
and existing ones (created before this migration) get it here. Guarded so the
migration is safe to run in either state.
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if "profile" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("profile")}
    if "projects" not in cols:
        op.add_column("profile", sa.Column("projects", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("profile", "projects")
