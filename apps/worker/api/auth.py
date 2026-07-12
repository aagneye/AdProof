"""Auth API — Supabase OAuth user sync and JWT issuance."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.jwt import create_access_token
from auth.dependencies import get_current_user
from db.models import User
from db.session import get_db
from schemas import AuthResponse, SupabaseAuthRequest, UserResponse
from services.users import upsert_google_user

router = APIRouter()


@router.post("/supabase", response_model=AuthResponse)
def auth_supabase(body: SupabaseAuthRequest, db: Session = Depends(get_db)):
    user = upsert_google_user(
        db,
        email=body.email,
        google_id=body.provider_user_id,
        name=body.name,
        avatar_url=body.picture,
    )
    token = create_access_token(user_id=user.id, email=user.email)
    return AuthResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
    )


@router.get("/me", response_model=UserResponse)
def auth_me(user: User = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )
