import logging

from src.app.core.constants import DOMAIN_KEYWORDS
from src.app.pipeline.base import PipelineStage
from src.app.pipeline.context import PipelineContext
from src.app.schemas.article import NormalizedArticle

logger = logging.getLogger(__name__)


class ClassifierStage(PipelineStage):
    """Keyword-based domain classification (Phase 1).

    Classifies each article into primary + secondary domains by counting
    keyword matches in the title and content. Upgradable to LDA (Phase 1.5)
    or ML classifier (Phase 2) via feature flag.
    """

    @property
    def name(self) -> str:
        return "classifier"

    async def process(
        self, articles: list[NormalizedArticle], context: PipelineContext
    ) -> list[NormalizedArticle]:
        classified = 0
        for article in articles:
            # Skip if already classified (e.g., by source adapter)
            if article.domain:
                classified += 1
                continue

            text = f"{article.title} {article.raw_content}".lower()
            scores: dict[str, int] = {}

            for domain_id, keywords in DOMAIN_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw.lower() in text)
                if score > 0:
                    scores[domain_id] = score

            if scores:
                sorted_domains = sorted(scores, key=scores.get, reverse=True)
                article.domain = sorted_domains[0]
                article.secondary_domains = sorted_domains[1:3]  # Top 2 secondary
                classified += 1
            else:
                # Default to "tech" if no keywords match
                article.domain = "tech"

        context.record_stat(self.name, "classified", classified)
        context.record_stat(self.name, "unclassified", len(articles) - classified)
        return articles
