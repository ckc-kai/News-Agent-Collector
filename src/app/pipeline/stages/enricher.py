import logging

from sklearn.feature_extraction.text import TfidfVectorizer

from src.app.pipeline.base import PipelineStage
from src.app.pipeline.context import PipelineContext
from src.app.schemas.article import NormalizedArticle

logger = logging.getLogger(__name__)


class EnricherStage(PipelineStage):
    """Extracts keywords (tags) and computes importance scores."""

    @property
    def name(self) -> str:
        return "enricher"

    async def process(
        self, articles: list[NormalizedArticle], context: PipelineContext
    ) -> list[NormalizedArticle]:
        # Extract keywords via TF-IDF across the batch
        if articles:
            self._extract_keywords(articles)
            self._compute_importance(articles)

        context.record_stat(self.name, "enriched", len(articles))
        return articles

    def _extract_keywords(self, articles: list[NormalizedArticle]) -> None:
        texts = [f"{a.title} {a.raw_content}" for a in articles]
        try:
            vectorizer = TfidfVectorizer(
                stop_words="english", max_features=1000, max_df=0.8
            )
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()

            for i, article in enumerate(articles):
                if article.tags:
                    continue  # Already has tags
                row = tfidf_matrix[i].toarray().flatten()
                top_indices = row.argsort()[-5:][::-1]  # Top 5 keywords
                article.tags = [
                    feature_names[idx] for idx in top_indices if row[idx] > 0
                ]
        except ValueError:
            pass  # Empty corpus

    def _compute_importance(self, articles: list[NormalizedArticle]) -> None:
        """Compute importance score from source-specific engagement signals."""
        for article in articles:
            if article.importance_score > 0:
                continue  # Already scored

            score = 0.0

            # Source-specific signals from extra metadata
            # (set by adapters: citations, stars, upvotes, etc.)
            # These are no longer in NormalizedArticle.extra, so we derive
            # from media_type and other available fields.

            # Papers with more authors tend to be from larger teams
            if article.media_type == "paper" and len(article.authors) > 3:
                score += 0.1

            # Multi-source articles are more important
            if len(article.merged_source_urls) > 0:
                score += min(len(article.merged_source_urls) * 0.15, 0.3)

            # Having rich content is a signal
            if len(article.raw_content) > 500:
                score += 0.1

            article.importance_score = min(score, 1.0)
