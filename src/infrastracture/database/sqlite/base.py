from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastracture.database.sqlite.db import Base, async_session, engine


def connection(func):
    async def wrapper(*args, **kwargs):
        if args and isinstance(args[0], AsyncSession) or kwargs.get("session"):
            return await func(*args, **kwargs)
        async with async_session() as session:
            return await func(session, *args, **kwargs)

    return wrapper


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
