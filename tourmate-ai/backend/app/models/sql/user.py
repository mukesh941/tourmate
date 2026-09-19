"""
User, UserInterest, and Preference models conforming strictly to locked architecture.
"""
import uuid
from datetime import datetime, time, timezone
from typing import TYPE_CHECKING, List
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.sql.base import Base

if TYPE_CHECKING:
    from app.models.sql.category import Category
    from app.models.sql.trip import Trip
    from app.models.sql.interaction import Feedback


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(email) >= 5", name="ck_users_email_length"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="user", nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    token_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
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

    # Convenience properties for backwards compatibility
    @property
    def hashed_password(self) -> str:
        return self.password_hash

    @hashed_password.setter
    def hashed_password(self, val: str) -> None:
        self.password_hash = val

    @property
    def full_name(self) -> str:
        return self.name

    @full_name.setter
    def full_name(self, val: str) -> None:
        self.name = val

    # Relationships
    interests: Mapped[List["UserInterest"]] = relationship(
        "UserInterest",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    preferences: Mapped["Preference | None"] = relationship(
        "Preference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    trips: Mapped[List["Trip"]] = relationship(
        "Trip",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    feedback: Mapped[List["Feedback"]] = relationship(
        "Feedback",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserInterest(Base):
    __tablename__ = "user_interests"
    __table_args__ = (
        UniqueConstraint("user_id", "category_id", name="uq_user_interests_user_category"),
        CheckConstraint("weight >= 0.0 AND weight <= 5.0", name="ck_user_interests_weight_range"),
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
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="interests")
    category: Mapped["Category"] = relationship("Category", back_populates="user_interests")


class Preference(Base):
    __tablename__ = "preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    budget_tier: Mapped[str] = mapped_column(String(32), default="moderate", nullable=False)
    travel_style: Mapped[str] = mapped_column(String(64), default="balanced", nullable=False)
    daily_start_time: Mapped[time] = mapped_column(Time, default=time(9, 0), nullable=False)
    daily_end_time: Mapped[time] = mapped_column(Time, default=time(20, 0), nullable=False)
    max_walking_distance_km: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    preferred_transport_mode: Mapped[str] = mapped_column(String(32), default="car", nullable=False)
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
    user: Mapped["User"] = relationship("User", back_populates="preferences")
