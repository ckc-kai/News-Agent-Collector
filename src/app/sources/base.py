from abc import ABC, abstractmethod

from src.app.schemas.article import RawArticle


class SourceAdapter(ABC):
    """Base class for all content source adapters.

    To add a new source:
    1. Create a new file in sources/adapters/
    2. Subclass SourceAdapter
    3. Implement all abstract methods
    4. Register in sources/registry.py
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this source (e.g., 'tavily', 'newsapi')."""

    @property
    @abstractmethod
    def supported_domains(self) -> list[str]:
        """List of DomainID values this source covers."""

    @property
    @abstractmethod
    def rate_limit_per_day(self) -> int:
        """Maximum API calls per day under the free tier."""

    @abstractmethod
    async def fetch(
        self, query: str, domain: str | None = None, max_results: int = 10
    ) -> list[RawArticle]:
        """Fetch articles matching the query.

        Args:
            query: Search query string.
            domain: Optional domain filter (DomainID value).
            max_results: Maximum number of articles to return.

        Returns:
            List of RawArticle objects from this source.
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the source API is reachable and functional."""

    def is_available(self) -> bool:
        """Whether this adapter has the required configuration (API keys, etc.).
        Override in subclasses that require API keys."""
        return True
