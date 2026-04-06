import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.article import Article
from src.app.pipeline.base import PipelineStage
from src.app.pipeline.context import PipelineContext
from src.app.schemas.article import NormalizedArticle

logger = logging.getLogger(__name__)


class StorerStage(PipelineStage):
    """Persists normalized articles to PostgreSQL via upsert."""

    @property
    def name(self) -> str:
        return "storer"

    async def process(
        self, articles: list[NormalizedArticle], context: PipelineContext
    ) -> list[NormalizedArticle]:
        if not context.db_session:
            logger.warning("No DB session in pipeline context, skipping storage")
            return articles

        session: AsyncSession = context.db_session
        inserted = 0
        updated = 0

        for article in articles:
            # Check if article already exists by canonical URL
            stmt = select(Article).where(
                Article.canonical_url == article.canonical_url
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update summaries and metadata if they were missing
                if not existing.summary_l1 and article.summary_l1:
                    existing.summary_l1 = article.summary_l1
                    existing.summary_l2 = article.summary_l2
                    existing.summary_l3 = article.summary_l3
                if not existing.domain and article.domain:
                    existing.domain = article.domain
                    existing.secondary_domains = article.secondary_domains
                if article.tags and not existing.tags:
                    existing.tags = article.tags
                updated += 1
            else:
                db_article = Article(
                    id=article.id,
                    source_adapter=article.source_adapter,
                    source_url=article.source_url,
                    canonical_url=article.canonical_url,
                    content_hash=article.content_hash,
                    title=article.title,
                    authors=article.authors,
                    published_at=article.published_at,
                    raw_content=article.raw_content,
                    domain=article.domain,
                    secondary_domains=article.secondary_domains,
                    tags=article.tags,
                    language=article.language,
                    media_type=article.media_type,
                    importance_score=article.importance_score,
                    summary_l1=article.summary_l1,
                    summary_l2=article.summary_l2,
                    summary_l3=article.summary_l3,
                    merged_source_urls=article.merged_source_urls,
                )
                session.add(db_article)
                inserted += 1

        await session.flush()
        context.record_stat(self.name, "inserted", inserted)
        context.record_stat(self.name, "updated", updated)
        logger.info("Stored %d new, %d updated articles", inserted, updated)
        return articles
