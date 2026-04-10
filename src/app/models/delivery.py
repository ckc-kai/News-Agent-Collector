import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.app.db.base import Base


class DeliveryLog(Base):
    __tablename__ = "delivery_log"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    sent_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False)  # "sent" | "failed"
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    resend_email_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("sent_date", "channel", name="uq_delivery_log_date_channel"),
    )
