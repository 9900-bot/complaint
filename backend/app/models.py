from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Text, Float, Integer, Boolean, DateTime, LargeBinary, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def uid():
    return str(uuid4())


class Region(Base):
    __tablename__ = 'geographic_regions'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    stable_code: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    region_type: Mapped[str] = mapped_column(String, index=True)
    parent_region_id: Mapped[str | None] = mapped_column(ForeignKey('geographic_regions.id'), index=True)
    geometry_reference: Mapped[str] = mapped_column(String)
    dataset_version: Mapped[str] = mapped_column(String)


class Cluster(Base):
    __tablename__ = 'clusters'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    label: Mapped[str] = mapped_column(String)
    representative_text: Mapped[str] = mapped_column(Text)
    centroid_embedding: Mapped[bytes] = mapped_column(LargeBinary)
    embedding_dimension: Mapped[int] = mapped_column(Integer)
    embedding_model_version: Mapped[str] = mapped_column(String)
    complaint_count: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    __table_args__ = (CheckConstraint('complaint_count >= 0'),)


class Complaint(Base):
    __tablename__ = 'complaints'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String)
    original_text: Mapped[str] = mapped_column(Text)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    state_id: Mapped[str] = mapped_column(ForeignKey('geographic_regions.id'), index=True)
    district_id: Mapped[str | None] = mapped_column(ForeignKey('geographic_regions.id'), index=True)
    constituency_id: Mapped[str | None] = mapped_column(ForeignKey('geographic_regions.id'), index=True)
    cluster_id: Mapped[str | None] = mapped_column(ForeignKey('clusters.id'), index=True)
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary)
    embedding_dimension: Mapped[int | None] = mapped_column(Integer)
    embedding_model_version: Mapped[str | None] = mapped_column(String)
    internal_processing_state: Mapped[str] = mapped_column(String, default='pending', index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    geographic_ambiguity: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        CheckConstraint('latitude >= -90 AND latitude <= 90'),
        CheckConstraint('longitude >= -180 AND longitude <= 180'),
        Index('ix_complaints_work', 'internal_processing_state', 'next_attempt_at'),
    )


class ClusterMerge(Base):
    __tablename__ = 'cluster_merges'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    source_cluster_id: Mapped[str] = mapped_column(ForeignKey('clusters.id'), unique=True)
    target_cluster_id: Mapped[str] = mapped_column(ForeignKey('clusters.id'), index=True)
    merge_score: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String)
    merged_at: Mapped[datetime] = mapped_column(DateTime, default=now)
