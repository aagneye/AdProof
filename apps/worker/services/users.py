"""User lookup and Google OAuth upsert."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from db.models import User


def upsert_google_user(
    db: Session,
    *,
    email: str,
    google_id: str,
    name: str | None = None,
    avatar_url: str | None = None,
) -> User:
    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()

    if user:
        user.email = email
        user.google_id = google_id
        user.name = name or user.name
        user.avatar_url = avatar_url or user.avatar_url
    else:
        user = User(
            email=email,
            google_id=google_id,
            name=name,
            avatar_url=avatar_url,
        )
        db.add(user)

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user
