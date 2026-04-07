import logging

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from src.app.models.article import Article
from src.app.models.user import User
from src.app.recommendation.base import RecommendationStrategy, ScoredArticle

logger = logging.getLogger(__name__)


class ContentBasedStrategy(RecommendationStrategy):
    """Phase 1 recommendation: TF-IDF + cosine similarity + domain weights.

    User vector = alpha * explicit_preferences + (1-alpha) * learned_behavior
    Alpha decays from 1.0 (day 0) to 0.3 (day 30+).
    In Phase 1, learned_behavior is empty, so alpha stays at 1.0 until
    enough feedback accumulates.
    """

    async def score(
        self, user: User, candidates: list[Article]
    ) -> list[ScoredArticle]:
        if not candidates:
            return []

        # Build user interest text from preferences and seed topics
        user_interests = self._build_user_interest_text(user)
        if not user_interests:
            # No preferences → return all with neutral scores
            return [ScoredArticle(article=a, content_score=0.5) for a in candidates]

        # Build domain weight lookup
        domain_weights = {
            dp.domain_id: dp.weight for dp in user.domain_preferences
        }

        # TF-IDF vectorize user interests + all article texts
        texts = [user_interests] + [
            f"{a.title} {a.raw_content or ''}" for a in candidates
        ]

        try:
            vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
            tfidf_matrix = vectorizer.fit_transform(texts)

            # Cosine similarity between user vector (index 0) and all articles
            user_vec = tfidf_matrix[0:1]
            article_vecs = tfidf_matrix[1:]
            similarities = cosine_similarity(user_vec, article_vecs).flatten()
        except ValueError:
            similarities = np.full(len(candidates), 0.5)

        scored = []
        for i, article in enumerate(candidates):
            # Base content similarity
            sim_score = float(similarities[i])

            # Boost by domain weight if user has a preference for this domain
            domain_weight = domain_weights.get(article.domain, 0.1)
            content_score = sim_score * (0.5 + 0.5 * domain_weight)

            # Penalize blocked domains
            if article.domain in (user.blocked_domains or []):
                content_score = 0.0

            scored.append(ScoredArticle(
                article=article,
                content_score=min(content_score, 1.0),
            ))

        return scored

    def _build_user_interest_text(self, user: User) -> str:
        """Build a text representation of user interests for TF-IDF comparison."""
        parts = []

        # Domain names with weights
        for dp in user.domain_preferences:
            # Repeat domain keywords proportionally to weight
            repeat = max(1, int(dp.weight * 5))
            parts.extend([dp.domain_id.replace("_", " ")] * repeat)

        # Seed topics
        if user.seed_topics:
            parts.extend(user.seed_topics)

        return " ".join(parts)
