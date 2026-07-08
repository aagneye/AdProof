"""Genblaze pipeline definition — live mode uses live_pipeline.py directly."""

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


def run_pipeline(brief_id: str, run_id: str, brief_text: str, **kwargs):
    """Legacy entrypoint for job worker."""
    from db.session import SessionLocal
    from pipeline.runner import execute_run

    db = SessionLocal()
    try:
        execute_run(db, brief_id, run_id, kwargs.get("fork_override"))
    finally:
        db.close()
