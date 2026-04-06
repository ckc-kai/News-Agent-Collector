from datetime import datetime

from pydantic import BaseModel, Field

from src.app.core.constants import FeedbackType


class FeedbackCreate(BaseModel):
    user_id: str
    article_id: str
    feedback_type: FeedbackType
    value: float | None = Field(
        default=None,
        description="Required for star_rating (1-5), optional for others",
    )


class FeedbackResponse(BaseModel):
    id: str
    user_id: str
    article_id: str
    feedback_type: str
    value: float | None
    created_at: datetime

    model_config = {"from_attributes": True}
