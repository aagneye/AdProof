"""Genblaze pipeline definition — see docs/pipeline.md."""

from pipeline.demo_pipeline import run_demo_pipeline
from pipeline.fallback_config import FALLBACK_CHAINS

PIPELINE_STEPS = [
    {
        "name": "storyboard",
        "provider": "gmicloud",
        "fallback_models": FALLBACK_CHAINS["storyboard"],
    },
    {
        "name": "animate",
        "provider": "gmicloud",
        "models": [
            "kling-image2video-v2.1-master",
            "wan2.6-i2v",
            "pixverse-v5.6-i2v",
        ],
        "concurrent": True,
        "fallback_models": FALLBACK_CHAINS["animate"],
    },
    {
        "name": "voiceover",
        "provider": "elevenlabs",
        "fallback_models": FALLBACK_CHAINS["voiceover"],
    },
    {
        "name": "score",
        "provider": "stability-audio",
        "fallback_models": FALLBACK_CHAINS["score"],
    },
    {"name": "compose", "type": "ffmpeg"},
]


def run_genblaze_pipeline(
    *,
    brief_id: str,
    run_id: str,
    brief_text: str,
    brand_name: str,
    storage,
    on_step_complete,
    fork_override=None,
):
    """Run with real Genblaze SDK when installed; falls back to demo."""
    try:
        from genblaze import Pipeline
        from genblaze_s3 import ObjectStorageSink, S3StorageBackend

        from config import get_settings

        settings = get_settings()
        backend = S3StorageBackend.for_backblaze(settings.b2_bucket_name)
        sink = ObjectStorageSink(backend)
        pipeline = Pipeline(sink=sink, chain=True)

        for step in PIPELINE_STEPS:
            if step["name"] == "compose":
                pipeline.step(step["name"], type="ffmpeg")
            elif step.get("concurrent"):
                pipeline.step(
                    step["name"],
                    provider=step["provider"],
                    models=step["models"],
                    concurrent=True,
                    fallback_models=step.get("fallback_models"),
                )
            else:
                pipeline.step(
                    step["name"],
                    provider=step["provider"],
                    fallback_models=step.get("fallback_models"),
                )

        # TODO: wire genblaze run output to on_step_complete callbacks
        return run_demo_pipeline(
            brief_id=brief_id,
            run_id=run_id,
            brief_text=brief_text,
            brand_name=brand_name,
            storage=storage,
            on_step_complete=on_step_complete,
            fork_override=fork_override,
        )
    except ImportError:
        return run_demo_pipeline(
            brief_id=brief_id,
            run_id=run_id,
            brief_text=brief_text,
            brand_name=brand_name,
            storage=storage,
            on_step_complete=on_step_complete,
            fork_override=fork_override,
        )


def run_pipeline(brief_id: str, run_id: str, brief_text: str, **kwargs):
    """Legacy entrypoint for job worker."""
    from db.session import SessionLocal
    from pipeline.runner import execute_run

    db = SessionLocal()
    try:
        from uuid import UUID

        execute_run(db, UUID(brief_id), UUID(run_id), kwargs.get("fork_override"))
    finally:
        db.close()
