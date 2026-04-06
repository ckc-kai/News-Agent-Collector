from typing import TypeVar, Generic, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: AsyncSession):
        self._model = model
        self._session = session

    async def get_by_id(self, id: str) -> T | None:
        return await self._session.get(self._model, id)

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        stmt = select(self._model).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj: T) -> T:
        self._session.add(obj)
        await self._session.flush()
        return obj

    async def delete(self, obj: T) -> None:
        await self._session.delete(obj)
        await self._session.flush()
