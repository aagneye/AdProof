"""Demo pipeline — simulates all 5 steps without external AI APIs."""

import io
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Callable

from manifest.builder import (
    build_run_manifest,
    build_step_manifest,
    build_variant_manifest,
    sha256_hex,
)
from pipeline.fallback_config import FALLBACK_CHAINS
from storage.b2_client import StorageClient
from storage.key_layout import (
    run_manifest_key,
    step_asset_key,
    step_manifest_key,
    variant_final_key,
    variant_manifest_key,
    variant_thumbnail_key,
)

STEP_COSTS = {
    "storyboard": "0.0500",
    "animate": "0.4500",
    "voiceover": "0.0800",
    "score": "0.0600",
    "compose": "0.0200",
}

ANIMATE_MODELS = [
    "kling-image2video-v2.1-master",
    "wan2.6-i2v",
    "pixverse-v5.6-i2v",
]


def _make_png(brand_name: str, brief_text: str) -> bytes:
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (1280, 720), color=(20, 24, 40))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(40, 40), (1240, 680)], outline=(99, 102, 241), width=4)
        draw.text((80, 80), brand_name[:40], fill=(255, 255, 255))
        draw.text((80, 140), brief_text[:120], fill=(200, 200, 220))
        draw.text((80, 600), "AdProof Demo Storyboard", fill=(129, 140, 248))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        # Minimal 1x1 PNG
        return (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx"
            b"\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01\x00\x05\xfe\xd4\xef\x00\x00\x00\x00IEND\xaeB`\x82"
        )


def _make_mp4(output_path: str, label: str) -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=0x312e81:s=1280x720:d=4",
                "-vf",
                f"drawtext=text='{label[:30]}':fontsize=36:fontcolor=white:x=80:y=80",
                "-c:v",
                "libx264",
                "-t",
                "4",
                "-pix_fmt",
                "yuv420p",
                output_path,
            ],
            capture_output=True,
            check=False,
        )
        try:
            return open(output_path, "rb").read()
        except OSError:
            pass
  # Tiny placeholder if ffmpeg unavailable
    return b"ADPROOF_DEMO_VIDEO_PLACEHOLDER"


def _make_audio_placeholder() -> bytes:
    return b"ID3\x04\x00\x00\x00\x00\x00\x00ADPROOF_DEMO_AUDIO"


