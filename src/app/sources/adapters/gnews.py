import logging
from datetime import datetime

import httpx

from src.app.config import settings
from src.app.core.constants import DomainID
from src.app.schemas.article import RawArticle
from src.app.sources.base import SourceAdapter

logger = logging.getLogger(__name__)

_BASE_URL = "https://gnews.io/api/v4"

_DOMAIN_TOPICS: dict[str, str] = {
    DomainID.TECH: "technology",
    DomainID.ECON: "business",
    DomainID.SCIENCE: "science",
    DomainID.BIOTECH: "health",
}


class GNewsAdapter(SourceAdapter):
    def __init__(self):
        self._api_key = settings.gnews_api_key

    @property
    def name(self) -> str:
        return "gnews"

    @property
    def supported_domains(self) -> list[str]:
        return list(DomainID)

    @property
    def rate_limit_per_day(self) -> int:
        return settings.gnews_daily_limit

    def is_available(self) -> bool:
        return bool(self._api_key)

    async def fetch(
        self, query: str, domain: str | None = None, max_results: int = 10
    ) -> list[RawArticle]:
        params: dict = {
            "apikey": self._api_key,
            "max": min(max_results, 10),
            "lang": "en",
        }

        # Use topic endpoint if domain maps to a GNews topic
        if domain and domain in _DOMAIN_TOPICS:
            endpoint = f"{_BASE_URL}/top-headlines"
            params["topic"] = _DOMAIN_TOPICS[domain]
            if query:
                params["q"] = query
        else:
            endpoint = f"{_BASE_URL}/search"
            params["q"] = query

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(endpoint, params=params)
            resp.raise_for_status()
            data = resp.json()

        articles = []
        for item in data.get("articles", []):
            articles.append(
                RawArticle(
                    source_adapter=self.name,
                    source_url=item.get("url", ""),
                    title=item.get("title", ""),
                    published_at=_parse_date(item.get("publishedAt")),
                    raw_content=item.get("description", "") or item.get("content", ""),
                    extra={
                        "source_name": item.get("source", {}).get("name"),
                        "image_url": item.get("image"),
                    },
                )
            )
        return articles

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{_BASE_URL}/top-headlines",
                    params={"apikey": self._api_key, "topic": "technology", "max": 1},
                )
                return resp.status_code == 200
        except Exception:
            logger.exception("GNews health check failed")
            return False


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
