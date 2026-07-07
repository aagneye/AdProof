"""Local filesystem storage fallback when B2 is not configured."""

import os
from pathlib import Path

from config import get_settings


class LocalStorage:
    def __init__(self, base_path: str | None = None):
        settings = get_settings()
        self.base_path = Path(base_path or settings.local_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _full_path(self, key: str) -> Path:
        path = self.base_path / key.replace("/", os.sep)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream", **_kwargs):
        path = self._full_path(key)
        path.write_bytes(data)
        return key

    def download(self, key: str) -> bytes:
        return self._full_path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._full_path(key).exists()

    def signed_url(self, key: str, expires_in: int = 3600) -> str:
        return f"/assets/{key}"

    def delete(self, key: str):
        path = self._full_path(key)
        if path.exists():
            path.unlink()
