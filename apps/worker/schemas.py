"""Pydantic schemas for API request/response."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CreateBriefRequest(BaseModel):
    brand_name: str = Field(..., min_length=1)
    brief_text: str = Field(..., min_length=1)
    reference_image_key: Optional[str] = None


class RunSummary(BaseModel):
    id: str
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    total_cost_usd: Optional[str] = None

    class Config:
        from_attributes = True


class BriefResponse(BaseModel):
    id: str
    user_id: str
    brand_name: str
    brief_text: str
    reference_image_key: Optional[str] = None
    status: str
    created_at: datetime
    run_id: Optional[str] = None
    latest_run: Optional[RunSummary] = None

    class Config:
        from_attributes = True


class RunStepResponse(BaseModel):
    id: str
    step_name: str
    provider: Optional[str] = None
    model: Optional[str] = None
    status: str
    fallback_triggered: bool
    cost_usd: Optional[str] = None
    latency_ms: Optional[int] = None
    manifest_key: Optional[str] = None
    asset_key: Optional[str] = None
    created_at: datetime

    @field_validator("cost_usd", mode="before")
    @classmethod
    def decimal_to_str(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        return str(v)

    class Config:
        from_attributes = True


class VariantResponse(BaseModel):
    id: str
    asset_key: str
    thumbnail_key: Optional[str] = None
    manifest_key: str
    sha256_hash: str
    provider_summary: Optional[str] = None
    selected: bool
    thumbnail_url: Optional[str] = None
    asset_url: Optional[str] = None

    class Config:
        from_attributes = True


class RunDetailResponse(BaseModel):
    id: str
    brief_id: str
    parent_run_id: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    total_cost_usd: Optional[str] = None
    steps: list[RunStepResponse] = []
    variants: list[VariantResponse] = []

    @field_validator("total_cost_usd", mode="before")
    @classmethod
    def run_cost_to_str(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        return str(v)

    class Config:
        from_attributes = True


class ForkRequest(BaseModel):
    overrides: dict = Field(default_factory=dict)


class VerifyResponse(BaseModel):
    match: bool
    expected_sha256: str
    actual_sha256: str
    manifest_key: str
    verified_at: datetime


class ManifestResponse(BaseModel):
    manifest_key: str
    signed_url: str
    expires_at: datetime


class LibraryItem(BaseModel):
    variant_id: str
    run_id: str
    brief_id: str
    brand_name: str
    thumbnail_url: Optional[str] = None
    provider_summary: Optional[str] = None
    sha256_hash: str
    total_cost_usd: Optional[str] = None
    created_at: datetime


class LibraryResponse(BaseModel):
    items: list[LibraryItem]
    page: int
    limit: int
    total: int
