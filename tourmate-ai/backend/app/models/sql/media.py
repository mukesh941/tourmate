"""
Media models: Image, POIImage, AccommodationImage.
Includes partial unique index on deduplicated external image references.
"""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.sql.base import Base

if TYPE_CHECKING:
    from app.models.sql.poi import POI
    from app.models.sql.accommodation import Accommodation


class Image(Base):
    __tablename__ = "images"
    __table_args__ = (
        Index(
            "uq_images_source_external_id",
            "source",
            "external_image_id",
            unique=True,
            postgresql_where=("source IS NOT NULL AND external_image_id IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    caption: Mapped[str | None] = mapped_column(String(255), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    external_image_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    license_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attribution_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Backwards compatibility alias
    @property
    def alt_text(self) -> str | None:
        return self.caption

    @alt_text.setter
    def alt_text(self, val: str | None) -> None:
        self.caption = val

    # Relationships
    poi_images: Mapped[List["POIImage"]] = relationship(
        "POIImage",
        back_populates="image",
    )
    accommodation_images: Mapped[List["AccommodationImage"]] = relationship(
        "AccommodationImage",
        back_populates="image",
    )


class POIImage(Base):
    __tablename__ = "poi_images"
    __table_args__ = (
        UniqueConstraint("poi_id", "image_id", name="uq_poi_images_poi_image"),
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
    image_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    poi: Mapped["POI"] = relationship("POI", back_populates="poi_images")
    image: Mapped["Image"] = relationship("Image", back_populates="poi_images")


class AccommodationImage(Base):
    __tablename__ = "accommodation_images"
    __table_args__ = (
        UniqueConstraint("accommodation_id", "image_id", name="uq_accommodation_images_acc_image"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    accommodation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accommodations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    accommodation: Mapped["Accommodation"] = relationship("Accommodation", back_populates="accommodation_images")
    image: Mapped["Image"] = relationship("Image", back_populates="accommodation_images")
