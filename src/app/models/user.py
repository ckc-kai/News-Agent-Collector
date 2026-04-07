import uuid
from datetime import datetime

from sqlalchemy import String, Float, Boolean, DateTime, ARRAY, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    name: Mapped[str | None] = mapped_column(String(255))

    # Global preferences
    global_depth_fallback: Mapped[str] = mapped_column(String(5), default="L2")
    exploration_rate: Mapped[float] = mapped_column(Float, default=0.15)

    # Delivery schedule
    delivery_frequency: Mapped[str] = mapped_column(String(20), default="daily")
    delivery_time: Mapped[str] = mapped_column(String(10), default="08:00")
    delivery_timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    delivery_channel: Mapped[str] = mapped_column(String(10), default="in_app")

    # Lists stored as arrays
    seed_topics: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=list)
    trusted_sources: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), default=list
    )
    excluded_sources: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), default=list
    )
    blocked_domains: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), default=list
    )

    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    domain_preferences: Mapped[list["UserDomainPreference"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )


class UserDomainPreference(Base):
    __tablename__ = "user_domain_preferences"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    domain_id: Mapped[str] = mapped_column(String(50))
    weight: Mapped[float] = mapped_column(Float, default=0.5)
    depth_preference: Mapped[str] = mapped_column(String(5), default="L2")
    is_explicit: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="domain_preferences")
