from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.repositories.base import BaseRepository
from src.app.models.article import Article


class ArticleRepository(BaseRepository[Article]):
    def __init__(self, session: AsyncSession):
        super().__init__(Article, session)

    async def get_by_canonical_url(self, canonical_url: str) -> Article | None:
        stmt = select(Article).where(Article.canonical_url == canonical_url)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_domain(
        self, domain: str, limit: int = 50, days: int = 7
    ) -> list[Article]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(Article)
            .where(Article.domain == domain, Article.published_at >= cutoff)
            .order_by(Article.published_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent(self, limit: int = 100, days: int = 7) -> list[Article]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(Article)
            .where(Article.published_at >= cutoff)
            .order_by(Article.published_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_unsummarized(self, limit: int = 50) -> list[Article]:
        stmt = (
            select(Article)
            .where(Article.summary_l1.is_(None))
            .order_by(Article.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_domain(self) -> dict[str, int]:
        stmt = (
            select(Article.domain, func.count())
            .group_by(Article.domain)
        )
        result = await self._session.execute(stmt)
        return {row[0]: row[1] for row in result.all() if row[0]}
