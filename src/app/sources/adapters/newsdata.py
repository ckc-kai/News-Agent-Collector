import logging
from datetime import datetime

import httpx

from src.app.config import settings
from src.app.core.constants import DomainID
from src.app.schemas.article import RawArticle
from src.app.sources.base import SourceAdapter

logger = logging.getLogger(__name__)

_BASE_URL = "https://newsdata.io/api/1/latest"

_DOMAIN_CATEGORIES: dict[str, str] = {
    DomainID.TECH: "technology",
    DomainID.ECON: "business",
    DomainID.POLITICS: "politics",
    DomainID.SCIENCE: "science",
    DomainID.BIOTECH: "health",
    DomainID.SUSTAINABILITY: "environment",
}


class NewsDataAdapter(SourceAdapter):
    def __init__(self):
        self._api_key = settings.newsdata_api_key

    @property
    def name(self) -> str:
        return "newsdata"

    @property
    def supported_domains(self) -> list[str]:
        return list(DomainID)

    @property
    def rate_limit_per_day(self) -> int:
        return settings.newsdata_daily_limit

    def is_available(self) -> bool:
        return bool(self._api_key)

    async def fetch(
        self, query: str, domain: str | None = None, max_results: int = 10
    ) -> list[RawArticle]:
        params: dict = {
            "apikey": self._api_key,
            "language": "en",
            "size": min(max_results, 50),
        }

        if domain and domain in _DOMAIN_CATEGORIES:
            params["category"] = _DOMAIN_CATEGORIES[domain]
        if query:
            params["q"] = query

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(_BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        articles = []
        for item in data.get("results", []):
            articles.append(
                RawArticle(
                    source_adapter=self.name,
                    source_url=item.get("link", ""),
                    title=item.get("title", ""),
                    authors=item.get("creator") or [],
                    published_at=_parse_date(item.get("pubDate")),
                    raw_content=item.get("description", "") or item.get("content", ""),
                    language=item.get("language", "en"),
                    extra={
                        "source_name": item.get("source_name"),
                        "country": item.get("country"),
                        "category": item.get("category"),
                        "image_url": item.get("image_url"),
                    },
                )
            )
        return articles

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    _BASE_URL,
                    params={"apikey": self._api_key, "language": "en", "size": 1},
                )
                return resp.status_code == 200
        except Exception:
            logger.exception("NewsData health check failed")
            return False


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
