import asyncio
import logging

from src.app.core.exceptions import SourceRateLimitError
from src.app.schemas.article import RawArticle
from src.app.sources.base import SourceAdapter
from src.app.sources.rate_limiter import rate_limiter
from src.app.sources.registry import source_registry
from src.app.sources.query_strategy import DOMAIN_SOURCE_PRIORITY, DOMAIN_DEFAULT_QUERIES

logger = logging.getLogger(__name__)


class AggregationService:
    """Orchestrates fetching from multiple sources using the query strategy."""

    async def fetch_for_domain(
        self, domain: str, max_per_source: int = 10
    ) -> list[RawArticle]:
        """Fetch articles for a domain using priority-ordered sources."""
        source_names = DOMAIN_SOURCE_PRIORITY.get(domain, [])
        queries = DOMAIN_DEFAULT_QUERIES.get(domain, ["latest news"])

        all_articles: list[RawArticle] = []
        tasks = []

        for source_name in source_names:
            adapter = source_registry.get(source_name)
            if not adapter:
                continue

            # Check rate limit before queuing
            can_call = await rate_limiter.can_call(
                source_name, adapter.rate_limit_per_day
            )
            if not can_call:
                logger.info("Rate limit reached for %s, skipping", source_name)
                continue

            # Use the first query for this domain
            query = queries[0] if queries else "latest news"
            tasks.append(self._fetch_from_source(adapter, query, domain, max_per_source))

        # Fan out to sources concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.warning("Source fetch failed: %s", result)
                continue
            all_articles.extend(result)

        logger.info(
            "Aggregated %d articles for domain '%s' from %d sources",
            len(all_articles),
            domain,
            len(tasks),
        )
        return all_articles

    async def fetch_for_domains(
        self, domains: list[str], max_per_source: int = 10
    ) -> list[RawArticle]:
        """Fetch articles for multiple domains."""
        all_articles: list[RawArticle] = []
        for domain in domains:
            articles = await self.fetch_for_domain(domain, max_per_source)
            all_articles.extend(articles)
        return all_articles

    async def search(
        self, query: str, max_results: int = 20
    ) -> list[RawArticle]:
        """Free-form search across all available sources."""
        tasks = []
        for adapter in source_registry.get_all():
            can_call = await rate_limiter.can_call(
                adapter.name, adapter.rate_limit_per_day
            )
            if can_call:
                tasks.append(
                    self._fetch_from_source(adapter, query, None, max_results)
                )

        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_articles: list[RawArticle] = []
        for result in results:
            if isinstance(result, Exception):
                continue
            all_articles.extend(result)

        return all_articles[:max_results]

    async def _fetch_from_source(
        self,
        adapter: SourceAdapter,
        query: str,
        domain: str | None,
        max_results: int,
    ) -> list[RawArticle]:
        """Fetch from a single source with rate limit recording."""
        recorded = await rate_limiter.record_call(
            adapter.name, adapter.rate_limit_per_day
        )
        if not recorded:
            raise SourceRateLimitError(adapter.name, "Daily budget exhausted")

        articles = await adapter.fetch(query, domain, max_results)
        logger.debug(
            "Fetched %d articles from %s (query: %s)",
            len(articles),
            adapter.name,
            query[:50],
        )
        return articles
