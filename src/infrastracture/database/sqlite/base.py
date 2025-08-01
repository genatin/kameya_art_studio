from collections.abc import Callable

import emoji

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastracture.database.sqlite.db import Base
from src.infrastracture.database.sqlite.db import async_session_maker
from src.infrastracture.database.sqlite.db import engine
from src.infrastracture.database.sqlite.models import ActivityType
from src.infrastracture.database.sqlite.models import ActivityTypeEnum


def de_emojify(text: str) -> str:
    return emoji.replace_emoji(text.strip(), replace='')


async def _create_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def connection(func) -> Callable:
    async def wrapper(*args, **kwargs) -> Callable:
        if (args and isinstance(args[0], AsyncSession)) or kwargs.get('session'):
            return await func(*args, **kwargs)
        async with async_session_maker() as session:
            return await func(session, *args, **kwargs)

    return wrapper


async def init_db() -> None:
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
