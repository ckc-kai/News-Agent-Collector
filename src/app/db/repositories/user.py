from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.db.repositories.base import BaseRepository
from src.app.models.user import User, UserDomainPreference


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_with_preferences(self, user_id: str) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.domain_preferences))
            .where(User.id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_domain_preference(
        self,
        user_id: str,
        domain_id: str,
        weight: float | None = None,
        depth_preference: str | None = None,
    ) -> UserDomainPreference | None:
        stmt = select(UserDomainPreference).where(
            UserDomainPreference.user_id == user_id,
            UserDomainPreference.domain_id == domain_id,
        )
        result = await self._session.execute(stmt)
        pref = result.scalar_one_or_none()

        if not pref:
            return None

        if weight is not None:
            pref.weight = max(0.0, min(1.0, weight))
        if depth_preference is not None:
            pref.depth_preference = depth_preference

        await self._session.flush()
        return pref
