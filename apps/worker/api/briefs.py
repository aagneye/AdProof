"""Briefs API — POST /briefs, GET /briefs/:id."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from db.models import Brief, Run
from db.session import get_db
from pipeline.runner import execute_run
from schemas import BriefResponse, CreateBriefRequest, RunSummary
from services.seed import get_or_create_demo_user

router = APIRouter()


def _run_in_background(brief_id, run_id):
    from db.session import SessionLocal

    db = SessionLocal()
    try:
        execute_run(db, brief_id, run_id)
    finally:
        db.close()


@router.post("", response_model=BriefResponse, status_code=201)
def create_brief(
    body: CreateBriefRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = get_or_create_demo_user(db)
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

    return BriefResponse(
        id=brief.id,
        user_id=brief.user_id,
        brand_name=brief.brand_name,
        brief_text=brief.brief_text,
        reference_image_key=brief.reference_image_key,
        status=brief.status,
        created_at=brief.created_at,
        run_id=run.id,
    )


@router.get("/{brief_id}", response_model=BriefResponse)
def get_brief(brief_id: str, db: Session = Depends(get_db)):
    brief = db.query(Brief).filter(Brief.id == brief_id).first()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")

    latest_run = (
        db.query(Run)
        .filter(Run.brief_id == brief.id)
        .order_by(Run.created_at.desc())
        .first()
    )
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
