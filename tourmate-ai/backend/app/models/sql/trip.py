"""
Trip and Trip associations: TripAccommodation, TripTransport, and POICluster models.
Conforms strictly to the locked 23-table architecture.
"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.sql.base import Base

if TYPE_CHECKING:
    from app.models.sql.user import User
    from app.models.sql.location import Location
    from app.models.sql.accommodation import Accommodation
    from app.models.sql.transport import TransportOption
    from app.models.sql.poi import POI
    from app.models.sql.itinerary import Itinerary
    from app.models.sql.interaction import Feedback


class Trip(Base):
    __tablename__ = "trips"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_trips_date_range"),
        CheckConstraint("total_days >= 1 AND total_days <= 30", name="ck_trips_total_days_range"),
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
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    budget: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="planning", nullable=False)
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

    # Backwards compatibility alias
    @property
    def destination_location_id(self) -> uuid.UUID:
        return self.location_id

    @destination_location_id.setter
    def destination_location_id(self, val: uuid.UUID) -> None:
        self.location_id = val

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="trips")
    location: Mapped["Location"] = relationship("Location", back_populates="trips")
    accommodations: Mapped[List["TripAccommodation"]] = relationship(
        "TripAccommodation",
        back_populates="trip",
        cascade="all, delete-orphan",
    )
    transports: Mapped[List["TripTransport"]] = relationship(
        "TripTransport",
        back_populates="trip",
        cascade="all, delete-orphan",
    )
    poi_clusters: Mapped[List["POICluster"]] = relationship(
        "POICluster",
        back_populates="trip",
        cascade="all, delete-orphan",
    )
    itineraries: Mapped[List["Itinerary"]] = relationship(
        "Itinerary",
        back_populates="trip",
        cascade="all, delete-orphan",
    )
    feedback: Mapped[List["Feedback"]] = relationship(
        "Feedback",
        back_populates="trip",
    )


class TripAccommodation(Base):
    __tablename__ = "trip_accommodations"
    __table_args__ = (
        CheckConstraint("check_out_date >= check_in_date", name="ck_trip_acc_date_range"),
    )

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
    accommodation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accommodations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="accommodations")
    accommodation: Mapped["Accommodation"] = relationship("Accommodation", back_populates="trip_accommodations")


class TripTransport(Base):
    __tablename__ = "trip_transports"

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
    transport_option_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transport_options.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    booking_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    departure_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    arrival_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="transports")
    transport_option: Mapped["TransportOption"] = relationship("TransportOption", back_populates="trip_transports")


class POICluster(Base):
    __tablename__ = "poi_clusters"
    __table_args__ = (
        UniqueConstraint("trip_id", "poi_id", name="uq_poi_clusters_trip_poi"),
    )

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
    poi_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pois.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    cluster_index: Mapped[int] = mapped_column(Integer, nullable=False)
    centroid_lat: Mapped[float] = mapped_column(Float, nullable=False)
    centroid_lon: Mapped[float] = mapped_column(Float, nullable=False)
    assigned_day: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="poi_clusters")
    poi: Mapped["POI"] = relationship("POI", back_populates="clusters")
