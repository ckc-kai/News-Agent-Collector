from datetime import datetime

from pydantic import BaseModel, Field


class RawArticle(BaseModel):
    """Raw article data as returned by a source adapter, before normalization."""

    source_adapter: str
    source_url: str
    title: str
    authors: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
    raw_content: str = ""
    language: str = "en"
    media_type: str = "article"
    # Source-specific metadata (upvotes, citations, stars, etc.)
    extra: dict = Field(default_factory=dict)


class NormalizedArticle(BaseModel):
    """Article after pipeline processing, ready for storage and recommendation."""

    id: str
    source_adapter: str
    source_url: str
    canonical_url: str
    content_hash: str | None = None
    title: str
    authors: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
    raw_content: str = ""
    domain: str | None = None
    secondary_domains: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    language: str = "en"
    media_type: str = "article"
    importance_score: float = 0.0
    summary_l1: str | None = None
    summary_l2: str | None = None
    summary_l3: str | None = None
    merged_source_urls: list[str] = Field(default_factory=list)


class ArticleResponse(BaseModel):
    """Article as returned to the API consumer."""

    id: str
    title: str
    source_url: str
    source_adapter: str
    authors: list[str]
    published_at: datetime | None
    domain: str | None
    tags: list[str]
    media_type: str
    importance_score: float
    summary_l1: str | None
    summary_l2: str | None
    summary_l3: str | None

    model_config = {"from_attributes": True}
