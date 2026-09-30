"""
Location model.
Canonical physical geographic entity and postal address authority.
Owns all spatial coordinates for POIs and Accommodations.
"""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List
from sqlalchemy import CheckConstraint, DateTime, Float, Index, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.sql.base import Base

if TYPE_CHECKING:
    from app.models.sql.poi import POI
    from app.models.sql.accommodation import Accommodation
    from app.models.sql.transport import TransportOption
    from app.models.sql.trip import Trip
    from app.models.sql.interaction import Offer


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        CheckConstraint("latitude >= -90.0 AND latitude <= 90.0", name="ck_locations_latitude_range"),
        CheckConstraint("longitude >= -180.0 AND longitude <= 180.0", name="ck_locations_longitude_range"),
        Index("idx_locations_lat_lon", "latitude", "longitude"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    city: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    canonical_name: Mapped[str] = mapped_column(String(128), server_default="", default="", nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(128), default="", nullable=False, index=True)
    union_territory: Mapped[str] = mapped_column(String(128), server_default="", default="", nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(128), server_default="", default="", nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    postal_code: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    
    category: Mapped[str] = mapped_column(String(128), server_default="", default="", nullable=False, index=True)
    subcategories: Mapped[list] = mapped_column(JSONB, server_default='[]', default=list, nullable=False)
    aliases: Mapped[list] = mapped_column(JSONB, server_default='[]', default=list, nullable=False)
    description: Mapped[str] = mapped_column(String, server_default="", default="", nullable=False)
    best_time_to_visit: Mapped[str] = mapped_column(String(255), server_default="", default="", nullable=False)
    image: Mapped[str] = mapped_column(String(1024), server_default="", default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", default=True, nullable=False)
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

    # Geographic Hierarchy
    location_type: Mapped[str] = mapped_column(String(64), server_default="poi", default="poi", nullable=False, index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    parent: Mapped["Location | None"] = relationship("Location", remote_side=[id], back_populates="children")
    children: Mapped[List["Location"]] = relationship("Location", back_populates="parent", cascade="all, delete")

    pois: Mapped[List["POI"]] = relationship(
        "POI",
        back_populates="location",
    )
    accommodations: Mapped[List["Accommodation"]] = relationship(
        "Accommodation",
        back_populates="location",
    )
    origin_transports: Mapped[List["TransportOption"]] = relationship(
        "TransportOption",
        foreign_keys="[TransportOption.origin_location_id]",
        back_populates="origin_location",
    )
    destination_transports: Mapped[List["TransportOption"]] = relationship(
        "TransportOption",
        foreign_keys="[TransportOption.destination_location_id]",
        back_populates="destination_location",
    )
    trips: Mapped[List["Trip"]] = relationship(
        "Trip",
        back_populates="location",
    )
    offers: Mapped[List["Offer"]] = relationship(
        "Offer",
        back_populates="location",
        cascade="all, delete-orphan",
    )
