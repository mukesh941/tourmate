"""
Accommodation model.
Lodging entities (hotels, hostels, dorms) that serve strictly as daily route anchors.
Coordinates referenced from physical locations entity.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.sql.base import Base

if TYPE_CHECKING:
    from app.models.sql.location import Location
    from app.models.sql.trip import TripAccommodation
    from app.models.sql.media import AccommodationImage
    from app.models.sql.interaction import Offer


class Accommodation(Base):
    __tablename__ = "accommodations"
    __table_args__ = (
        CheckConstraint(
            "type IN ('hotel', 'hostel', 'dorm', 'guesthouse', 'resort')",
            name="ck_accommodations_type",
        ),
        CheckConstraint(
            "budget_tier IN ('budget', 'moderate', 'luxury')",
            name="ck_accommodations_budget_tier",
        ),
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
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), default="hotel", nullable=False)
    budget_tier: Mapped[str] = mapped_column(String(32), default="moderate", nullable=False, index=True)
    price_per_night: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    external_booking_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
    location: Mapped["Location"] = relationship("Location", back_populates="accommodations")
    trip_accommodations: Mapped[List["TripAccommodation"]] = relationship(
        "TripAccommodation",
        back_populates="accommodation",
    )
    accommodation_images: Mapped[List["AccommodationImage"]] = relationship(
        "AccommodationImage",
        back_populates="accommodation",
        cascade="all, delete-orphan",
    )
    offers: Mapped[List["Offer"]] = relationship(
        "Offer",
        back_populates="accommodation",
    )
