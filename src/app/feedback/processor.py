import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.events import event_bus, FEEDBACK_RECEIVED, PREFERENCE_UPDATED
from src.app.feedback.handlers import compute_delta
from src.app.feedback.preference_updater import PreferenceUpdater
from src.app.models.article import Article
from src.app.models.feedback import Feedback
from src.app.schemas.feedback import FeedbackCreate

logger = logging.getLogger(__name__)


class FeedbackProcessor:
    """Processes user feedback: persist → compute delta → update preferences → emit events."""

    def __init__(self):
        self._updater = PreferenceUpdater()

    async def process(self, feedback: FeedbackCreate, session: AsyncSession) -> Feedback:
        # Get article to determine its domain
        article = await session.get(Article, feedback.article_id)
        if not article:
            raise ValueError(f"Article not found: {feedback.article_id}")

        # Persist feedback
        fb = Feedback(
            user_id=feedback.user_id,
            article_id=feedback.article_id,
            feedback_type=feedback.feedback_type,
            value=feedback.value,
        )
        session.add(fb)
        await session.flush()

        # Compute and apply weight delta
        delta = compute_delta(
            feedback.feedback_type,
            article.domain or "tech",
            feedback.value,
        )
        await self._updater.apply(session, feedback.user_id, delta)

        # Emit events
        await event_bus.publish(
            FEEDBACK_RECEIVED,
            user_id=feedback.user_id,
            article_id=feedback.article_id,
            feedback_type=feedback.feedback_type,
        )
        await event_bus.publish(
            PREFERENCE_UPDATED,
            user_id=feedback.user_id,
            domain_id=delta.domain_id,
            weight_change=delta.weight_change,
        )

        logger.info(
            "Processed %s feedback from user %s for article %s (domain: %s, delta: %+.2f)",
            feedback.feedback_type,
            feedback.user_id,
            feedback.article_id,
            delta.domain_id,
            delta.weight_change,
        )
        return fb
