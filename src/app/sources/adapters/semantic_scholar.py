import logging
from datetime import datetime

import httpx

from src.app.config import settings
from src.app.core.constants import DomainID
from src.app.schemas.article import RawArticle
from src.app.sources.base import SourceAdapter

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.semanticscholar.org/graph/v1"

_DOMAIN_FIELDS: dict[str, str] = {
    DomainID.AI_ML: "Computer Science",
    DomainID.BIOTECH: "Biology,Medicine",
    DomainID.SCIENCE: "Physics,Mathematics,Chemistry",
    DomainID.ECON: "Economics",
}


class SemanticScholarAdapter(SourceAdapter):
    def __init__(self):
        self._api_key = settings.semantic_scholar_api_key

    @property
    def name(self) -> str:
        return "semantic_scholar"

    @property
    def supported_domains(self) -> list[str]:
        return [DomainID.AI_ML, DomainID.BIOTECH, DomainID.SCIENCE, DomainID.ECON]

    @property
    def rate_limit_per_day(self) -> int:
        return settings.semantic_scholar_daily_limit

    def is_available(self) -> bool:
        return bool(self._api_key)

    async def fetch(
        self, query: str, domain: str | None = None, max_results: int = 10
    ) -> list[RawArticle]:
        headers = {"x-api-key": self._api_key}
        params: dict = {
            "query": query,
            "limit": min(max_results, 100),
            "fields": "title,abstract,authors,year,citationCount,url,externalIds,publicationDate,fieldsOfStudy",
        }

        if domain and domain in _DOMAIN_FIELDS:
            params["fieldsOfStudy"] = _DOMAIN_FIELDS[domain]

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_BASE_URL}/paper/search",
                headers=headers,
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        articles = []
        for item in data.get("data", []):
            paper_url = item.get("url", "")
            ext_ids = item.get("externalIds") or {}
            if not paper_url and ext_ids.get("DOI"):
                paper_url = f"https://doi.org/{ext_ids['DOI']}"

            articles.append(
                RawArticle(
                    source_adapter=self.name,
                    source_url=paper_url,
                    title=item.get("title", ""),
                    authors=[
                        a.get("name", "") for a in (item.get("authors") or [])
                    ],
                    published_at=_parse_date(item.get("publicationDate")),
                    raw_content=item.get("abstract") or "",
                    media_type="paper",
                    extra={
                        "citation_count": item.get("citationCount", 0),
                        "fields_of_study": item.get("fieldsOfStudy"),
                        "arxiv_id": ext_ids.get("ArXiv"),
                    },
                )
            )
        return articles

    async def health_check(self) -> bool:
        try:
            headers = {"x-api-key": self._api_key}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{_BASE_URL}/paper/search",
                    headers=headers,
                    params={"query": "test", "limit": 1, "fields": "title"},
                )
                return resp.status_code == 200
        except Exception:
            logger.exception("Semantic Scholar health check failed")
            return False


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, AttributeError):
        return None
