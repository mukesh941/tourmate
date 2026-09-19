"""
TransportOption model.
Multi-modal transit options linking origin and destination locations.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.sql.base import Base

if TYPE_CHECKING:
    from app.models.sql.location import Location
    from app.models.sql.trip import TripTransport


class TransportOption(Base):
    __tablename__ = "transport_options"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    mode: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    origin_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    destination_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    booking_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    origin_location: Mapped["Location | None"] = relationship(
        "Location",
        foreign_keys=[origin_location_id],
        back_populates="origin_transports",
    )
    destination_location: Mapped["Location | None"] = relationship(
        "Location",
        foreign_keys=[destination_location_id],
        back_populates="destination_transports",
    )
    trip_transports: Mapped[List["TripTransport"]] = relationship(
        "TripTransport",
        back_populates="transport_option",
    )
