"""AdProof FastAPI application entrypoint."""

import os
import sys

# Ensure worker package root is on path
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from api.assets import router as assets_router
from api.auth import router as auth_router
from api.briefs import router as briefs_router
from api.library import router as library_router
from api.runs import router as runs_router
from api.webhooks import router as webhooks_router
from config import get_settings
from db.models import Base
from db.migrate import ensure_user_activities_table, ensure_user_auth_columns
from db.session import engine, get_database_url


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_user_auth_columns()
    ensure_user_activities_table()
    yield


app = FastAPI(title="AdProof API", version="0.1.0", lifespan=lifespan)

settings = get_settings()

# Demo mode: allow any localhost port (Next.js may use 3001, 3002, etc.)
_cors_kwargs: dict = {
    "allow_origins": settings.cors_origin_list,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if settings.is_mock_mode:
    _cors_kwargs["allow_origin_regex"] = r"http://(localhost|127\.0\.0\.1)(:\d+)?"

app.add_middleware(CORSMiddleware, **_cors_kwargs)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(briefs_router, prefix="/briefs", tags=["briefs"])
app.include_router(runs_router, prefix="/runs", tags=["runs"])
app.include_router(library_router, prefix="/library", tags=["library"])
app.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])
app.include_router(assets_router, prefix="/assets", tags=["assets"])


@app.get("/health")
def health():
    db_ok = "unknown"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = "connected"
    except Exception:
        db_ok = "disconnected"

    redis_ok = "skipped"
    if settings.use_rq_worker:
        try:
            import redis

            r = redis.from_url(settings.redis_url)
            r.ping()
            redis_ok = "connected"
        except Exception:
            redis_ok = "disconnected"

    return {
        "status": "ok",
        "db": db_ok,
        "db_dialect": engine.dialect.name,
        "database_url_scheme": get_database_url().split("://", 1)[0] if get_database_url() else "none",
        "redis": redis_ok,
        "pipeline_mode": settings.pipeline_mode,
        "mock_mode": settings.is_mock_mode,
    }
