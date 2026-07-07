"""Canonical B2 key naming — see docs/b2-storage.md."""


def brief_reference_key(brief_id: str, ext: str) -> str:
    return f"briefs/{brief_id}/reference-image.{ext}"


def step_asset_key(
    run_id: str, step_name: str, step_id: str, ext: str, model: str | None = None
) -> str:
    if model and step_name == "animate":
        return f"runs/{run_id}/steps/animate/{model}/{step_id}.{ext}"
    return f"runs/{run_id}/steps/{step_name}/{step_id}.{ext}"


def step_manifest_key(
    run_id: str, step_name: str, step_id: str, model: str | None = None
) -> str:
    if model and step_name == "animate":
        return f"runs/{run_id}/steps/animate/{model}/{step_id}.manifest.json"
    return f"runs/{run_id}/steps/{step_name}/{step_id}.manifest.json"


def variant_final_key(run_id: str, variant_id: str) -> str:
    return f"runs/{run_id}/variants/{variant_id}/final.mp4"


def variant_thumbnail_key(run_id: str, variant_id: str) -> str:
    return f"runs/{run_id}/variants/{variant_id}/thumbnail.jpg"


def variant_manifest_key(run_id: str, variant_id: str) -> str:
    return f"runs/{run_id}/variants/{variant_id}/manifest.json"


def run_manifest_key(run_id: str) -> str:
    return f"runs/{run_id}/run.manifest.json"


def pipeline_log_key(run_id: str) -> str:
    return f"logs/{run_id}/pipeline.log"
