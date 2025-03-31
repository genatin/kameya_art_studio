import emoji
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastracture.database.sqlite.db import Base, async_session_maker, engine
from src.infrastracture.database.sqlite.models import ActivityType, ActivityTypeEnum


def de_emojify(text):
    return emoji.replace_emoji(text, replace="")


async def _create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def connection(func):
    async def wrapper(*args, **kwargs):
        if args and isinstance(args[0], AsyncSession) or kwargs.get("session"):
            return await func(*args, **kwargs)
        async with async_session_maker() as session:
            return await func(session, *args, **kwargs)

    return wrapper


async def init_db():
    await _create_db()
    async with async_session_maker() as session:
        existing_types = (await session.execute(select(ActivityType.name))).all()
        try:
            # Создаем предопределенные типы, если их нет
            for activity_type in ActivityTypeEnum:
                safe_str = de_emojify(activity_type)
                if safe_str not in existing_types:
                    session.add(ActivityType(name=safe_str))

            await session.commit()
        except IntegrityError:
            await session.rollback()
        finally:
            await session.close()
