import logging
from collections.abc import Sequence
from datetime import date, datetime, time

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.domen.models.activity_type import ActivityType as ActType
from src.config import get_config
from src.infrastracture.database.sqlite.base import de_emojify
from src.infrastracture.database.sqlite.models import Activity, ActivityType, User

logger = logging.getLogger(__name__)


async def get_act_type_by_name(session: AsyncSession, name: str) -> ActivityType | None:
    return await session.scalar(
        select(ActivityType).where(ActivityType.name == de_emojify(name))
    )


async def add_activity(
    session: AsyncSession,
    activity_type: str,
    theme: str,
    image_id: str,
    content_type: str,
    description: str | None = None,
    date_time: datetime | None = None,
) -> Activity | None:
    try:
        act_type = await get_act_type_by_name(session, activity_type)
        if not act_type:
            return None
        activity = Activity(
            activity_type=act_type,
            theme=theme,
            file_id=image_id,
            content_type=content_type,
            description=description,
            date_time=date_time,
        )
        session.add(activity)
        logger.info('Added activity: %s', activity)
        await session.commit()
        return activity
    except SQLAlchemyError as e:
        logger.error('Adding activity failed: %s', e)
        await session.rollback()


async def get_all_activity_by_type(
    session: AsyncSession, activity_type: str
) -> Sequence[Activity]:
    stmt = (
        select(Activity)
        .join(ActivityType)
        .where(ActivityType.name == de_emojify(activity_type))
        .order_by(Activity.created_at.desc())
    )
    return (await session.scalars(stmt)).all()


async def update_activity_name_by_name(
    session: AsyncSession, activity_type: ActType, old_theme: str, new_theme: str
) -> Activity | None:
    try:
        activity = await get_activity_by_theme_and_type(session, activity_type, old_theme)
        activity.theme = new_theme
        await session.commit()
        return activity
    except SQLAlchemyError:
        logger.error('Update new_name activity %s failed', old_theme)
        await session.rollback()


async def update_activity_description_by_name(
    session: AsyncSession, activity_type: str, theme: str, new_description: str
) -> Activity | None:
    try:
        activity = await get_activity_by_theme_and_type(session, activity_type, theme)
        activity.description = new_description
        await session.commit()
        return activity
    except SQLAlchemyError:
        logger.error('Update description activity failed', theme)
        await session.rollback()


async def update_activity_date_by_name(
    session: AsyncSession, activity_type: str, theme: str, new_date: date | None
) -> Activity | None:
    try:
        activity = await get_activity_by_theme_and_type(session, activity_type, theme)
        old_datetime = activity.date_time
        if not new_date:
            activity.date_time = None
        elif old_datetime:
            activity.date_time = datetime.combine(
                new_date, old_datetime.time(), tzinfo=get_config().zone_info
            )
        else:
            activity.date_time = datetime(
                new_date.year,
                new_date.month,
                new_date.day,
                tzinfo=get_config().zone_info,
            )
        await session.commit()
        return activity
    except SQLAlchemyError:
        logger.error('Update description activity failed', theme)
        await session.rollback()


async def update_activity_time_by_name(
    session: AsyncSession,
    activity_type: str,
    theme: str,
    new_time: time | None = None,
) -> Activity | None:
    z_i = get_config().zone_info
    try:
        activity = await get_activity_by_theme_and_type(session, activity_type, theme)
        old_datetime = activity.date_time
        if old_datetime:
            if new_time:
                activity.date_time = datetime.combine(
                    old_datetime.date(), new_time, tzinfo=z_i
                )
            else:
                activity.date_time = datetime(
                    old_datetime.year, old_datetime.month, old_datetime.day, tzinfo=z_i
                )
            await session.commit()
            return activity
        return None
    except SQLAlchemyError:
        logger.error('Update description activity failed', theme)
        await session.rollback()


async def update_activity_fileid_by_name(
    session: AsyncSession,
    activity_type: str,
    theme: str,
    file_id: str,
    content_type: str,
) -> Activity | None:
    try:
        activity = await get_activity_by_theme_and_type(session, activity_type, theme)
        activity.file_id = file_id
        activity.content_type = content_type
        await session.commit()
        return activity
    except SQLAlchemyError:
        logger.error('Update description activity %s failed', theme)
        await session.rollback()


async def get_activity_by_theme_and_type(
    session: AsyncSession,
    activity_type: str,
    theme: str,
) -> Activity:
    stmt = (
        select(Activity)
        .join(Activity.activity_type)  # Используем relationship для join
        .where(Activity.theme == theme, ActivityType.name == de_emojify(activity_type))
    )
    return await session.scalar(stmt)


async def remove_activity_by_theme_and_type(
    session: AsyncSession, activity_type: str, theme: str
) -> None:
    try:
        activity = await get_activity_by_theme_and_type(session, activity_type, theme)
        if activity is None:
            logger.error('Mclass with %s not found', theme)
            return
        await session.delete(activity)
        await session.commit()
        logger.info('Mclass with %s successful removed', theme)
    except SQLAlchemyError:
        logger.error('Removing activity failed')
        await session.rollback()


async def add_user(
    session: AsyncSession,
    tg_id: int,
    nickname: str | None,
    phone: str,
    name: str,
    last_name: str,
) -> None:
    try:
        user = User(
            id=tg_id, nickname=nickname, phone=phone, name=name, last_name=last_name
        )
        session.add(user)
        await session.commit()
        logger.info('Added new user: %s', tg_id)
    except SQLAlchemyError:
        logger.error('Adding user failed')
        await session.rollback()


async def get_user(session: AsyncSession, tg_id: int) -> User | None:
    return await session.scalar(select(User).where(User.id == tg_id))


async def get_users(session: AsyncSession) -> list[User] | None:
    return (await session.scalars(select(User).order_by(User.created_at))).all()


async def delete_user(session: AsyncSession, tg_id: int) -> bool:
    user = await get_user(session, tg_id)
    if user:
        try:
            await session.delete(user)
            await session.commit()
            return True
        except SQLAlchemyError:
            logger.error('Adding user failed')
            await session.rollback()
    return False


async def update_user(session: AsyncSession, tg_id: int, update_data: dict) -> bool:
    try:
        stmt = update(User).where(User.id == tg_id).values(**update_data)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0
    except SQLAlchemyError:
        logger.error('Update user failed')
        await session.rollback()
        return False
