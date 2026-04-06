import asyncio
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from src.app.core.constants import DomainID
from src.app.schemas.article import RawArticle
from src.app.sources.base import SourceAdapter

logger = logging.getLogger(__name__)

# Default RSS feeds per domain (extensible via config)
DEFAULT_FEEDS: dict[str, list[dict[str, str]]] = {
    DomainID.AI_ML: [
        {"url": "https://arxiv.org/rss/cs.AI", "name": "arxiv CS.AI"},
        {"url": "https://blog.google/technology/ai/rss/", "name": "Google AI Blog"},
    ],
    DomainID.TECH: [
        {"url": "https://feeds.arstechnica.com/arstechnica/index", "name": "Ars Technica"},
        {"url": "https://www.theverge.com/rss/index.xml", "name": "The Verge"},
        {"url": "https://techcrunch.com/feed/", "name": "TechCrunch"},
    ],
    DomainID.ECON: [
        {"url": "https://feeds.reuters.com/reuters/businessNews", "name": "Reuters Business"},
    ],
    DomainID.POLITICS: [
        {"url": "https://feeds.bbci.co.uk/news/politics/rss.xml", "name": "BBC Politics"},
        {"url": "https://feeds.npr.org/1001/rss.xml", "name": "NPR News"},
    ],
    DomainID.SCIENCE: [
        {"url": "https://www.nature.com/nature.rss", "name": "Nature"},
        {"url": "https://www.science.org/rss/news_current.xml", "name": "Science"},
    ],
    DomainID.SUSTAINABILITY: [
        {"url": "https://www.carbonbrief.org/feed", "name": "Carbon Brief"},
    ],
    DomainID.OSS: [
        {"url": "https://github.blog/feed/", "name": "GitHub Blog"},
    ],
}


class RSSAdapter(SourceAdapter):
    def __init__(self, custom_feeds: dict[str, list[dict[str, str]]] | None = None):
        self._feeds = custom_feeds or DEFAULT_FEEDS

    @property
    def name(self) -> str:
        return "rss"

    @property
    def supported_domains(self) -> list[str]:
        return list(self._feeds.keys())

    @property
    def rate_limit_per_day(self) -> int:
        return 999999  # Unlimited

    async def fetch(
        self, query: str, domain: str | None = None, max_results: int = 10
    ) -> list[RawArticle]:
        # Get feeds for the requested domain, or all feeds
        if domain and domain in self._feeds:
            feeds = self._feeds[domain]
        else:
            feeds = [f for feed_list in self._feeds.values() for f in feed_list]

        loop = asyncio.get_event_loop()
        articles: list[RawArticle] = []

        for feed_info in feeds:
            if len(articles) >= max_results:
                break
            try:
                parsed = await loop.run_in_executor(
                    None, feedparser.parse, feed_info["url"]
                )
                for entry in parsed.entries[:max_results]:
                    title = entry.get("title", "")
                    # Basic query filter
                    if query and query.lower() not in title.lower():
                        continue

                    articles.append(
                        RawArticle(
                            source_adapter=self.name,
                            source_url=entry.get("link", ""),
                            title=title,
                            authors=(
                                [entry.author] if hasattr(entry, "author") and entry.author else []
                            ),
                            published_at=_parse_feed_date(entry),
                            raw_content=entry.get("summary", "") or entry.get("description", ""),
                            extra={
                                "feed_name": feed_info["name"],
                                "feed_url": feed_info["url"],
                            },
                        )
                    )
            except Exception:
                logger.warning("Failed to parse RSS feed: %s", feed_info["url"])
                continue

        return articles[:max_results]

    async def health_check(self) -> bool:
        # Check if at least one feed is reachable
        all_feeds = [f for feeds in self._feeds.values() for f in feeds]
        if not all_feeds:
            return False
        try:
            loop = asyncio.get_event_loop()
            parsed = await loop.run_in_executor(
                None, feedparser.parse, all_feeds[0]["url"]
            )
            return bool(parsed.entries)
        except Exception:
            logger.exception("RSS health check failed")
            return False


def _parse_feed_date(entry) -> datetime | None:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            from time import mktime
            return datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)
        except (TypeError, ValueError, OverflowError):
            pass
    if hasattr(entry, "published") and entry.published:
        try:
            return parsedate_to_datetime(entry.published)
        except (TypeError, ValueError):
            pass
    return None
