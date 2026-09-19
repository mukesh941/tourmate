"""
Location model.
Canonical physical geographic entity and postal address authority.
Owns all spatial coordinates for POIs and Accommodations.
"""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List
from sqlalchemy import CheckConstraint, DateTime, Float, Index, String
from sqlalchemy.dialects.postgresql import UUID
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
    state: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    country: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    postal_code: Mapped[str] = mapped_column(String(32), default="", nullable=False)
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
