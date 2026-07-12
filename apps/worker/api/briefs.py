"""Briefs API — POST /briefs, GET /briefs, GET /briefs/:id."""

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from db.models import Brief, Run, User
from db.session import get_db
from pipeline.runner import execute_run
from schemas import BriefListResponse, BriefResponse, CreateBriefRequest, RunSummary
from services.access import get_user_brief
from services.activity import log_activity

router = APIRouter()


def _run_in_background(brief_id, run_id):
    from db.session import SessionLocal

    db = SessionLocal()
    try:
        execute_run(db, brief_id, run_id)
    finally:
        db.close()


def _brief_response(brief: Brief, latest_run: Run | None) -> BriefResponse:
    latest = None
    if latest_run:
        latest = RunSummary(
            id=latest_run.id,
            status=latest_run.status,
            started_at=latest_run.started_at,
            finished_at=latest_run.finished_at,
            total_cost_usd=str(latest_run.total_cost_usd) if latest_run.total_cost_usd else None,
        )
    return BriefResponse(
        id=brief.id,
        user_id=brief.user_id,
        brand_name=brief.brand_name,
        brief_text=brief.brief_text,
        reference_image_key=brief.reference_image_key,
        status=brief.status,
        created_at=brief.created_at,
        run_id=latest_run.id if latest_run else None,
        latest_run=latest,
    )


@router.get("", response_model=BriefListResponse)
def list_briefs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    briefs = (
        db.query(Brief)
        .filter(Brief.user_id == user.id)
        .order_by(Brief.created_at.desc())
        .limit(50)
        .all()
    )
    items = []
    for brief in briefs:
        latest_run = (
            db.query(Run)
            .filter(Run.brief_id == brief.id)
            .order_by(Run.created_at.desc())
            .first()
        )
        items.append(_brief_response(brief, latest_run))
    return BriefListResponse(items=items, total=len(items))


@router.post("", response_model=BriefResponse, status_code=201)
def create_brief(
    body: CreateBriefRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    brief = Brief(
        user_id=user.id,
        brand_name=body.brand_name,
        brief_text=body.brief_text,
        reference_image_key=body.reference_image_key,
        status="pending",
    )
    db.add(brief)
    db.commit()
    db.refresh(brief)

    run = Run(brief_id=brief.id, status="queued")
    db.add(run)
    db.commit()
    db.refresh(run)

    background_tasks.add_task(_run_in_background, brief.id, run.id)

    log_activity(
        db,
        user_id=user.id,
        action="brief.create",
        resource_type="brief",
        resource_id=brief.id,
        metadata={"brand_name": brief.brand_name, "run_id": run.id},
    )

    return _brief_response(brief, run)


@router.get("/{brief_id}", response_model=BriefResponse)
def get_brief(
    brief_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    brief = get_user_brief(db, brief_id, user)
    latest_run = (
        db.query(Run)
        .filter(Run.brief_id == brief.id)
        .order_by(Run.created_at.desc())
        .first()
    )
    return _brief_response(brief, latest_run)
