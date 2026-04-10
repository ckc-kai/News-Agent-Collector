import logging

from src.app.sources.base import SourceAdapter
from src.app.sources.adapters.tavily import TavilyAdapter
from src.app.sources.adapters.event_registry import EventRegistryAdapter
from src.app.sources.adapters.gnews import GNewsAdapter
from src.app.sources.adapters.newsdata import NewsDataAdapter
from src.app.sources.adapters.arxiv_source import ArxivAdapter
from src.app.sources.adapters.semantic_scholar import SemanticScholarAdapter
from src.app.sources.adapters.hackernews import HackerNewsAdapter
from src.app.sources.adapters.github_trending import GitHubTrendingAdapter
from src.app.sources.adapters.rss import RSSAdapter

logger = logging.getLogger(__name__)


class SourceRegistry:
    """Central registry of all source adapters.

    Automatically instantiates adapters and skips those missing API keys.
    """

    def __init__(self):
        self._adapters: dict[str, SourceAdapter] = {}
        self._init_adapters()

    def _init_adapters(self) -> None:
        adapter_classes: list[type[SourceAdapter]] = [
            TavilyAdapter,
            EventRegistryAdapter,
            GNewsAdapter,
            NewsDataAdapter,
            ArxivAdapter,
            SemanticScholarAdapter,
            HackerNewsAdapter,
            GitHubTrendingAdapter,
            RSSAdapter,
        ]

        for cls in adapter_classes:
            try:
                adapter = cls()
                if adapter.is_available():
                    self._adapters[adapter.name] = adapter
                    logger.info("Registered source adapter: %s", adapter.name)
                else:
                    logger.warning(
                        "Skipping %s — missing API key or config", adapter.name
                    )
            except Exception:
                logger.exception("Failed to initialize adapter: %s", cls.__name__)

    def get(self, name: str) -> SourceAdapter | None:
        return self._adapters.get(name)

    def get_all(self) -> list[SourceAdapter]:
        return list(self._adapters.values())

    def get_for_domain(self, domain: str) -> list[SourceAdapter]:
        return [
            a for a in self._adapters.values() if domain in a.supported_domains
        ]

    def get_names(self) -> list[str]:
        return list(self._adapters.keys())


# Singleton
source_registry = SourceRegistry()
