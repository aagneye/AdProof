"""User activity event logging — tracks what each user does."""

import json
from typing import Any

from sqlalchemy.orm import Session

from db.models import UserActivity


def log_activity(
    db: Session,
    *,
    user_id: str,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    commit: bool = True,
) -> UserActivity:
    row = UserActivity(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
    return row


def list_user_activities(
    db: Session,
    user_id: str,
    *,
    limit: int = 50,
) -> list[UserActivity]:
    return (
        db.query(UserActivity)
        .filter(UserActivity.user_id == user_id)
        .order_by(UserActivity.created_at.desc())
        .limit(limit)
        .all()
    )
