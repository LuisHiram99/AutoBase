from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# env.py is at <repo>/backend/alembic/env.py — add the src directory to sys.path
# In Docker, PYTHONPATH is already set to /app/src, so we can import directly
# For local development, we need to add the path
try:
    from db.database import Base
    from db import models
except ModuleNotFoundError:
    # Fallback for local development
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / 'backend' / 'src'))
    from db.database import Base
    from db import models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Load environment variables from config/.env and set the sqlalchemy.url
# so Alembic uses the same DB configuration as the application.
try:
    # In Docker, config is at /app/config/.env
    # For local dev, it's at backend/config/.env relative to repo root
    env_path = Path('/app/config/.env')
    if not env_path.exists():
        # Fallback for local development
        env_path = Path(__file__).resolve().parents[1] / 'config' / '.env'
    
    load_dotenv(dotenv_path=env_path)
    
    # Check for DATABASE_URL first (Railway provides this)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Convert async URL to sync for Alembic
        if 'postgresql+asyncpg://' in database_url:
            db_url = database_url.replace('postgresql+asyncpg://', 'postgresql+psycopg2://')
        elif database_url.startswith('postgres://'):
            db_url = database_url.replace('postgres://', 'postgresql+psycopg2://', 1)
        elif database_url.startswith('postgresql://'):
            db_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
        else:
            db_url = database_url
        config.set_main_option('sqlalchemy.url', db_url)
    else:
        # Fallback to individual environment variables
        DB_USER = os.getenv('DB_USER')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        DB_HOST = os.getenv('DB_HOST', 'localhost')
        DB_PORT = os.getenv('DB_PORT', '5432')
        DB_NAME = os.getenv('DB_NAME')
        if DB_USER and DB_PASSWORD and DB_NAME:
            # Use sync psycopg2 driver for Alembic/SQLAlchemy Engine
            db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            config.set_main_option('sqlalchemy.url', db_url)
except Exception as e:
    # If anything fails, fall back to the value already present in alembic.ini
    print(f"Warning: Could not load database configuration: {e}")
    pass

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

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

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
