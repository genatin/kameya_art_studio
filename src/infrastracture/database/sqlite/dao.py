import logging
from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastracture.database.sqlite.base import connection
from src.infrastracture.database.sqlite.models import MClass

logger = logging.getLogger(__name__)


@connection
async def add_mclass(
    session: AsyncSession, name: str, image_id: str, description: str = None
):
    try:
        mclass = MClass(name=name, file_id=image_id, description=description)
        session.add(mclass)
        logger.info(f"Added mclass: {name}")
        await session.commit()

    except SQLAlchemyError as exc:
        logger.error("Adding mclass failed", exc_info=exc)
        await session.rollback()


@connection
async def get_all_mclasses(session: AsyncSession) -> list[MClass]:
    return (await session.execute(select(MClass))).scalars().all()


@connection
async def get_mclass_by_name(session: AsyncSession, name: str) -> MClass:
    return await session.scalar(select(MClass).filter_by(name=name))


@connection
async def remove_mclasses_by_name(session: AsyncSession, name: str) -> None:
    try:
        mclass = await get_mclass_by_name(session, name)
        if mclass is None:
            logger.error(f"Mclass with {name=} not found")
            return
        await session.delete(mclass)
        await session.commit()
        logger.info(f"Mclass with {name=} successful removed")
    except SQLAlchemyError as exc:
        logger.error("Removing mclass failed", exc_info=exc)
        await session.rollback()
