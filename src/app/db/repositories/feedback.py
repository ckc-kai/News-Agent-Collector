from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.repositories.base import BaseRepository
from src.app.models.feedback import Feedback


class FeedbackRepository(BaseRepository[Feedback]):
    def __init__(self, session: AsyncSession):
        super().__init__(Feedback, session)

    async def get_recent_for_user(
        self, user_id: str, days: int = 14
    ) -> list[Feedback]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(Feedback)
            .where(Feedback.user_id == user_id, Feedback.created_at >= cutoff)
            .order_by(Feedback.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_domain_engagement_counts(
        self, user_id: str, days: int = 14
    ) -> dict[str, int]:
        """Count feedback events per domain for drift detection."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(Feedback)
            .where(Feedback.user_id == user_id, Feedback.created_at >= cutoff)
        )
        result = await self._session.execute(stmt)
        feedbacks = result.scalars().all()

        # Would need a join with articles to get domains
        # For now, return feedback count (domain-level aggregation done at service layer)
        counts: dict[str, int] = {}
        for fb in feedbacks:
            counts[fb.feedback_type] = counts.get(fb.feedback_type, 0) + 1
        return counts
