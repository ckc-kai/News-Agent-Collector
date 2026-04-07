import asyncio
import logging
from datetime import datetime

import arxiv

from src.app.core.constants import DomainID
from src.app.schemas.article import RawArticle
from src.app.sources.base import SourceAdapter

logger = logging.getLogger(__name__)

# Map domains to arxiv category prefixes
_DOMAIN_CATEGORIES: dict[str, list[str]] = {
    DomainID.AI_ML: ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "stat.ML"],
    DomainID.TECH: ["cs.SE", "cs.DC", "cs.NI", "cs.CR"],
    DomainID.SCIENCE: ["physics", "math", "astro-ph", "quant-ph"],
    DomainID.BIOTECH: ["q-bio", "cs.CE"],
    DomainID.ECON: ["econ", "q-fin"],
}

# Polite delay between calls (PRD: 3s)
_CALL_DELAY = 3.0


class ArxivAdapter(SourceAdapter):
    @property
    def name(self) -> str:
        return "arxiv"

    @property
    def supported_domains(self) -> list[str]:
        return [DomainID.AI_ML, DomainID.TECH, DomainID.SCIENCE, DomainID.BIOTECH, DomainID.ECON]

    @property
    def rate_limit_per_day(self) -> int:
        return 100

    async def fetch(
        self, query: str, domain: str | None = None, max_results: int = 10
    ) -> list[RawArticle]:
        # Build category-scoped query if domain is specified
        search_query = query
        if domain and domain in _DOMAIN_CATEGORIES:
            cats = " OR ".join(f"cat:{c}" for c in _DOMAIN_CATEGORIES[domain])
            search_query = f"({query}) AND ({cats})"

        client = arxiv.Client(num_retries=2, page_size=max_results)
        search = arxiv.Search(
            query=search_query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        # arxiv library is synchronous, run in executor
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None, lambda: list(client.results(search))
        )

        # Polite delay
        await asyncio.sleep(_CALL_DELAY)

        articles = []
        for result in results:
            articles.append(
                RawArticle(
                    source_adapter=self.name,
                    source_url=result.entry_id,
                    title=result.title.replace("\n", " "),
                    authors=[a.name for a in result.authors],
                    published_at=result.published.replace(
                        tzinfo=result.published.tzinfo or __import__("datetime").timezone.utc
                    ),
                    raw_content=result.summary.replace("\n", " "),
                    media_type="paper",
                    extra={
                        "categories": result.categories,
                        "pdf_url": result.pdf_url,
                        "primary_category": result.primary_category,
                        "doi": result.doi,
                    },
                )
            )
        return articles

    async def health_check(self) -> bool:
        try:
            client = arxiv.Client(num_retries=1)
            search = arxiv.Search(query="test", max_results=1)
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, lambda: list(client.results(search))
            )
            return len(results) > 0
        except Exception:
            logger.exception("arxiv health check failed")
            return False
