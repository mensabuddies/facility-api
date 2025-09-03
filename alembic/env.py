import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

# --- Make sure we can import app.src.config.database ---
BASE_DIR = Path(__file__).resolve().parents[1]  # api/
sys.path.append(str(BASE_DIR))

# Your app's DB + models
from app.src.config.database import connection_string
from sqlmodel import SQLModel
# IMPORTANT: import all models so SQLModel.metadata is populated
# (database.py already defines all models; importing it suffices)
from app.src.config import database  # noqa

# Alembic Config object, provides access to values within .ini file
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set DB URL programmatically to avoid duplication
config.set_main_option("sqlalchemy.url", connection_string)

# Target metadata for 'autogenerate'
target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,               # detect type changes
        compare_server_default=True,     # detect server default changes
        include_schemas=False,
        version_table="alembic_version",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode'."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:  # type: Connection
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=False,
            version_table="alembic_version",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
