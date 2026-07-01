"""
Alembic environment configuration.

Loads the application's SQLAlchemy metadata so that ``autogenerate``
can diff the current models against the database and produce migrations.

Key design decisions:
  - DATABASE_URL is sourced from ``app.core.config.settings`` (which already
    handles .env loading and SSM secrets) — never hardcoded here.
  - All model modules are imported via ``app.models`` to ensure every table
    is registered on ``Base.metadata`` before autogenerate runs.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.database import Base

# Import all models so their tables are registered on Base.metadata.
# This ensures autogenerate can detect every table.
from app.models import (  # noqa: F401
    chat_model,
    flashcard_model,
    material_model,
    quiz_model,
    space_model,
    user_model,
    video_model,
)

# Alembic Config object — provides access to values in alembic.ini.
config = context.config

# Set sqlalchemy.url from application settings so we never duplicate secrets.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The MetaData object for 'autogenerate' support.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    Useful for reviewing migration SQL before applying it.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    Uses NullPool to avoid dangling connections in short-lived processes
    (CI runners, Lambda cold starts, etc.).
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
