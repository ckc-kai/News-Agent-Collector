import uuid
from datetime import datetime

from sqlalchemy import Index, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.app.db.base import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE")
    )
    article_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("articles.id", ondelete="CASCADE")
    )
    feedback_type: Mapped[str] = mapped_column(String(30))
    # Nullable value: used for star_rating (1-5), None for binary actions
    value: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_feedback_user_created", "user_id", "created_at"),
    )
