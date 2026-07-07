"""Pipeline runner — orchestrates execution and DB persistence."""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from config import get_settings
from db.models import Brief, Run, RunStep, Variant
from pipeline.demo_pipeline import run_demo_pipeline
from storage.b2_client import get_storage


def _record_step(db: Session, run_id: str, info: dict) -> None:
    step = RunStep(
        run_id=run_id,
        step_name=info["step_name"],
        provider=info.get("provider"),
        model=info.get("model"),
        status=info.get("status", "succeeded"),
        fallback_triggered=info.get("fallback_triggered", False),
        cost_usd=Decimal(info["cost_usd"]) if info.get("cost_usd") else None,
        latency_ms=info.get("latency_ms"),
        manifest_key=info.get("manifest_key"),
        asset_key=info.get("asset_key"),
    )
    db.add(step)
    db.commit()


def execute_run(db: Session, brief_id: str, run_id: str, fork_override: dict | None = None):
    """Run the pipeline for a brief/run pair; updates DB throughout."""
    settings = get_settings()
    storage = get_storage()

    brief = db.query(Brief).filter(Brief.id == brief_id).first()
    run = db.query(Run).filter(Run.id == run_id).first()
    if not brief or not run:
        return

    run.status = "running"
    run.started_at = datetime.now(timezone.utc)
    brief.status = "running"
    db.commit()

    def on_step(info: dict):
        _record_step(db, run_id, info)

    try:
        if settings.effective_demo_mode:
            result = run_demo_pipeline(
                brief_id=str(brief_id),
                run_id=str(run_id),
                brief_text=brief.brief_text,
                brand_name=brief.brand_name,
                storage=storage,
                on_step_complete=on_step,
                fork_override=fork_override,
            )
        else:
            from pipeline.ad_pipeline import run_genblaze_pipeline

            result = run_genblaze_pipeline(
                brief_id=str(brief_id),
                run_id=str(run_id),
                brief_text=brief.brief_text,
                brand_name=brief.brand_name,
                storage=storage,
                on_step_complete=on_step,
                fork_override=fork_override,
            )

        variant = Variant(
            run_id=run_id,
            asset_key=result["asset_key"],
            thumbnail_key=result.get("thumbnail_key"),
            manifest_key=result["manifest_key"],
            sha256_hash=result["sha256_hash"],
            provider_summary=result.get("provider_summary"),
            selected=False,
        )
        db.add(variant)
        run.status = "succeeded"
        run.finished_at = datetime.now(timezone.utc)
        run.total_cost_usd = Decimal(result.get("total_cost_usd", "0"))
        brief.status = "done"
        db.commit()
    except Exception:
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        brief.status = "failed"
        db.commit()
        raise
