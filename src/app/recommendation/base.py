from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.app.models.article import Article
from src.app.models.user import User


@dataclass
class ScoredArticle:
    """An article with its computed recommendation scores."""

    article: Article
    content_score: float = 0.0
    freshness_score: float = 0.0
    source_diversity_bonus: float = 0.0
    exploration_score: float = 0.0
    importance_score: float = 0.0
    final_score: float = 0.0
    is_exploration: bool = False


class RecommendationStrategy(ABC):
    """Base class for recommendation strategies (Strategy Pattern).

    Phase 1: ContentBasedStrategy (TF-IDF + cosine similarity)
    Phase 2: CollaborativeStrategy (implicit ALS)
    """

    @abstractmethod
    async def score(
        self, user: User, candidates: list[Article]
    ) -> list[ScoredArticle]:
        """Score candidate articles for a user.

        Returns articles with content_score populated.
        Other score components are added by the FinalScorer.
        """
