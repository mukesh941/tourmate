"""
Itinerary, ItineraryStop, Route, and AlternativeRoute models.
Conforms strictly to the locked Trip -> Itinerary -> Itinerary Stops hierarchy.
"""
import uuid
from datetime import datetime, time, timezone
from typing import TYPE_CHECKING, Any, List
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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.sql.base import Base

if TYPE_CHECKING:
    from app.models.sql.trip import Trip
    from app.models.sql.poi import POI
    from app.models.sql.interaction import Feedback


class Itinerary(Base):
    __tablename__ = "itineraries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), default="Primary Plan", nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    total_distance_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_travel_time_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
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
    trip: Mapped["Trip"] = relationship("Trip", back_populates="itineraries")
    stops: Mapped[List["ItineraryStop"]] = relationship(
        "ItineraryStop",
        back_populates="itinerary",
        cascade="all, delete-orphan",
        order_by="ItineraryStop.day_number, ItineraryStop.stop_order",
    )
    routes: Mapped[List["Route"]] = relationship(
        "Route",
        back_populates="itinerary",
        cascade="all, delete-orphan",
    )
    feedback: Mapped[List["Feedback"]] = relationship(
        "Feedback",
        back_populates="itinerary",
    )


class ItineraryStop(Base):
    __tablename__ = "itinerary_stops"
    __table_args__ = (
        UniqueConstraint("itinerary_id", "day_number", "stop_order", name="uq_itinerary_stops_seq"),
        CheckConstraint("duration_minutes > 0", name="ck_itinerary_stops_duration_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    itinerary_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("itineraries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    poi_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pois.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    day_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    stop_order: Mapped[int] = mapped_column(Integer, nullable=False)
    arrival_time: Mapped[time] = mapped_column(Time, default=time(9, 0), nullable=False)
    departure_time: Mapped[time] = mapped_column(Time, default=time(10, 30), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    itinerary: Mapped["Itinerary"] = relationship("Itinerary", back_populates="stops")
    poi: Mapped["POI"] = relationship("POI", back_populates="itinerary_stops")


class Route(Base):
    __tablename__ = "routes"
    __table_args__ = (
        CheckConstraint(
            "source_stop_id IS NOT NULL OR target_stop_id IS NOT NULL",
            name="ck_routes_source_or_target_not_null",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    itinerary_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("itineraries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_stop_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("itinerary_stops.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    target_stop_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("itinerary_stops.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    distance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    geometry: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB, nullable=True)
    polyline: Mapped[str | None] = mapped_column(Text, nullable=True)
    mode: Mapped[str] = mapped_column(String(32), default="driving", nullable=False)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Aliases for backwards compatibility
    @property
    def distance_meters(self) -> float:
        return self.distance * 1000.0

    @distance_meters.setter
    def distance_meters(self, val: float) -> None:
        self.distance = val / 1000.0

    @property
    def duration_seconds(self) -> int:
        return self.duration * 60

    @duration_seconds.setter
    def duration_seconds(self, val: int) -> None:
        self.duration = int(val / 60)

    # Relationships
    itinerary: Mapped["Itinerary"] = relationship("Itinerary", back_populates="routes")
    source_stop: Mapped["ItineraryStop | None"] = relationship(
        "ItineraryStop",
        foreign_keys=[source_stop_id],
    )
    target_stop: Mapped["ItineraryStop | None"] = relationship(
        "ItineraryStop",
        foreign_keys=[target_stop_id],
    )
    alternative_routes: Mapped[List["AlternativeRoute"]] = relationship(
        "AlternativeRoute",
        back_populates="route",
        cascade="all, delete-orphan",
    )


class AlternativeRoute(Base):
    __tablename__ = "alternative_routes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    distance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    geometry: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB, nullable=True)
    polyline: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Backwards compatibility alias
    @property
    def reason(self) -> str | None:
        return self.description

    @reason.setter
    def reason(self, val: str | None) -> None:
        self.description = val

    # Relationships
    route: Mapped["Route"] = relationship("Route", back_populates="alternative_routes")
