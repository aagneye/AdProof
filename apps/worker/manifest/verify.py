"""Manifest verification — re-compute SHA-256 and compare."""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from db.models import Run, Variant
from manifest.builder import sha256_hex
from storage.b2_client import get_storage


def verify_run_manifest(db: Session, run_id: str) -> dict:
    storage = get_storage()
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise ValueError("Run not found")

    variant = (
        db.query(Variant).filter(Variant.run_id == run_id).order_by(Variant.created_at).first()
    )
    if not variant:
        raise ValueError("No variant found for run")

    manifest_bytes = storage.download(variant.manifest_key)
    manifest = json.loads(manifest_bytes)
    expected = manifest.get("sha256", variant.sha256_hash)

    final_bytes = storage.download(variant.asset_key)
    actual = sha256_hex(final_bytes)

    return {
        "match": expected == actual,
        "expected_sha256": expected,
        "actual_sha256": actual,
        "manifest_key": variant.manifest_key,
        "verified_at": datetime.now(timezone.utc),
    }
