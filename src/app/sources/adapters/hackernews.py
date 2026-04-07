import logging
from datetime import datetime, timezone

import httpx

from src.app.core.constants import DomainID
from src.app.schemas.article import RawArticle
from src.app.sources.base import SourceAdapter

logger = logging.getLogger(__name__)

_BASE_URL = "https://hacker-news.firebaseio.com/v0"


class HackerNewsAdapter(SourceAdapter):
    @property
    def name(self) -> str:
        return "hackernews"

    @property
    def supported_domains(self) -> list[str]:
        return [DomainID.TECH, DomainID.AI_ML, DomainID.OSS]

    @property
    def rate_limit_per_day(self) -> int:
        return 1000  # Effectively unlimited

    async def fetch(
        self, query: str, domain: str | None = None, max_results: int = 10
    ) -> list[RawArticle]:
        async with httpx.AsyncClient(timeout=15) as client:
            # Get top story IDs
            resp = await client.get(f"{_BASE_URL}/topstories.json")
            resp.raise_for_status()
            story_ids = resp.json()[:max_results * 3]  # Fetch extra for filtering

            articles = []
            for story_id in story_ids:
                if len(articles) >= max_results:
                    break
                item_resp = await client.get(f"{_BASE_URL}/item/{story_id}.json")
                item = item_resp.json()

                if not item or item.get("type") != "story" or not item.get("url"):
                    continue

                title = item.get("title", "")
                # Basic keyword filter if query is provided
                if query and query.lower() not in title.lower():
                    continue

                articles.append(
                    RawArticle(
                        source_adapter=self.name,
                        source_url=item["url"],
                        title=title,
                        authors=[item["by"]] if item.get("by") else [],
                        published_at=datetime.fromtimestamp(
                            item.get("time", 0), tz=timezone.utc
                        ),
                        raw_content="",  # HN stories link externally
                        media_type="post",
                        extra={
                            "hn_id": story_id,
                            "score": item.get("score", 0),
                            "comment_count": item.get("descendants", 0),
                            "hn_url": f"https://news.ycombinator.com/item?id={story_id}",
                        },
                    )
                )
        return articles

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{_BASE_URL}/topstories.json")
                return resp.status_code == 200
        except Exception:
            logger.exception("Hacker News health check failed")
            return False
