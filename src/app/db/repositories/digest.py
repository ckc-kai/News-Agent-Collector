from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.db.repositories.base import BaseRepository
from src.app.models.digest import Digest, DigestItem


class DigestRepository(BaseRepository[Digest]):
    def __init__(self, session: AsyncSession):
        super().__init__(Digest, session)

    async def get_latest_for_user(self, user_id: str) -> Digest | None:
        stmt = (
            select(Digest)
            .options(selectinload(Digest.items))
            .where(Digest.user_id == user_id)
            .order_by(Digest.generated_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_items(self, digest_id: str) -> Digest | None:
        stmt = (
            select(Digest)
            .options(selectinload(Digest.items))
            .where(Digest.id == digest_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
