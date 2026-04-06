import logging
from datetime import datetime, timezone

from tavily import AsyncTavilyClient

from src.app.config import settings
from src.app.core.constants import DomainID
from src.app.schemas.article import RawArticle
from src.app.sources.base import SourceAdapter

logger = logging.getLogger(__name__)


class TavilyAdapter(SourceAdapter):
    def __init__(self):
        if self.is_available():
            self._client = AsyncTavilyClient(api_key=settings.tavily_api_key)

    @property
    def name(self) -> str:
        return "tavily"

    @property
    def supported_domains(self) -> list[str]:
        return list(DomainID)  # General-purpose search covers all domains

    @property
    def rate_limit_per_day(self) -> int:
        return settings.tavily_daily_limit

    def is_available(self) -> bool:
        return bool(settings.tavily_api_key)

    async def fetch(
        self, query: str, domain: str | None = None, max_results: int = 10
    ) -> list[RawArticle]:
        response = await self._client.search(
            query=query,
            max_results=min(max_results, 10),
            search_depth="basic",
            include_answer=False,
        )

        articles = []
        for result in response.get("results", []):
            articles.append(
                RawArticle(
                    source_adapter=self.name,
                    source_url=result.get("url", ""),
                    title=result.get("title", ""),
                    raw_content=result.get("content", ""),
                    published_at=_parse_date(result.get("published_date")),
                    extra={"score": result.get("score", 0)},
                )
            )
        return articles

    async def health_check(self) -> bool:
        try:
            response = await self._client.search(query="test", max_results=1)
            return "results" in response
        except Exception:
            logger.exception("Tavily health check failed")
            return False


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
