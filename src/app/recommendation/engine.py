import logging

from src.app.models.article import Article
from src.app.models.user import User
from src.app.recommendation.base import RecommendationStrategy, ScoredArticle
from src.app.recommendation.diversity import DiversityFilter
from src.app.recommendation.scorer import FinalScorer
from src.app.recommendation.strategies.content_based import ContentBasedStrategy

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Orchestrates strategy → scorer → diversity filter.

    Composes three pluggable components:
    1. Strategy: scores articles by content relevance
    2. Scorer: applies the weighted formula (freshness, diversity, etc.)
    3. DiversityFilter: enforces constraints and interleaving
    """

    def __init__(
        self,
        strategy: RecommendationStrategy | None = None,
        scorer: FinalScorer | None = None,
        diversity_filter: DiversityFilter | None = None,
    ):
        self._strategy = strategy or ContentBasedStrategy()
        self._scorer = scorer or FinalScorer()
        self._diversity = diversity_filter or DiversityFilter()

    async def recommend(
        self,
        user: User,
        candidates: list[Article],
        max_items: int | None = None,
    ) -> list[ScoredArticle]:
        """Generate ranked, diversified recommendations for a user."""
        if not candidates:
            return []

        # Step 1: Content-based scoring
        scored = await self._strategy.score(user, candidates)

        # Step 2: Apply weighted formula (freshness, diversity bonus, etc.)
        scored = self._scorer.score(scored, user)

        # Step 3: Enforce diversity constraints and interleave
        result = self._diversity.filter(scored, user, max_items)

        logger.info(
            "Recommended %d items for user %s from %d candidates",
            len(result),
            user.id,
            len(candidates),
        )
        return result
