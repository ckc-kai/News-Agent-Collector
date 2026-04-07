from datetime import datetime

from pydantic import BaseModel

from src.app.schemas.article import ArticleResponse


class DigestItemResponse(BaseModel):
    position: int
    rendered_depth: str
    final_score: float
    is_exploration: bool
    article: ArticleResponse


class DigestResponse(BaseModel):
    id: str
    user_id: str
    generated_at: datetime
    item_count: int
    items: list[DigestItemResponse]
