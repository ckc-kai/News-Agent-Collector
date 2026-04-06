import logging
from collections import Counter

from src.app.config import settings
from src.app.models.user import User
from src.app.recommendation.base import ScoredArticle

logger = logging.getLogger(__name__)


class DiversityFilter:
    """Enforces digest diversity constraints from PRD Section FR-4.2.

    - Max 40% items from a single domain
    - Max 30% items from a single source
    - Min explorationRate * N exploration items
    - Domain interleaving (avoid clustering)
    """

    def filter(
        self, scored: list[ScoredArticle], user: User, max_items: int | None = None
    ) -> list[ScoredArticle]:
        max_items = max_items or settings.digest_max_items

        # Sort by final score descending
        sorted_articles = sorted(scored, key=lambda s: s.final_score, reverse=True)

        exploration_rate = max(user.exploration_rate, settings.min_exploration_rate)
        min_exploration = max(1, int(exploration_rate * max_items))
        max_per_domain = max(1, int(settings.digest_max_domain_pct * max_items))
        max_per_source = max(1, int(settings.digest_max_source_pct * max_items))

        selected: list[ScoredArticle] = []
        domain_counts: Counter = Counter()
        source_counts: Counter = Counter()
        exploration_count = 0

        # First pass: select top items respecting constraints
        for sa in sorted_articles:
            if len(selected) >= max_items:
                break

            domain = sa.article.domain or "unknown"
            source = sa.article.source_adapter

            if domain_counts[domain] >= max_per_domain:
                continue
            if source_counts[source] >= max_per_source:
                continue

            selected.append(sa)
            domain_counts[domain] += 1
            source_counts[source] += 1
            if sa.is_exploration:
                exploration_count += 1

        # Second pass: ensure minimum exploration quota
        if exploration_count < min_exploration:
            exploration_candidates = [
                sa for sa in sorted_articles
                if sa.is_exploration and sa not in selected
            ]
            for sa in exploration_candidates:
                if exploration_count >= min_exploration:
                    break
                if len(selected) >= max_items:
                    # Replace the lowest-scored non-exploration item
                    non_exp = [s for s in selected if not s.is_exploration]
                    if non_exp:
                        worst = min(non_exp, key=lambda s: s.final_score)
                        selected.remove(worst)
                        selected.append(sa)
                        exploration_count += 1
                else:
                    selected.append(sa)
                    exploration_count += 1

        # Interleave domains to avoid clustering
        return self._interleave_domains(selected)

    def _interleave_domains(
        self, articles: list[ScoredArticle]
    ) -> list[ScoredArticle]:
        """Reorder articles so same-domain items aren't adjacent."""
        if len(articles) <= 2:
            return articles

        # Group by domain
        by_domain: dict[str, list[ScoredArticle]] = {}
        for sa in articles:
            domain = sa.article.domain or "unknown"
            by_domain.setdefault(domain, []).append(sa)

        # Round-robin across domains, taking highest scored from each
        for group in by_domain.values():
            group.sort(key=lambda s: s.final_score, reverse=True)

        result: list[ScoredArticle] = []
        while any(by_domain.values()):
            for domain in sorted(
                by_domain.keys(),
                key=lambda d: by_domain[d][0].final_score if by_domain[d] else 0,
                reverse=True,
            ):
                if by_domain[domain]:
                    result.append(by_domain[domain].pop(0))
            # Remove empty domains
            by_domain = {k: v for k, v in by_domain.items() if v}

        return result
