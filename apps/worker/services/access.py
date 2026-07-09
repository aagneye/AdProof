"""Ownership checks — users may only access their own data."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.models import Brief, Run, User


def get_user_brief(db: Session, brief_id: str, user: User) -> Brief:
    brief = (
        db.query(Brief)
        .filter(Brief.id == brief_id, Brief.user_id == user.id)
        .first()
    )
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    return brief


def get_user_run(db: Session, run_id: str, user: User) -> Run:
    run = (
        db.query(Run)
        .join(Brief, Run.brief_id == Brief.id)
        .filter(Run.id == run_id, Brief.user_id == user.id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
