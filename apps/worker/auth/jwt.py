"""JWT creation and validation for API authentication."""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from config import get_settings

ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7


def create_access_token(*, user_id: str, email: str) -> str:
    settings = get_settings()
    secret = settings.auth_jwt_secret
    if not secret:
        raise RuntimeError("AUTH_JWT_SECRET is not configured")
    expire = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    secret = settings.auth_jwt_secret
    if not secret:
        raise RuntimeError("AUTH_JWT_SECRET is not configured")
    return jwt.decode(token, secret, algorithms=[ALGORITHM])
