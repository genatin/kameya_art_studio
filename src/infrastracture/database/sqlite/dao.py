import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastracture.database.sqlite.base import connection
from src.infrastracture.database.sqlite.models import MClass

logger = logging.getLogger(__name__)


@connection
async def add_mclass(
    session: AsyncSession | None, name: str, image_id: str, description: str = None
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
async def get_all_mclasses(session: AsyncSession | None) -> list[MClass]:
    return (await session.execute(select(MClass))).scalars().all()


@connection
async def update_mclass_name_by_name(
    session: AsyncSession | None, old_name: str, new_name: str
) -> MClass | None:
    try:
        mclass = await get_mclass_by_name(session, old_name)
        mclass.name = new_name
        await session.commit()
        return mclass
    except SQLAlchemyError as exc:
        logger.error(f"Update new_name mclass {old_name=} failed", exc_info=exc)
        await session.rollback()


@connection
async def update_mclass_description_by_name(
    session: AsyncSession | None, name: str, new_description: str
) -> MClass | None:
    try:
        mclass = await get_mclass_by_name(session, name)
        mclass.description = new_description
        await session.commit()
        return mclass
    except SQLAlchemyError as exc:
        logger.error(f"Update description mclass {name=} failed", exc_info=exc)
        await session.rollback()


@connection
async def update_mclass_photo_by_name(
    session: AsyncSession | None, name: str, file_id: str
) -> MClass | None:
    try:
        mclass = await get_mclass_by_name(session, name)
        mclass.file_id = file_id
        await session.commit()
        return mclass
    except SQLAlchemyError as exc:
        logger.error(f"Update description mclass {name=} failed", exc_info=exc)
        await session.rollback()


@connection
async def get_mclass_by_name(session: AsyncSession | None, name: str) -> MClass:
    return await session.scalar(select(MClass).filter_by(name=name))


@connection
async def remove_mclasses_by_name(session: AsyncSession | None, name: str) -> None:
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
