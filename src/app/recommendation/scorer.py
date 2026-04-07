import math
import random
from collections import Counter
from datetime import datetime, timezone

from src.app.config import settings
from src.app.models.user import User
from src.app.recommendation.base import ScoredArticle


class FinalScorer:
    """Applies the weighted scoring formula from PRD Section 10.5.

    final_score = w1 * content + w2 * freshness + w3 * source_diversity
                + w4 * exploration + w5 * importance
    """

    def score(
        self,
        scored_articles: list[ScoredArticle],
        user: User,
        recent_source_counts: Counter | None = None,
    ) -> list[ScoredArticle]:
        if not scored_articles:
            return []

        primary_domains = {dp.domain_id for dp in user.domain_preferences}
        exploration_rate = max(
            user.exploration_rate, settings.min_exploration_rate
        )
        recent_source_counts = recent_source_counts or Counter()

        for sa in scored_articles:
            article = sa.article

            # Freshness: exponential decay based on publish time
            sa.freshness_score = self._freshness(article.published_at)

            # Source diversity: boost under-represented sources
            source_count = recent_source_counts.get(article.source_adapter, 0)
            sa.source_diversity_bonus = 1.0 / (1.0 + source_count)

            # Exploration: random boost for non-primary domains
            if article.domain not in primary_domains:
                sa.exploration_score = exploration_rate * random.random()
                sa.is_exploration = True
            else:
                sa.exploration_score = 0.0

            # Importance from article
            sa.importance_score = article.importance_score

            # Weighted final score
            sa.final_score = (
                settings.weight_content * sa.content_score
                + settings.weight_freshness * sa.freshness_score
                + settings.weight_source_diversity * sa.source_diversity_bonus
                + settings.weight_exploration * sa.exploration_score
                + settings.weight_importance * sa.importance_score
            )

        return scored_articles

    def _freshness(self, published_at: datetime | None) -> float:
        """Exponential decay: 1.0 for now, ~0.5 at 24h, ~0.1 at 3 days."""
        if not published_at:
            return 0.3  # Unknown date gets a neutral score

        now = datetime.now(timezone.utc)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)

        hours_old = max(0, (now - published_at).total_seconds() / 3600)
        return math.exp(-0.03 * hours_old)
