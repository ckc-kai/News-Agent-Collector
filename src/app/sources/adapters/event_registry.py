import logging
from datetime import datetime

import httpx

from src.app.config import settings
from src.app.core.constants import DomainID
from src.app.schemas.article import RawArticle
from src.app.sources.base import SourceAdapter
from src.app.sources.adapters.event_registry_concepts import DOMAIN_CONCEPTS

logger = logging.getLogger(__name__)

_BASE_URL = "https://newsapi.ai/api/v1/article/getArticles"
_HEALTH_URL = "https://newsapi.ai/api/v1/article/getArticles"


class EventRegistryAdapter(SourceAdapter):
    def __init__(self):
        self._api_key = settings.event_registry_api_key

    @property
    def name(self) -> str:
        return "event_registry"

    @property
    def supported_domains(self) -> list[str]:
        return list(DomainID)

    @property
    def rate_limit_per_day(self) -> int:
        return settings.event_registry_daily_limit

    def is_available(self) -> bool:
        return bool(self._api_key)

    async def fetch(
        self, query: str, domain: str | None = None, max_results: int = 10
    ) -> list[RawArticle]:
        payload = self._build_payload(query, domain, max_results)
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(_BASE_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return self._parse_articles(data)

    async def health_check(self) -> bool:
        try:
            payload = self._build_payload("technology", domain=None, max_results=1)
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(_HEALTH_URL, json=payload)
                return resp.status_code == 200
        except Exception:
            logger.exception("EventRegistry health check failed")
            return False

    def _build_payload(
        self, query: str, domain: str | None, max_results: int
    ) -> dict:
        payload: dict = {
            "action": "getArticles",
            "articlesPage": 1,
            "articlesCount": min(max_results, 100),
            "articlesSortBy": "date",
            "articlesSortByAsc": False,
            "dataType": ["news"],
            "forceMaxDataTimeWindow": 31,
            "resultType": "articles",
            "ignoreSourceGroupUri": "paywall/paywalled_sources",
            "lang": "eng",
            "apiKey": self._api_key,
        }

        if domain and domain in DOMAIN_CONCEPTS:
            mapping = DOMAIN_CONCEPTS[domain]
            concept_uris = mapping.get("conceptUris", [])
            if concept_uris:
                payload["conceptUri"] = concept_uris
            else:
                payload["keyword"] = " OR ".join(mapping.get("keywords", [query]))
            if "categoryUri" in mapping:
                payload["categoryUri"] = mapping["categoryUri"]
            if "dataType" in mapping:
                payload["dataType"] = mapping["dataType"]
        else:
            payload["keyword"] = query

        return payload

    def _parse_articles(self, data: dict) -> list[RawArticle]:
        results = data.get("articles", {}).get("results", [])
        articles = []
        for item in results:
            body = item.get("body", "") or ""
            title = item.get("title", "") or ""
            if not title:
                continue

            source = item.get("source", {}) or {}
            authors_raw = item.get("authors", []) or []
            authors = [a["name"] for a in authors_raw if isinstance(a, dict) and a.get("name")]

            articles.append(
                RawArticle(
                    source_adapter=self.name,
                    source_url=item.get("url", "") or "",
                    title=title,
                    authors=authors,
                    published_at=_parse_date(item.get("dateTimePub") or item.get("dateTime")),
                    raw_content=body,
                    extra={
                        "source_name": source.get("title") or source.get("uri"),
                        "image_url": item.get("image"),
                        "event_uri": item.get("eventUri"),
                        "sentiment": item.get("sentiment"),
                        "is_duplicate": item.get("isDuplicate", False),
                    },
                )
            )
        return articles


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
