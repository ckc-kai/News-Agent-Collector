from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.session import AsyncSessionLocal
from src.app.digest.builder import DigestBuilder
from src.app.feedback.processor import FeedbackProcessor
from src.app.recommendation.engine import RecommendationEngine
from src.app.services.aggregation import AggregationService


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_aggregation_service() -> AggregationService:
    return AggregationService()


def get_recommendation_engine() -> RecommendationEngine:
    return RecommendationEngine()


def get_digest_builder() -> DigestBuilder:
    return DigestBuilder()


def get_feedback_processor() -> FeedbackProcessor:
    return FeedbackProcessor()
