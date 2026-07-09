"""Lightweight SQLite migrations for auth columns."""

from sqlalchemy import inspect, text

from db.session import engine


def ensure_user_auth_columns() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("users")}
    alters = []
    if "google_id" not in columns:
        alters.append("ALTER TABLE users ADD COLUMN google_id TEXT")
    if "name" not in columns:
        alters.append("ALTER TABLE users ADD COLUMN name TEXT")
    if "avatar_url" not in columns:
        alters.append("ALTER TABLE users ADD COLUMN avatar_url TEXT")
    if not alters:
        return
    with engine.begin() as conn:
        for stmt in alters:
            conn.execute(text(stmt))
