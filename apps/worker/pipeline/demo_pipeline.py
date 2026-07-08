"""Mock pipeline — MOCK mode only. Never used in live mode."""

import hashlib
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
from pipeline.ffmpeg_utils import extract_thumbnail
from storage.b2_client import StorageClient
from storage.key_layout import (
    run_manifest_key,
    step_asset_key,
    step_manifest_key,
    variant_final_key,
    variant_manifest_key,
    variant_thumbnail_key,
)

ANIMATE_MODELS = [
    "kling-image2video-v2.1-master",
    "wan2.6-i2v",
    "pixverse-v5.6-i2v",
]


def _make_png(brand_name: str, brief_text: str, run_id: str) -> bytes:
    try:
        from PIL import Image, ImageDraw

        seed = int(hashlib.sha256(f"{run_id}:{brand_name}:{brief_text}".encode()).hexdigest()[:8], 16)
        r = 20 + (seed % 80)
        g = 24 + ((seed >> 8) % 80)
        b = 40 + ((seed >> 16) % 80)

        img = Image.new("RGB", (1280, 720), color=(r, g, b))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(40, 40), (1240, 680)], outline=(99, 102, 241), width=4)
        draw.text((80, 80), brand_name[:40], fill=(255, 255, 255))
        draw.text((80, 140), brief_text[:120], fill=(200, 200, 220))
        draw.text((80, 600), f"MOCK — run {run_id[:8]}", fill=(248, 113, 113))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        return hashlib.sha256(f"mock-png:{run_id}:{brand_name}".encode()).digest()


def _make_mp4(output_path: str, label: str, run_id: str) -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    color = run_id.replace("-", "")[:6]
    if ffmpeg:
        subprocess.run(
            [
                ffmpeg, "-y", "-f", "lavfi",
                "-i", f"color=c=0x{color}:s=1280x720:d=4",
                "-vf", f"drawtext=text='MOCK {label[:24]}':fontsize=36:fontcolor=white:x=80:y=80",
                "-c:v", "libx264", "-t", "4", "-pix_fmt", "yuv420p", output_path,
            ],
            capture_output=True, check=False,
        )
        try:
            return Path(output_path).read_bytes()
        except OSError:
            pass
    return hashlib.sha256(f"mock-video:{run_id}:{label}".encode()).digest() + b"MOCK_VIDEO"


def _make_audio_placeholder(run_id: str, step: str) -> bytes:
    digest = hashlib.sha256(f"mock-audio:{run_id}:{step}".encode()).digest()
    return b"ID3\x04\x00\x00\x00\x00\x00\x22" + digest


