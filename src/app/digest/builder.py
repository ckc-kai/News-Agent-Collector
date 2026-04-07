import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.digest.renderer import DepthRenderer
from src.app.models.article import Article
from src.app.models.digest import Digest, DigestItem
from src.app.models.user import User
from src.app.recommendation.base import ScoredArticle
from src.app.recommendation.engine import RecommendationEngine

logger = logging.getLogger(__name__)


class DigestBuilder:
    """Assembles a digest: recommend → assign depth → persist."""

    def __init__(
        self,
        engine: RecommendationEngine | None = None,
        renderer: DepthRenderer | None = None,
    ):
        self._engine = engine or RecommendationEngine()
        self._renderer = renderer or DepthRenderer()

    async def build(
        self,
        user: User,
        candidates: list[Article],
        session: AsyncSession,
        max_items: int | None = None,
    ) -> Digest:
        """Build and persist a digest for a user."""

        # Get recommendations
        scored = await self._engine.recommend(user, candidates, max_items)

        # Create digest
        digest = Digest(user_id=user.id, item_count=len(scored))
        session.add(digest)
        await session.flush()  # Get the digest ID

        # Create digest items with per-domain depth
        for position, sa in enumerate(scored, 1):
            depth = self._renderer.resolve_depth(sa, user)
            item = DigestItem(
                digest_id=digest.id,
                article_id=sa.article.id,
                position=position,
                rendered_depth=depth,
                final_score=sa.final_score,
                is_exploration=sa.is_exploration,
            )
            session.add(item)

        await session.flush()
        logger.info(
            "Built digest %s for user %s with %d items",
            digest.id,
            user.id,
            len(scored),
        )
        return digest
