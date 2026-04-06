import logging

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.app.pipeline.base import PipelineStage
from src.app.pipeline.context import PipelineContext
from src.app.schemas.article import NormalizedArticle

logger = logging.getLogger(__name__)

# PRD: cosine similarity on TF-IDF vectors of titles; threshold ≥ 0.85 = duplicate
_SIMILARITY_THRESHOLD = 0.85


class DeduplicatorStage(PipelineStage):
    @property
    def name(self) -> str:
        return "deduplicator"

    async def process(
        self, articles: list[NormalizedArticle], context: PipelineContext
    ) -> list[NormalizedArticle]:
        if len(articles) <= 1:
            return articles

        # Step 1: URL-based dedup (exact canonical URL match)
        seen_urls: dict[str, int] = {}
        url_deduped: list[NormalizedArticle] = []
        for article in articles:
            key = article.canonical_url
            if key in seen_urls:
                # Merge source URLs
                existing = url_deduped[seen_urls[key]]
                if article.source_url not in existing.merged_source_urls:
                    existing.merged_source_urls.append(article.source_url)
            else:
                seen_urls[key] = len(url_deduped)
                url_deduped.append(article)

        url_dupes = len(articles) - len(url_deduped)

        # Step 2: Title similarity dedup via TF-IDF
        if len(url_deduped) <= 1:
            context.record_stat(self.name, "url_duplicates", url_dupes)
            context.record_stat(self.name, "title_duplicates", 0)
            return url_deduped

        titles = [a.title for a in url_deduped]
        try:
            vectorizer = TfidfVectorizer(stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(titles)
            sim_matrix = cosine_similarity(tfidf_matrix)
        except ValueError:
            # All titles might be empty or stop words only
            context.record_stat(self.name, "url_duplicates", url_dupes)
            context.record_stat(self.name, "title_duplicates", 0)
            return url_deduped

        # Mark duplicates (keep the first occurrence)
        is_duplicate = [False] * len(url_deduped)
        for i in range(len(url_deduped)):
            if is_duplicate[i]:
                continue
            for j in range(i + 1, len(url_deduped)):
                if is_duplicate[j]:
                    continue
                if sim_matrix[i][j] >= _SIMILARITY_THRESHOLD:
                    is_duplicate[j] = True
                    # Merge source URL from duplicate
                    if url_deduped[j].source_url not in url_deduped[i].merged_source_urls:
                        url_deduped[i].merged_source_urls.append(
                            url_deduped[j].source_url
                        )

        result = [a for a, dup in zip(url_deduped, is_duplicate) if not dup]
        title_dupes = len(url_deduped) - len(result)

        context.record_stat(self.name, "url_duplicates", url_dupes)
        context.record_stat(self.name, "title_duplicates", title_dupes)
        logger.info(
            "Deduplication: %d URL dupes, %d title dupes removed",
            url_dupes,
            title_dupes,
        )
        return result
