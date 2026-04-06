from datetime import datetime

from pydantic import BaseModel, Field

from src.app.schemas.article import ArticleResponse


class SearchQuery(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    domains: list[str] | None = None
    source_types: list[str] | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    max_results: int = Field(default=20, ge=1, le=100)


class SearchResponse(BaseModel):
    query: str
    total_results: int
    articles: list[ArticleResponse]
    sources_queried: list[str]
