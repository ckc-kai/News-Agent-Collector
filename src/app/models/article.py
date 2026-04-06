import uuid
from datetime import datetime

from sqlalchemy import Index, String, Text, Float, DateTime, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from src.app.db.base import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    source_adapter: Mapped[str] = mapped_column(String(50))
    source_url: Mapped[str] = mapped_column(String(2048), unique=True)
    canonical_url: Mapped[str] = mapped_column(String(2048), index=True)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(1024))
    authors: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=list)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_content: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str | None] = mapped_column(String(50), index=True)
    secondary_domains: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), default=list
    )
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=list)
    language: Mapped[str] = mapped_column(String(10), default="en")
    media_type: Mapped[str] = mapped_column(String(20), default="article")
    importance_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Multi-level summaries
    summary_l1: Mapped[str | None] = mapped_column(Text)  # Headline ≤ 15 words
    summary_l2: Mapped[str | None] = mapped_column(Text)  # 3-5 sentences
    summary_l3: Mapped[str | None] = mapped_column(Text)  # 2-3 paragraphs

    # Merged source URLs when deduplicated across sources
    merged_source_urls: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), default=list
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_articles_domain_published", "domain", "published_at"),
    )
