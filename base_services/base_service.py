from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    model = None

    @classmethod
    async def get_all(cls, session: AsyncSession, **data):
        query = select(cls.model).filter_by(**data)
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_one_or_none(cls, session: AsyncSession, to_update: bool = False, no_wait: bool = False, **data):
        query = select(cls.model).filter_by(**data)
        if to_update:
            query = query.with_for_update(nowait=no_wait)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, session: AsyncSession, **data):
        stmt = insert(cls.model).values(**data).returning(cls.model)
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one_or_none()
