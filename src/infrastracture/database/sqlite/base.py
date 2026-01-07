
import emoji
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.infrastracture.database.sqlite.db import Base, engine
from src.infrastracture.database.sqlite.models import ActivityType, ActivityTypeEnum


def de_emojify(text: str) -> str:
    return emoji.replace_emoji(text.strip(), replace='')


async def _create_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def init_db(session_maker) -> None:
    await _create_db()
    async with session_maker() as session:
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
