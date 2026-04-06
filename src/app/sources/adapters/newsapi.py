import logging
from datetime import datetime, timezone

import httpx

from src.app.config import settings
from src.app.core.constants import DomainID
from src.app.schemas.article import RawArticle
from src.app.sources.base import SourceAdapter

logger = logging.getLogger(__name__)

_BASE_URL = "https://newsapi.org/v2"

# Map domains to NewsAPI categories/keywords
_DOMAIN_QUERIES: dict[str, dict] = {
    DomainID.AI_ML: {"q": "artificial intelligence OR machine learning OR LLM"},
    DomainID.TECH: {"category": "technology"},
    DomainID.ECON: {"category": "business", "q": "economy OR finance OR market"},
    DomainID.POLITICS: {"q": "politics OR policy OR election OR regulation"},
    DomainID.BIOTECH: {"category": "health", "q": "biotech OR pharmaceutical OR genomics"},
    DomainID.SCIENCE: {"category": "science"},
    DomainID.SUSTAINABILITY: {"q": "climate OR sustainability OR renewable energy OR ESG"},
    DomainID.OSS: {"q": "open source OR developer tools OR GitHub"},
}


class NewsAPIAdapter(SourceAdapter):
    def __init__(self):
        self._api_key = settings.newsapi_api_key

    @property
    def name(self) -> str:
        return "newsapi"

    @property
    def supported_domains(self) -> list[str]:
        return list(DomainID)

    @property
    def rate_limit_per_day(self) -> int:
        return settings.newsapi_daily_limit

    def is_available(self) -> bool:
        return bool(self._api_key)

    async def fetch(
        self, query: str, domain: str | None = None, max_results: int = 10
    ) -> list[RawArticle]:
        params: dict = {
            "apiKey": self._api_key,
            "pageSize": min(max_results, 100),
            "language": "en",
            "sortBy": "publishedAt",
        }

        # Use domain-specific params if available, otherwise use raw query
        if domain and domain in _DOMAIN_QUERIES:
            domain_params = _DOMAIN_QUERIES[domain]
            if "category" in domain_params:
                params["category"] = domain_params["category"]
                endpoint = f"{_BASE_URL}/top-headlines"
                if "q" in domain_params:
                    params["q"] = domain_params["q"]
            else:
                params["q"] = domain_params.get("q", query)
                endpoint = f"{_BASE_URL}/everything"
        else:
            params["q"] = query
            endpoint = f"{_BASE_URL}/everything"

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(endpoint, params=params)
            resp.raise_for_status()
            data = resp.json()

        articles = []
        for item in data.get("articles", []):
            if item.get("title") == "[Removed]":
                continue
            articles.append(
                RawArticle(
                    source_adapter=self.name,
                    source_url=item.get("url", ""),
                    title=item.get("title", ""),
                    authors=[item["author"]] if item.get("author") else [],
                    published_at=_parse_date(item.get("publishedAt")),
                    raw_content=item.get("description", "") or item.get("content", ""),
                    extra={
                        "source_name": item.get("source", {}).get("name"),
                        "image_url": item.get("urlToImage"),
                    },
                )
            )
        return articles

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{_BASE_URL}/top-headlines",
                    params={"apiKey": self._api_key, "country": "us", "pageSize": 1},
                )
                return resp.status_code == 200
        except Exception:
            logger.exception("NewsAPI health check failed")
            return False


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
