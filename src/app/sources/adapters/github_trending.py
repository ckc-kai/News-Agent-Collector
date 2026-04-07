import logging
from datetime import datetime, timezone

import httpx

from src.app.config import settings
from src.app.core.constants import DomainID
from src.app.schemas.article import RawArticle
from src.app.sources.base import SourceAdapter

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.github.com"

# Language filters per domain
_DOMAIN_LANGUAGES: dict[str, list[str]] = {
    DomainID.AI_ML: ["python", "jupyter-notebook"],
    DomainID.TECH: ["go", "rust", "java", "c++"],
    DomainID.OSS: [],  # All languages
}


class GitHubTrendingAdapter(SourceAdapter):
    def __init__(self):
        self._token = settings.github_token

    @property
    def name(self) -> str:
        return "github_trending"

    @property
    def supported_domains(self) -> list[str]:
        return [DomainID.AI_ML, DomainID.TECH, DomainID.OSS]

    @property
    def rate_limit_per_day(self) -> int:
        return settings.github_daily_limit

    def is_available(self) -> bool:
        return bool(self._token)

    async def fetch(
        self, query: str, domain: str | None = None, max_results: int = 10
    ) -> list[RawArticle]:
        headers = {
            "Authorization": f"token {self._token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Search for recently created/updated repos with high stars
        search_query = f"{query} stars:>10 pushed:>2026-03-01"

        if domain and domain in _DOMAIN_LANGUAGES and _DOMAIN_LANGUAGES[domain]:
            lang = _DOMAIN_LANGUAGES[domain][0]
            search_query += f" language:{lang}"

        params = {
            "q": search_query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(max_results, 30),
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_BASE_URL}/search/repositories",
                headers=headers,
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        articles = []
        for repo in data.get("items", []):
            articles.append(
                RawArticle(
                    source_adapter=self.name,
                    source_url=repo.get("html_url", ""),
                    title=f"{repo.get('full_name', '')}: {repo.get('description', '') or 'No description'}",
                    authors=[repo.get("owner", {}).get("login", "")],
                    published_at=_parse_date(repo.get("created_at")),
                    raw_content=repo.get("description", "") or "",
                    media_type="repo",
                    extra={
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0),
                        "language": repo.get("language"),
                        "topics": repo.get("topics", []),
                        "updated_at": repo.get("updated_at"),
                    },
                )
            )
        return articles

    async def health_check(self) -> bool:
        try:
            headers = {
                "Authorization": f"token {self._token}",
                "Accept": "application/vnd.github.v3+json",
            }
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{_BASE_URL}/rate_limit", headers=headers)
                return resp.status_code == 200
        except Exception:
            logger.exception("GitHub health check failed")
            return False


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
