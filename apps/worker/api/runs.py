"""Runs API — GET /runs/:id, replay, fork, verify, manifest."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from config import get_settings
from db.models import Run, User, Variant
from db.session import get_db
from manifest.replay import execute_fork
from manifest.verify import verify_run_manifest
from schemas import (
    ForkRequest,
    ManifestResponse,
    RunDetailResponse,
    RunStepResponse,
    RunSummary,
    VariantResponse,
    VerifyResponse,
)
from services.access import get_user_run
from services.activity import log_activity
from storage.b2_client import get_storage

router = APIRouter()


def _variant_urls(variant: Variant) -> tuple[str | None, str | None]:
    storage = get_storage()
    settings = get_settings()
    thumb = storage.signed_url(variant.thumbnail_key) if variant.thumbnail_key else None
    asset = storage.signed_url(variant.asset_key)

    def _abs(url: str | None) -> str | None:
        if url and url.startswith("/"):
            return f"{settings.api_base_url.rstrip('/')}{url}"
        return url

    return _abs(thumb), _abs(asset)


@router.get("/{run_id}", response_model=RunDetailResponse)
def get_run(
    run_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run = get_user_run(db, run_id, user)

    steps = [
        RunStepResponse.model_validate(s)
        for s in sorted(run.steps, key=lambda x: x.created_at)
    ]
    variants = []
    for v in run.variants:
        thumb, asset = _variant_urls(v)
        vr = VariantResponse.model_validate(v)
        vr.thumbnail_url = thumb
        vr.asset_url = asset
        variants.append(vr)

    return RunDetailResponse(
        id=run.id,
        brief_id=run.brief_id,
        parent_run_id=run.parent_run_id,
        status=run.status,
        started_at=run.started_at,
        finished_at=run.finished_at,
        total_cost_usd=str(run.total_cost_usd) if run.total_cost_usd else None,
        steps=steps,
        variants=variants,
    )


def _run_child_background(brief_id: str, run_id: str, overrides: dict):
    from db.session import SessionLocal

    db = SessionLocal()
    try:
        execute_fork(db, brief_id, run_id, fork_override=overrides or None)
    finally:
        db.close()


@router.post("/{run_id}/replay", response_model=RunSummary, status_code=201)
def replay_run(
    run_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    parent = get_user_run(db, run_id, user)

    child = Run(brief_id=parent.brief_id, parent_run_id=parent.id, status="queued")
    db.add(child)
    db.commit()
    db.refresh(child)
    background_tasks.add_task(_run_child_background, child.brief_id, child.id, {})
    log_activity(
        db,
        user_id=user.id,
        action="run.replay",
        resource_type="run",
        resource_id=child.id,
        metadata={"parent_run_id": parent.id},
    )
    return RunSummary(id=child.id, status=child.status)


@router.post("/{run_id}/fork", response_model=RunSummary, status_code=201)
def fork_run(
    run_id: str,
    body: ForkRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    parent = get_user_run(db, run_id, user)

    child = Run(brief_id=parent.brief_id, parent_run_id=parent.id, status="queued")
    db.add(child)
    db.commit()
    db.refresh(child)
    background_tasks.add_task(_run_child_background, child.brief_id, child.id, body.overrides)
    log_activity(
        db,
        user_id=user.id,
        action="run.fork",
        resource_type="run",
        resource_id=child.id,
        metadata={"parent_run_id": parent.id, "overrides": body.overrides},
    )
    return RunSummary(id=child.id, status=child.status)


@router.get("/{run_id}/manifest", response_model=ManifestResponse)
def get_manifest(
    run_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_user_run(db, run_id, user)
    variant = (
        db.query(Variant).filter(Variant.run_id == run_id).order_by(Variant.created_at).first()
    )
    if not variant:
        raise HTTPException(status_code=404, detail="No manifest for run")

    storage = get_storage()
    settings = get_settings()
    url = storage.signed_url(variant.manifest_key)
    if url.startswith("/"):
        url = f"{settings.api_base_url.rstrip('/')}{url}"
    return ManifestResponse(
        manifest_key=variant.manifest_key,
        signed_url=url,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


@router.get("/{run_id}/verify", response_model=VerifyResponse)
def verify_run(
    run_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_user_run(db, run_id, user)
    try:
        result = verify_run_manifest(db, run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    log_activity(
        db,
        user_id=user.id,
        action="run.verify",
        resource_type="run",
        resource_id=run_id,
        metadata={"match": result.get("match")},
    )
    return VerifyResponse(**result)
