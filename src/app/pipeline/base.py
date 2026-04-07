from abc import ABC, abstractmethod

from src.app.pipeline.context import PipelineContext
from src.app.schemas.article import NormalizedArticle


class PipelineStage(ABC):
    """Base class for all pipeline stages.

    Each stage receives a list of articles and a shared context,
    processes them, and returns a (possibly modified) list.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for logging and metrics."""

    @abstractmethod
    async def process(
        self, articles: list[NormalizedArticle], context: PipelineContext
    ) -> list[NormalizedArticle]:
        """Process articles through this stage.

        Args:
            articles: List of articles to process.
            context: Shared pipeline context for stats, errors, etc.

        Returns:
            Processed list of articles (may be filtered/modified).
        """
