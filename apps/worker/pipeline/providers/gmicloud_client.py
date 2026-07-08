"""GMI Cloud request-queue API client — real HTTP calls with polling."""

import logging
import time
from typing import Any

import httpx

from pipeline.keys import log_key_usage

logger = logging.getLogger("adproof.gmicloud")

BASE_URL = "https://console.gmicloud.ai/api/v1/ie/requestqueue/apikey"
POLL_INTERVAL_SEC = 3
DEFAULT_TIMEOUT_SEC = 600


class GMICloudClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or log_key_usage("gmicloud", "GMICLOUD_API_KEY", "GMI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GMICLOUD_API_KEY is required for live pipeline calls")
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def submit(self, model: str, payload: dict[str, Any]) -> str:
        start = time.monotonic()
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{BASE_URL}/requests",
                headers=self._headers,
                json={"model": model, "payload": payload},
            )
            resp.raise_for_status()
            data = resp.json()
        request_id = data.get("id") or data.get("request_id")
        if not request_id:
            raise RuntimeError(f"GMI Cloud submit returned no request id: {data}")
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.info("GMI submit model=%s request_id=%s latency_ms=%d", model, request_id, latency_ms)
        return str(request_id)

    def poll_until_done(self, request_id: str, timeout_sec: int = DEFAULT_TIMEOUT_SEC) -> dict:
        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            with httpx.Client(timeout=60) as client:
                resp = client.get(
                    f"{BASE_URL}/requests/{request_id}",
                    headers=self._headers,
                )
                resp.raise_for_status()
                data = resp.json()
            status = (data.get("status") or "").lower()
            if status in ("success", "succeeded", "completed", "finished"):
                return data
            if status in ("failed", "error", "cancelled"):
                raise RuntimeError(f"GMI Cloud request {request_id} failed: {data}")
            time.sleep(POLL_INTERVAL_SEC)
        raise TimeoutError(f"GMI Cloud request {request_id} timed out after {timeout_sec}s")

    def download_artifact(self, url: str) -> bytes:
        start = time.monotonic()
        with httpx.Client(timeout=120, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.content
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.info("GMI download %d bytes latency_ms=%d", len(data), latency_ms)
        return data

    def run_image(self, model: str, prompt: str, timeout_sec: int = 300) -> tuple[bytes, dict]:
        start = time.monotonic()
        request_id = self.submit(
            model,
            {"prompt": prompt, "aspect_ratio": "16:9", "image_size": "1K"},
        )
        result = self.poll_until_done(request_id, timeout_sec=timeout_sec)
        urls = self._extract_urls(result)
        if not urls:
            raise RuntimeError(f"No artifact URLs in GMI response: {result}")
        asset_bytes = self.download_artifact(urls[0])
        latency_ms = int((time.monotonic() - start) * 1000)
        meta = {
            "request_id": request_id,
            "provider_response": result,
            "latency_ms": latency_ms,
            "artifact_url": urls[0],
        }
        return asset_bytes, meta

    def run_image_to_video(
        self,
        model: str,
        prompt: str,
        image_url: str,
        timeout_sec: int = 600,
    ) -> tuple[bytes, dict]:
        start = time.monotonic()
        payload: dict[str, Any] = {
            "prompt": prompt,
            "image": image_url,
            "aspect_ratio": "16:9",
            "duration": 5,
        }
        request_id = self.submit(model, payload)
        result = self.poll_until_done(request_id, timeout_sec=timeout_sec)
        urls = self._extract_urls(result)
        if not urls:
            raise RuntimeError(f"No video URLs in GMI response: {result}")
        asset_bytes = self.download_artifact(urls[0])
        latency_ms = int((time.monotonic() - start) * 1000)
        meta = {
            "request_id": request_id,
            "provider_response": result,
            "latency_ms": latency_ms,
            "artifact_url": urls[0],
        }
        return asset_bytes, meta

    def run_audio(self, model: str, prompt: str, timeout_sec: int = 300) -> tuple[bytes, dict]:
        start = time.monotonic()
        request_id = self.submit(model, {"prompt": prompt})
        result = self.poll_until_done(request_id, timeout_sec=timeout_sec)
        urls = self._extract_urls(result)
        if not urls:
            raise RuntimeError(f"No audio URLs in GMI response: {result}")
        asset_bytes = self.download_artifact(urls[0])
        latency_ms = int((time.monotonic() - start) * 1000)
        meta = {
            "request_id": request_id,
            "provider_response": result,
            "latency_ms": latency_ms,
            "artifact_url": urls[0],
        }
        return asset_bytes, meta

    def get_upload_url(self, file_type: str = "png") -> tuple[str, str]:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{BASE_URL}/upload-url",
                headers=self._headers,
                json={"file_type": file_type},
            )
            resp.raise_for_status()
            data = resp.json()
        return data["upload_url"], data["public_url"]

    def upload_bytes(self, data: bytes, file_type: str = "png") -> str:
        upload_url, public_url = self.get_upload_url(file_type)
        with httpx.Client(timeout=120) as client:
            resp = client.put(upload_url, content=data)
            resp.raise_for_status()
        return public_url

    @staticmethod
    def _extract_urls(result: dict) -> list[str]:
        urls: list[str] = []
        outcome = result.get("outcome") or {}
        if isinstance(outcome.get("media_urls"), list):
            urls.extend(outcome["media_urls"])
        if outcome.get("url"):
            urls.append(outcome["url"])
        if result.get("artifact_url"):
            urls.append(result["artifact_url"])
        return [u for u in urls if u]
