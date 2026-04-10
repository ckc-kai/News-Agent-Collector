import asyncio
import logging
import random

from src.app.core.exceptions import SourceRateLimitError
from src.app.schemas.article import RawArticle
from src.app.services.topic_expander import TopicExpander
from src.app.sources.base import SourceAdapter
from src.app.sources.rate_limiter import rate_limiter
from src.app.sources.registry import source_registry
from src.app.sources.query_strategy import DOMAIN_SOURCE_PRIORITY, DOMAIN_DEFAULT_QUERIES, NATURE_TO_SOURCES

# Singleton for dynamic query generation for custom (unknown) domains
topic_expander = TopicExpander()

logger = logging.getLogger(__name__)

MAX_PER_ROUND = 15
MAX_PER_DOMAIN = 3
EXPLORATION_SLOTS = 3  # 1-3 articles in "You May Also Like"
EXPLORATION_WEIGHT = 0.1  # Low initial weight for exploration clicks


class AggregationService:
    """Orchestrates fetching from multiple sources using the query strategy."""

    async def fetch_for_domain(
        self, domain: str, max_per_source: int = 10
    ) -> list[RawArticle]:
        """Fetch articles for a domain using priority-ordered sources.

        Known domains (DomainID values) use hand-tuned source lists and queries.
        Custom user-typed domains are classified by the LLM into source-affinity
        natures (academic / industry_news / community_tech / general_news), and
        only the 2-4 most relevant sources for that nature are queried.
        """
        source_names = DOMAIN_SOURCE_PRIORITY.get(domain, [])
        queries = DOMAIN_DEFAULT_QUERIES.get(domain, [])

        # Dynamic routing for custom (user-typed) domains
        if not source_names:
            try:
                natures = await topic_expander.classify_source_affinity(domain)
                seen: set[str] = set()
                source_names = []
                for nature in natures:
                    for src in NATURE_TO_SOURCES.get(nature, []):
                        if src not in seen:
                            seen.add(src)
                            source_names.append(src)
            except Exception:
                logger.warning("Nature classification failed for %s, using general fallback", domain)
                source_names = NATURE_TO_SOURCES["general_news"]

            try:
                queries = await topic_expander.generate_queries(domain)
            except Exception:
                logger.warning("Dynamic query generation failed for %s", domain)
                queries = [f"latest {domain} news"]

        if not queries:
            queries = ["latest news"]

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

    async def fetch_smart(
        self,
        domains_with_weights: list[tuple[str, float]],
        max_per_round: int = MAX_PER_ROUND,
    ) -> list[RawArticle]:
        """Fetch with smart domain sampling: prioritize high-weight domains,
        sprinkle in 1-3 random exploration articles from lower-weight ones.
        Total capped at max_per_round."""
        if not domains_with_weights:
            return []

        sorted_dw = sorted(domains_with_weights, key=lambda x: x[1], reverse=True)
        total_weight = sum(w for _, w in sorted_dw)
        if total_weight == 0:
            total_weight = 1.0

        # Allocate articles per domain proportional to weight
        allocations: dict[str, int] = {}
        remaining = max_per_round

        for domain, weight in sorted_dw:
            if remaining <= 0:
                break
            share = max(1, round((weight / total_weight) * max_per_round))
            share = min(share, MAX_PER_DOMAIN, remaining)
            allocations[domain] = share
            remaining -= share

        # Distribute leftover budget to random unallocated domains (exploration)
        unallocated = [d for d, _ in sorted_dw if d not in allocations]
        if remaining > 0 and unallocated:
            picks = random.sample(unallocated, min(remaining, len(unallocated)))
            for d in picks:
                allocations[d] = 1
                remaining -= 1

        # If still remaining, boost top domains (up to MAX_PER_DOMAIN each)
        if remaining > 0:
            for domain, _ in sorted_dw:
                if remaining <= 0:
                    break
                current = allocations.get(domain, 0)
                if current < MAX_PER_DOMAIN:
                    extra = min(MAX_PER_DOMAIN - current, remaining)
                    allocations[domain] = current + extra
                    remaining -= extra

        # Fetch all domains concurrently
        domain_order = list(allocations.keys())
        tasks = [
            self.fetch_for_domain(domain, max_per_source=allocations[domain])
            for domain in domain_order
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_articles: list[RawArticle] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning("Fetch failed for %s: %s", domain_order[i], result)
                continue
            domain_articles = list(result)
            target = allocations[domain_order[i]]
            if len(domain_articles) > target:
                random.shuffle(domain_articles)
                domain_articles = domain_articles[:target]
            all_articles.extend(domain_articles)

        # Final trim
        if len(all_articles) > max_per_round:
            random.shuffle(all_articles)
            all_articles = all_articles[:max_per_round]

        logger.info(
            "Smart fetch: %d articles from %d domains (budget: %d)",
            len(all_articles), len(allocations), max_per_round,
        )
        return all_articles

    async def fetch_smart_with_exploration(
        self,
        domains_with_weights: list[tuple[str, float]],
        all_known_domains: list[str] | None = None,
        max_per_round: int = MAX_PER_ROUND,
    ) -> tuple[list[RawArticle], list[RawArticle]]:
        """Fetch main articles + exploration articles from unselected domains.
        Returns (main_articles, exploration_articles)."""
        # Fetch main articles via existing fetch_smart
        main_articles = await self.fetch_smart(domains_with_weights, max_per_round)

        # Determine exploration domains
        user_domain_ids = {d for d, _ in domains_with_weights}
        candidate_domains = [
            d for d in (all_known_domains or [])
            if d not in user_domain_ids
        ]

        if not candidate_domains:
            return main_articles, []

        # Pick random exploration domains
        num_explore = min(EXPLORATION_SLOTS, len(candidate_domains))
        explore_domains = random.sample(candidate_domains, num_explore)

        # Fetch 1 article per exploration domain
        tasks = [self.fetch_for_domain(d, max_per_source=1) for d in explore_domains]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        exploration_articles: list[RawArticle] = []
        for result in results:
            if isinstance(result, Exception):
                continue
            for article in result[:1]:  # max 1 per domain
                article.extra["is_exploration"] = True
                article.extra["exploration_weight"] = EXPLORATION_WEIGHT
                exploration_articles.append(article)

        logger.info(
            "Exploration: %d articles from %d domains",
            len(exploration_articles), len(explore_domains),
        )
        return main_articles, exploration_articles

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
