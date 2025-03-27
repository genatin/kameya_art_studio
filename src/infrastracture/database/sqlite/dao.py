import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.domen.models.activity_type import ActivityType as ActType
from src.infrastracture.database.sqlite.base import connection
from src.infrastracture.database.sqlite.models import Activity, ActivityType

logger = logging.getLogger(__name__)


@connection
async def get_act_type_by_name(session: AsyncSession, name: str) -> ActivityType | None:
    return await session.scalar(select(ActivityType).where(ActivityType.name == name))


@connection
async def add_activity(
    session: AsyncSession | None,
    activity_type: str,
    theme: str,
    image_id: str,
    description: str = None,
) -> Activity | None:
    try:
        act_type = await get_act_type_by_name(session, activity_type)
        if not act_type:
            return None
        activity = Activity(
            activity_type=act_type,
            theme=theme,
            file_id=image_id,
            description=description,
        )
        session.add(activity)
        logger.info(f"Added activity: {activity}")
        await session.commit()
        return activity
    except SQLAlchemyError as exc:
        logger.error("Adding activity failed", exc_info=exc)
        await session.rollback()


@connection
async def get_all_activity_by_type(
    session: AsyncSession | None, activity_type: str
) -> list[Activity]:
    stmt = (
        select(Activity)
        .join(ActivityType)  # Используем relationship для join
        .where(ActivityType.name == activity_type)
        .order_by(Activity.id.desc())
    )
    return await session.scalars(stmt)


@connection
async def update_activity_name_by_name(
    session: AsyncSession | None, activity_type: ActType, old_theme: str, new_theme: str
) -> Activity | None:
    try:
        activity = await get_activity_by_theme_and_type(
            session, activity_type, old_theme
        )
        activity.theme = new_theme
        await session.commit()
        return activity
    except SQLAlchemyError as exc:
        logger.error(f"Update new_name activity {old_theme=} failed", exc_info=exc)
        await session.rollback()


@connection
async def update_activity_description_by_name(
    session: AsyncSession | None, type_name: str, theme: str, new_description: str
) -> Activity | None:
    try:
        activity = await get_activity_by_theme_and_type(session, type_name, theme)
        activity.description = new_description
        await session.commit()
        return activity
    except SQLAlchemyError as exc:
        logger.error(f"Update description activity {theme=} failed", exc_info=exc)
        await session.rollback()


@connection
async def update_activity_fileid_by_name(
    session: AsyncSession | None, type_name: str, theme: str, file_id: str
) -> Activity | None:
    try:
        activity = await get_activity_by_theme_and_type(session, type_name, theme)
        activity.file_id = file_id
        await session.commit()
        return activity
    except SQLAlchemyError as exc:
        logger.error(f"Update description activity {theme=} failed", exc_info=exc)
        await session.rollback()


@connection
async def get_activity_by_theme_and_type(
    session: AsyncSession | None,
    type_name: str,
    theme: str,
) -> Activity:
    stmt = (
        select(Activity)
        .join(Activity.activity_type)  # Используем relationship для join
        .where(Activity.theme == theme, ActivityType.name == type_name)
    )
    return await session.scalar(stmt)


@connection
async def remove_activity_by_theme_and_type(
    session: AsyncSession | None, type_name: str, theme: str
) -> None:
    try:
        activity = await get_activity_by_theme_and_type(session, type_name, theme)
        if activity is None:
            logger.error(f"Mclass with {theme=} not found")
            return
        await session.delete(activity)
        await session.commit()
        logger.info(f"Mclass with {theme=} successful removed")
    except SQLAlchemyError as exc:
        logger.error("Removing activity failed", exc_info=exc)
        await session.rollback()
