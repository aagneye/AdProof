"""SQLAlchemy models — see docs/database.md for full schema."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def _uuid_str() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    email = Column(Text, unique=True, nullable=False)
    google_id = Column(Text, unique=True, nullable=True)
    name = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    briefs = relationship("Brief", back_populates="user")


class Brief(Base):
    __tablename__ = "briefs"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    brand_name = Column(Text, nullable=False)
    brief_text = Column(Text, nullable=False)
    reference_image_key = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="briefs")
    runs = relationship("Run", back_populates="brief")


class Run(Base):
    __tablename__ = "runs"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    brief_id = Column(String(36), ForeignKey("briefs.id"), nullable=False)
    parent_run_id = Column(String(36), ForeignKey("runs.id"), nullable=True)
    status = Column(String(20), nullable=False, default="queued")
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    total_cost_usd = Column(Numeric(10, 4), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    brief = relationship("Brief", back_populates="runs")
    parent_run = relationship("Run", remote_side=[id])
    steps = relationship("RunStep", back_populates="run")
    variants = relationship("Variant", back_populates="run")


class RunStep(Base):
    __tablename__ = "run_steps"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    run_id = Column(String(36), ForeignKey("runs.id"), nullable=False)
    step_name = Column(String(50), nullable=False)
    provider = Column(Text, nullable=True)
    model = Column(Text, nullable=True)
    status = Column(String(20), nullable=False)
    fallback_triggered = Column(Boolean, nullable=False, default=False)
    cost_usd = Column(Numeric(10, 4), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    manifest_key = Column(Text, nullable=True)
    asset_key = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    run = relationship("Run", back_populates="steps")


class Variant(Base):
    __tablename__ = "variants"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    run_id = Column(String(36), ForeignKey("runs.id"), nullable=False)
    asset_key = Column(Text, nullable=False)
    thumbnail_key = Column(Text, nullable=True)
    manifest_key = Column(Text, nullable=False)
    sha256_hash = Column(Text, nullable=False)
    provider_summary = Column(Text, nullable=True)
    selected = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    run = relationship("Run", back_populates="variants")
