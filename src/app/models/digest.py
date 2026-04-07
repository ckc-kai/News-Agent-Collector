import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.db.base import Base


class Digest(Base):
    __tablename__ = "digests"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    item_count: Mapped[int] = mapped_column(Integer, default=0)

    items: Mapped[list["DigestItem"]] = relationship(
        back_populates="digest", cascade="all, delete-orphan", lazy="selectin"
    )


class DigestItem(Base):
    __tablename__ = "digest_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    digest_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("digests.id", ondelete="CASCADE"), index=True
    )
    article_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("articles.id", ondelete="CASCADE")
    )
    position: Mapped[int] = mapped_column(Integer)
    rendered_depth: Mapped[str] = mapped_column(String(5))  # L1, L2, or L3
    final_score: Mapped[float] = mapped_column(Float)
    is_exploration: Mapped[bool] = mapped_column(Boolean, default=False)

    digest: Mapped["Digest"] = relationship(back_populates="items")
