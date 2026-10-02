from alembic import context
from sqlalchemy import create_engine

from app.config import settings
from app.models import Base

engine = create_engine(settings.database_url)
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