def run_mock_pipeline(
    *,
    brief_id: str,
    run_id: str,
    brief_text: str,
    brand_name: str,
    storage: StorageClient,
    on_step_complete: Callable[[dict], None],
    fork_override: dict | None = None,
) -> dict:
    """Execute MOCK pipeline — unique hashes per brief, clearly labeled."""
    step_manifests = []
    animate_model = ANIMATE_MODELS[0]
    if fork_override and "animate" in fork_override:
        animate_model = fork_override["animate"].get("model", animate_model)

    # storyboard
    t0 = time.monotonic()
    step_id = str(uuid.uuid4())
    png = _make_png(brand_name, brief_text, run_id)
    asset_key = step_asset_key(run_id, "storyboard", step_id, "png")
    manifest_key = step_manifest_key(run_id, "storyboard", step_id)
    storage.upload(asset_key, png, "image/png")
    manifest = build_step_manifest(
        run_id=run_id, step_id=step_id, step_name="storyboard",
        provider="gmicloud", model="seedream-5.0-lite", asset_bytes=png,
        extra={"pipeline_mode": "mock", "brief_id": brief_id},
    )
    storage.upload_json(manifest_key, manifest)
    step_manifests.append(manifest)
    on_step_complete({
        "step_name": "storyboard", "provider": "gmicloud", "model": "seedream-5.0-lite",
        "status": "succeeded", "fallback_triggered": False, "cost_usd": None,
        "latency_ms": int((time.monotonic() - t0) * 1000),
        "manifest_key": manifest_key, "asset_key": asset_key,
    })

    # animate
    t0 = time.monotonic()
    step_id = str(uuid.uuid4())
    tmp_mp4 = Path(tempfile.gettempdir()) / f"adproof_{run_id}_animate.mp4"
    mp4 = _make_mp4(str(tmp_mp4), brand_name, run_id)
    asset_key = step_asset_key(run_id, "animate", step_id, "mp4", animate_model)
    manifest_key = step_manifest_key(run_id, "animate", step_id, animate_model)
    storage.upload(asset_key, mp4, "video/mp4")
    fallback = animate_model != ANIMATE_MODELS[0]
    manifest = build_step_manifest(
        run_id=run_id, step_id=step_id, step_name="animate",
        provider="gmicloud", model=animate_model, asset_bytes=mp4,
        fallback_triggered=fallback,
        extra={"pipeline_mode": "mock", "concurrent_models": ANIMATE_MODELS},
    )
    storage.upload_json(manifest_key, manifest)
    step_manifests.append(manifest)
    on_step_complete({
        "step_name": "animate", "provider": "gmicloud", "model": animate_model,
        "status": "fallback_used" if fallback else "succeeded",
        "fallback_triggered": fallback, "cost_usd": None,
        "latency_ms": int((time.monotonic() - t0) * 1000),
        "manifest_key": manifest_key, "asset_key": asset_key,
    })

    # voiceover
    t0 = time.monotonic()
    step_id = str(uuid.uuid4())
    audio = _make_audio_placeholder(run_id, "voiceover")
    asset_key = step_asset_key(run_id, "voiceover", step_id, "mp3")
    manifest_key = step_manifest_key(run_id, "voiceover", step_id)
    storage.upload(asset_key, audio, "audio/mpeg")
    manifest = build_step_manifest(
        run_id=run_id, step_id=step_id, step_name="voiceover",
        provider="elevenlabs", model="eleven_multilingual_v2", asset_bytes=audio,
        extra={"pipeline_mode": "mock"},
    )
    storage.upload_json(manifest_key, manifest)
    step_manifests.append(manifest)
    on_step_complete({
        "step_name": "voiceover", "provider": "elevenlabs", "model": "eleven_multilingual_v2",
        "status": "succeeded", "fallback_triggered": False, "cost_usd": None,
        "latency_ms": int((time.monotonic() - t0) * 1000),
        "manifest_key": manifest_key, "asset_key": asset_key,
    })

    # score
    t0 = time.monotonic()
    step_id = str(uuid.uuid4())
    score = _make_audio_placeholder(run_id, "score")
    asset_key = step_asset_key(run_id, "score", step_id, "mp3")
    manifest_key = step_manifest_key(run_id, "score", step_id)
    storage.upload(asset_key, score, "audio/mpeg")
    manifest = build_step_manifest(
        run_id=run_id, step_id=step_id, step_name="score",
        provider="stability-audio", model="stable-audio-2.0", asset_bytes=score,
        extra={"pipeline_mode": "mock"},
    )
    storage.upload_json(manifest_key, manifest)
    step_manifests.append(manifest)
    on_step_complete({
        "step_name": "score", "provider": "stability-audio", "model": "stable-audio-2.0",
        "status": "succeeded", "fallback_triggered": False, "cost_usd": None,
        "latency_ms": int((time.monotonic() - t0) * 1000),
        "manifest_key": manifest_key, "asset_key": asset_key,
    })

    # compose
    t0 = time.monotonic()
    variant_id = str(uuid.uuid4())
    final_bytes = mp4
    final_key = variant_final_key(run_id, variant_id)
    thumb_key = variant_thumbnail_key(run_id, variant_id)
    storage.upload(final_key, final_bytes, "video/mp4")
    try:
        thumb_bytes = extract_thumbnail(final_bytes)
    except Exception:
        thumb_bytes = png
    storage.upload(thumb_key, thumb_bytes, "image/jpeg")

    run_man = build_run_manifest(run_id=run_id, step_manifests=step_manifests)
    run_man["pipeline_mode"] = "mock"
    storage.upload_json(run_manifest_key(run_id), run_man)

    provider_summary = f"{animate_model.split('-')[0]} + elevenlabs + stability-audio"
    variant_man = build_variant_manifest(
        run_id=run_id, variant_id=variant_id, final_bytes=final_bytes,
        run_manifest=run_man, provider_summary=provider_summary,
    )
    variant_man["pipeline_mode"] = "mock"
    var_manifest_key = variant_manifest_key(run_id, variant_id)
    storage.upload_json(var_manifest_key, variant_man)

    step_id = str(uuid.uuid4())
    compose_manifest_key = step_manifest_key(run_id, "compose", step_id)
    compose_manifest = build_step_manifest(
        run_id=run_id, step_id=step_id, step_name="compose",
        provider="ffmpeg", model="compose", asset_bytes=final_bytes,
        extra={"pipeline_mode": "mock"},
    )
    storage.upload_json(compose_manifest_key, compose_manifest)
    on_step_complete({
        "step_name": "compose", "provider": "ffmpeg", "model": "compose",
        "status": "succeeded", "fallback_triggered": False, "cost_usd": None,
        "latency_ms": int((time.monotonic() - t0) * 1000),
        "manifest_key": compose_manifest_key, "asset_key": final_key,
    })

    return {
        "variant_id": variant_id,
        "asset_key": final_key,
        "thumbnail_key": thumb_key,
        "manifest_key": var_manifest_key,
        "sha256_hash": sha256_hex(final_bytes),
        "provider_summary": provider_summary,
        "total_cost_usd": None,
        "pipeline_mode": "mock",
    }


# Backwards-compatible alias
run_demo_pipeline = run_mock_pipeline
