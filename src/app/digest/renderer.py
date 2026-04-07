from src.app.core.constants import DepthLevel
from src.app.models.user import User
from src.app.recommendation.base import ScoredArticle


class DepthRenderer:
    """Maps each article to the user's per-domain depth preference.

    Each digest item is rendered at its domain-specific depth level,
    falling back to the user's global_depth_fallback.
    """

    def resolve_depth(self, scored: ScoredArticle, user: User) -> str:
        """Determine the depth level for a scored article."""
        domain = scored.article.domain

        # Look up per-domain depth preference
        for dp in user.domain_preferences:
            if dp.domain_id == domain:
                return dp.depth_preference

        # Fall back to global default
        return user.global_depth_fallback or DepthLevel.L2

    def get_summary(self, scored: ScoredArticle, depth: str) -> str | None:
        """Get the appropriate summary text for the given depth."""
        article = scored.article
        if depth == DepthLevel.L1:
            return article.summary_l1
        elif depth == DepthLevel.L2:
            return article.summary_l2 or article.summary_l1
        elif depth == DepthLevel.L3:
            return article.summary_l3 or article.summary_l2 or article.summary_l1
        return article.summary_l1
