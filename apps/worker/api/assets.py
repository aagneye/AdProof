"""Serve local storage assets when B2 is not configured."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from config import get_settings
from storage.local_storage import LocalStorage

router = APIRouter()


@router.get("/{key:path}")
def serve_asset(key: str):
    settings = get_settings()
    storage = LocalStorage(settings.local_storage_path)
    path = storage._full_path(key)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(path)