def run_demo_pipeline(
    *,
    brief_id: str,
    run_id: str,
    brief_text: str,
    brand_name: str,
    storage: StorageClient,
    on_step_complete: Callable[[dict], None],
    fork_override: dict | None = None,
) -> dict:
    """Execute demo pipeline; returns variant info dict."""
    step_manifests = []
    animate_model = ANIMATE_MODELS[0]
    if fork_override and "animate" in fork_override:
        animate_model = fork_override["animate"].get("model", animate_model)

    # --- storyboard ---
    t0 = time.time()
    step_id = str(uuid.uuid4())
    png = _make_png(brand_name, brief_text)
    asset_key = step_asset_key(run_id, "storyboard", step_id, "png")
    manifest_key = step_manifest_key(run_id, "storyboard", step_id)
    storage.upload(asset_key, png, "image/png")
    manifest = build_step_manifest(
        run_id=run_id,
        step_id=step_id,
        step_name="storyboard",
        provider="gmicloud",
        model="seedream-5.0-lite",
        asset_bytes=png,
    )
    storage.upload_json(manifest_key, manifest)
    step_manifests.append(manifest)
    latency = int((time.time() - t0) * 1000)
    on_step_complete(
        {
            "step_name": "storyboard",
            "provider": "gmicloud",
            "model": "seedream-5.0-lite",
            "status": "succeeded",
            "fallback_triggered": False,
            "cost_usd": STEP_COSTS["storyboard"],
            "latency_ms": latency,
            "manifest_key": manifest_key,
            "asset_key": asset_key,
        }
    )

    # --- animate (concurrent fan-out demo: pick first model) ---
    t0 = time.time()
    step_id = str(uuid.uuid4())
    tmp_mp4 = Path(tempfile.gettempdir()) / f"adproof_{run_id}_animate.mp4"
    mp4 = _make_mp4(str(tmp_mp4), brand_name)
    asset_key = step_asset_key(run_id, "animate", step_id, "mp4", animate_model)
    manifest_key = step_manifest_key(run_id, "animate", step_id, animate_model)
    storage.upload(asset_key, mp4, "video/mp4")
    fallback = animate_model != ANIMATE_MODELS[0]
    manifest = build_step_manifest(
        run_id=run_id,
        step_id=step_id,
        step_name="animate",
        provider="gmicloud",
        model=animate_model,
        asset_bytes=mp4,
        fallback_triggered=fallback,
        extra={"concurrent_models": ANIMATE_MODELS, "selected_model": animate_model},
    )
    storage.upload_json(manifest_key, manifest)
    step_manifests.append(manifest)
    latency = int((time.time() - t0) * 1000)
    on_step_complete(
        {
            "step_name": "animate",
            "provider": "gmicloud",
            "model": animate_model,
            "status": "fallback_used" if fallback else "succeeded",
            "fallback_triggered": fallback,
            "cost_usd": STEP_COSTS["animate"],
            "latency_ms": latency,
            "manifest_key": manifest_key,
            "asset_key": asset_key,
        }
    )

    # --- voiceover ---
    t0 = time.time()
    step_id = str(uuid.uuid4())
    audio = _make_audio_placeholder()
    asset_key = step_asset_key(run_id, "voiceover", step_id, "mp3")
    manifest_key = step_manifest_key(run_id, "voiceover", step_id)
    storage.upload(asset_key, audio, "audio/mpeg")
    manifest = build_step_manifest(
        run_id=run_id,
        step_id=step_id,
        step_name="voiceover",
        provider="elevenlabs",
        model="eleven_multilingual_v2",
        asset_bytes=audio,
    )
    storage.upload_json(manifest_key, manifest)
    step_manifests.append(manifest)
    latency = int((time.time() - t0) * 1000)
    on_step_complete(
        {
            "step_name": "voiceover",
            "provider": "elevenlabs",
            "model": "eleven_multilingual_v2",
            "status": "succeeded",
            "fallback_triggered": False,
            "cost_usd": STEP_COSTS["voiceover"],
            "latency_ms": latency,
            "manifest_key": manifest_key,
            "asset_key": asset_key,
        }
    )

    # --- score ---
    t0 = time.time()
    step_id = str(uuid.uuid4())
    score = _make_audio_placeholder()
    asset_key = step_asset_key(run_id, "score", step_id, "mp3")
    manifest_key = step_manifest_key(run_id, "score", step_id)
    storage.upload(asset_key, score, "audio/mpeg")
    manifest = build_step_manifest(
        run_id=run_id,
        step_id=step_id,
        step_name="score",
        provider="stability-audio",
        model="stable-audio-2.0",
        asset_bytes=score,
    )
    storage.upload_json(manifest_key, manifest)
    step_manifests.append(manifest)
    latency = int((time.time() - t0) * 1000)
    on_step_complete(
        {
            "step_name": "score",
            "provider": "stability-audio",
            "model": "stable-audio-2.0",
            "status": "succeeded",
            "fallback_triggered": False,
            "cost_usd": STEP_COSTS["score"],
            "latency_ms": latency,
            "manifest_key": manifest_key,
            "asset_key": asset_key,
        }
    )

    # --- compose ---
    t0 = time.time()
    variant_id = str(uuid.uuid4())
    final_bytes = mp4  # demo: use animate output as final
    final_key = variant_final_key(run_id, variant_id)
    thumb_key = variant_thumbnail_key(run_id, variant_id)
    storage.upload(final_key, final_bytes, "video/mp4")
    storage.upload(thumb_key, png, "image/jpeg")

    run_man = build_run_manifest(run_id=run_id, step_manifests=step_manifests)
    storage.upload_json(run_manifest_key(run_id), run_man)

    provider_summary = f"{animate_model.split('-')[0]} + elevenlabs + stability-audio"
    variant_man = build_variant_manifest(
        run_id=run_id,
        variant_id=variant_id,
        final_bytes=final_bytes,
        run_manifest=run_man,
        provider_summary=provider_summary,
    )
    var_manifest_key = variant_manifest_key(run_id, variant_id)
    storage.upload_json(var_manifest_key, variant_man)

    step_id = str(uuid.uuid4())
    compose_manifest_key = step_manifest_key(run_id, "compose", step_id)
    compose_manifest = build_step_manifest(
        run_id=run_id,
        step_id=step_id,
        step_name="compose",
        provider="ffmpeg",
        model="compose",
        asset_bytes=final_bytes,
    )
    storage.upload_json(compose_manifest_key, compose_manifest)
    latency = int((time.time() - t0) * 1000)
    on_step_complete(
        {
            "step_name": "compose",
            "provider": "ffmpeg",
            "model": "compose",
            "status": "succeeded",
            "fallback_triggered": False,
            "cost_usd": STEP_COSTS["compose"],
            "latency_ms": latency,
            "manifest_key": compose_manifest_key,
            "asset_key": final_key,
        }
    )

    return {
        "variant_id": variant_id,
        "asset_key": final_key,
        "thumbnail_key": thumb_key,
        "manifest_key": var_manifest_key,
        "sha256_hash": sha256_hex(final_bytes),
        "provider_summary": provider_summary,
        "total_cost_usd": str(
            round(sum(float(STEP_COSTS[s]) for s in STEP_COSTS), 4)
        ),
    }
