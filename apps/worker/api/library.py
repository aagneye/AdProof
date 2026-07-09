"""Library API — GET /library paginated variants for the current user."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from config import get_settings
from db.models import Brief, Run, User, Variant
from db.session import get_db
from schemas import LibraryItem, LibraryResponse
from storage.b2_client import get_storage

router = APIRouter()


@router.get("", response_model=LibraryResponse)
def list_library(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    provider: str | None = None,
    brand: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = (
        db.query(Variant, Run, Brief)
        .join(Run, Variant.run_id == Run.id)
        .join(Brief, Run.brief_id == Brief.id)
        .filter(Brief.user_id == user.id)
        .order_by(Variant.created_at.desc())
    )
    if provider:
        q = q.filter(Variant.provider_summary.ilike(f"%{provider}%"))
    if brand:
        q = q.filter(Brief.brand_name.ilike(f"%{brand}%"))

    total = q.count()
    rows = q.offset((page - 1) * limit).limit(limit).all()
    storage = get_storage()
    settings = get_settings()

    items = []
    for variant, run, brief in rows:
        thumb_url = None
        if variant.thumbnail_key:
            thumb_url = storage.signed_url(variant.thumbnail_key)
            if thumb_url.startswith("/"):
                thumb_url = f"{settings.api_base_url.rstrip('/')}{thumb_url}"
        items.append(
            LibraryItem(
                variant_id=variant.id,
                run_id=run.id,
                brief_id=brief.id,
                brand_name=brief.brand_name,
                thumbnail_url=thumb_url,
                provider_summary=variant.provider_summary,
                sha256_hash=variant.sha256_hash,
                total_cost_usd=str(run.total_cost_usd) if run.total_cost_usd else None,
                created_at=variant.created_at,
            )
        )

    return LibraryResponse(items=items, page=page, limit=limit, total=total)
