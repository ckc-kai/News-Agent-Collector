from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dependencies import get_db, get_feedback_processor
from src.app.feedback.processor import FeedbackProcessor
from src.app.schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    data: FeedbackCreate,
    session: AsyncSession = Depends(get_db),
    processor: FeedbackProcessor = Depends(get_feedback_processor),
):
    fb = await processor.process(data, session)
    return fb
