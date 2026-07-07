"""Backblaze B2 client with local filesystem fallback."""

import json
from functools import lru_cache

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from config import get_settings
from storage.local_storage import LocalStorage


class StorageClient:
    """Unified storage: B2 when configured, else local disk."""

    def __init__(self):
        self.settings = get_settings()
        self.local = LocalStorage()
        self._s3 = None
        if self.settings.has_b2_credentials:
            self._s3 = boto3.client(
                "s3",
                endpoint_url=self.settings.b2_endpoint,
                aws_access_key_id=self.settings.b2_key_id,
                aws_secret_access_key=self.settings.b2_app_key,
                config=Config(signature_version="s3v4"),
            )

    @property
    def uses_b2(self) -> bool:
        return self._s3 is not None

    def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        object_lock: bool = False,
    ) -> str:
        if self._s3:
            extra = {"ContentType": content_type}
            if object_lock:
                extra["ObjectLockMode"] = "GOVERNANCE"
                extra["ObjectLockRetainUntilDate"] = "2030-01-01T00:00:00Z"
            try:
                self._s3.put_object(
                    Bucket=self.settings.b2_bucket_name,
                    Key=key,
                    Body=data,
                    **extra,
                )
                return key
            except ClientError:
                pass
        return self.local.upload(key, data, content_type)

    def download(self, key: str) -> bytes:
        if self._s3:
            try:
                resp = self._s3.get_object(
                    Bucket=self.settings.b2_bucket_name, Key=key
                )
                return resp["Body"].read()
            except ClientError:
                pass
        return self.local.download(key)

    def exists(self, key: str) -> bool:
        if self.local.exists(key):
            return True
        if self._s3:
            try:
                self._s3.head_object(Bucket=self.settings.b2_bucket_name, Key=key)
                return True
            except ClientError:
                return False
        return False

    def signed_url(self, key: str, expires_in: int = 3600) -> str:
        if self._s3:
            try:
                return self._s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.settings.b2_bucket_name, "Key": key},
                    ExpiresIn=expires_in,
                )
            except ClientError:
                pass
        return self.local.signed_url(key, expires_in)

    def upload_json(self, key: str, payload: dict, object_lock: bool = True) -> str:
        data = json.dumps(payload, indent=2, sort_keys=True).encode()
        return self.upload(key, data, "application/json", object_lock=object_lock)

    def delete(self, key: str):
        if self.local.exists(key):
            self.local.delete(key)
        if self._s3:
            try:
                self._s3.delete_object(Bucket=self.settings.b2_bucket_name, Key=key)
            except ClientError:
                pass


@lru_cache
def get_storage() -> StorageClient:
    return StorageClient()
