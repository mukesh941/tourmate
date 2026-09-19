"""
Interaction models: Feedback and Offer.
Supports user sentiment capture with target check constraint and commercial affiliate offers.
"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.sql.base import Base

if TYPE_CHECKING:
    from app.models.sql.user import User
    from app.models.sql.poi import POI
    from app.models.sql.trip import Trip
    from app.models.sql.itinerary import Itinerary
    from app.models.sql.location import Location
    from app.models.sql.accommodation import Accommodation


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_feedback_rating_range"),
        CheckConstraint(
            "trip_id IS NOT NULL OR poi_id IS NOT NULL OR itinerary_id IS NOT NULL",
            name="ck_feedback_target_not_null",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    poi_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pois.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    trip_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    itinerary_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("itineraries.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, default="", nullable=False)
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
    user: Mapped["User"] = relationship("User", back_populates="feedback")
    poi: Mapped["POI | None"] = relationship("POI", back_populates="feedback")
    trip: Mapped["Trip | None"] = relationship("Trip", back_populates="feedback")
    itinerary: Mapped["Itinerary | None"] = relationship("Itinerary", back_populates="feedback")


class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (
        CheckConstraint("valid_until >= valid_from", name="ck_offers_validity_window"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    poi_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pois.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    accommodation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accommodations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    discount_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    promo_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    affiliate_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Backwards compatibility alias
    @property
    def valid_to(self) -> date:
        return self.valid_until

    @valid_to.setter
    def valid_to(self, val: date) -> None:
        self.valid_until = val

    # Relationships
    location: Mapped["Location"] = relationship("Location", back_populates="offers")
    poi: Mapped["POI | None"] = relationship("POI", back_populates="offers")
    accommodation: Mapped["Accommodation | None"] = relationship("Accommodation", back_populates="offers")
