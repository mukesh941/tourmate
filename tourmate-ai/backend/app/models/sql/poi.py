"""
POI (Point of Interest) and OpeningHours models.
Sightseeing attractions without duplicated coordinates.
"""
import uuid
from datetime import datetime, time, timezone
from typing import TYPE_CHECKING, List
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.sql.base import Base

if TYPE_CHECKING:
    from app.models.sql.location import Location
    from app.models.sql.category import Category
    from app.models.sql.knowledge import KnowledgeChunk
    from app.models.sql.trip import POICluster
    from app.models.sql.itinerary import ItineraryStop
    from app.models.sql.media import POIImage
    from app.models.sql.interaction import Feedback, Offer


class POI(Base):
    __tablename__ = "pois"
    __table_args__ = (
        CheckConstraint("rating >= 0.0 AND rating <= 5.0", name="ck_pois_rating_range"),
        CheckConstraint("price_tier BETWEEN 1 AND 4", name="ck_pois_price_tier_range"),
        CheckConstraint("typical_visit_duration_minutes > 0", name="ck_pois_visit_duration_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    price_tier: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    typical_visit_duration_minutes: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    embedding = mapped_column(Vector(384), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    location: Mapped["Location"] = relationship("Location", back_populates="pois")
    category: Mapped["Category"] = relationship("Category", back_populates="pois")
    opening_hours: Mapped[List["OpeningHours"]] = relationship(
        "OpeningHours",
        back_populates="poi",
        cascade="all, delete-orphan",
    )
    knowledge_chunks: Mapped[List["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk",
        back_populates="poi",
    )
    clusters: Mapped[List["POICluster"]] = relationship(
        "POICluster",
        back_populates="poi",
    )
    itinerary_stops: Mapped[List["ItineraryStop"]] = relationship(
        "ItineraryStop",
        back_populates="poi",
    )
    poi_images: Mapped[List["POIImage"]] = relationship(
        "POIImage",
        back_populates="poi",
        cascade="all, delete-orphan",
    )
    feedback: Mapped[List["Feedback"]] = relationship(
        "Feedback",
        back_populates="poi",
    )
    offers: Mapped[List["Offer"]] = relationship(
        "Offer",
        back_populates="poi",
    )


class OpeningHours(Base):
    __tablename__ = "opening_hours"
    __table_args__ = (
        UniqueConstraint("poi_id", "day_of_week", name="uq_opening_hours_poi_day"),
        CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_opening_hours_day_of_week"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    poi_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pois.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    open_time: Mapped[time] = mapped_column(Time, nullable=False)
    close_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    poi: Mapped["POI"] = relationship("POI", back_populates="opening_hours")
