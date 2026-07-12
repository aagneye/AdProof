"""Database session management."""

import logging
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()


def _make_sqlite_engine(path: str | None = None):
    if path is None:
        path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "adproof_local.db")
        )
    url = path if path.startswith("sqlite:") else f"sqlite:///{path}"
    return create_engine(url, connect_args={"check_same_thread": False})


def _create_engine(url: str):
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True)


if not DATABASE_URL:
    engine = _make_sqlite_engine()
    DATABASE_URL = str(engine.url)
    logger.warning("DATABASE_URL unset — using local SQLite: %s", DATABASE_URL)
elif DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres"):
    # Fail loudly — never silently fall back to SQLite when Postgres is configured.
    # Silent fallback caused OAuth users to appear in Supabase Auth while briefs/runs
    # were written to a local SQLite file that nobody inspected.
    engine = _create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Connected to Postgres DATABASE_URL")
elif DATABASE_URL.startswith("sqlite"):
    engine = _create_engine(DATABASE_URL)
    logger.info("Using SQLite DATABASE_URL: %s", DATABASE_URL)
else:
    engine = _create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Connected to DATABASE_URL dialect=%s", engine.dialect.name)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_database_url() -> str:
    return DATABASE_URL
