import logging
from collections.abc import Sequence
from datetime import date, datetime, time

from sqlalchemy import select, update
from sqlalchemy.exc import MultipleResultsFound, NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import get_config
from src.infrastracture.database.sqlite.base import de_emojify
from src.infrastracture.database.sqlite.models import Activity, ActivityType, User

logger = logging.getLogger(__name__)


async def get_act_type_by_name(session: AsyncSession, name: str) -> ActivityType | None:
    """Получить тип активности по имени.

    Args:
        session: Асинхронная сессия SQLAlchemy
        name: Название типа активности

    Returns:
        Объект ActivityType или None
    """
    try:
        stmt = select(ActivityType).where(ActivityType.name == de_emojify(name))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error('Error getting activity type %s: %s', name, e)
        return None


async def add_activity(
    session: AsyncSession,
    activity_type: str,
    theme: str,
    image_id: str,
    content_type: str,
    description: str | None = None,
    date_time: datetime | None = None,
) -> Activity | None:
    """Добавить новую активность.

    Args:
        session: Асинхронная сессия SQLAlchemy
        activity_type: Тип активности
        theme: Тема активности
        image_id: ID изображения
        content_type: Тип контента
        description: Описание (опционально)
        date_time: Дата и время (опционально)

    Returns:
        Объект Activity или None при ошибке
    """
    try:
        async with session.begin():
            # Получаем тип активности
            act_type = await get_act_type_by_name(session, activity_type)
            if not act_type:
                logger.error("Activity type '%s' not found", activity_type)
                return None

            # Создаем активность
            activity = Activity(
                activity_type=act_type,
                theme=theme,
                file_id=image_id,
                content_type=content_type,
                description=description,
                date_time=date_time,
            )
            session.add(activity)

        # Обновляем объект из БД (не в транзакции)
        logger.info('Added activity: %s (%s)', theme, activity_type)
        return activity

    except SQLAlchemyError as e:
        logger.error('Adding activity failed: %s', e)
        return None


async def get_all_activity_by_type(
    session: AsyncSession, activity_type: str
) -> Sequence[Activity]:
    """Получить все активности по типу.

    Args:
        session: Асинхронная сессия SQLAlchemy
        activity_type: Тип активности

    Returns:
        Список активностей
    """
    try:
        stmt = (
            select(Activity)
            .join(ActivityType)
            .where(ActivityType.name == de_emojify(activity_type))
            .order_by(Activity.created_at.desc())
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error('Error getting activities for type %s: %s', activity_type, e)
        return []


async def get_activity_by_theme_and_type(
    session: AsyncSession,
    activity_type: str,
    theme: str,
) -> Activity | None:
    """Получить активность по теме и типу.

    Args:
        session: Асинхронная сессия SQLAlchemy
        activity_type: Тип активности
        theme: Тема активности

    Returns:
        Объект Activity или None
    """
    try:
        stmt = (
            select(Activity)
            .options(selectinload(Activity.activity_type))
            .join(Activity.activity_type)
            .where(
                Activity.theme == theme, ActivityType.name == de_emojify(activity_type)
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    except (NoResultFound, MultipleResultsFound) as e:
        logger.error('Error getting activity %s (%s): %s', theme, activity_type, e)
        return None
    except SQLAlchemyError as e:
        logger.error('Database error getting activity %s: %s', theme, e)
        return None


async def _update_activity(
    session: AsyncSession,
    activity_type: str,
    theme: str,
    update_values: dict,
) -> Activity | None:
    """Внутренняя функция для обновления активности.

    Args:
        session: Асинхронная сессия SQLAlchemy
        activity_type: Тип активности
        theme: Тема активности
        update_values: Словарь с полями для обновления

    Returns:
        Обновленный объект Activity или None
    """
    try:
        # Получаем активность
        activity = await get_activity_by_theme_and_type(session, activity_type, theme)
        if not activity:
            logger.warning('Activity not found: %s (%s)', theme, activity_type)
            return None

        # Обновляем поля
        for key, value in update_values.items():
            setattr(activity, key, value)

        # Коммитим изменения
        async with session.begin():
            session.add(activity)

        # Обновляем объект из БД
        return activity

    except SQLAlchemyError as e:
        logger.error('Update failed for activity %s: %s', theme, e)
        return None


async def update_activity_name_by_name(
    session: AsyncSession, activity_type: str, old_theme: str, new_theme: str
) -> Activity | None:
    """Обновить название активности.

    Args:
        session: Асинхронная сессия SQLAlchemy
        activity_type: Тип активности
        old_theme: Старая тема
        new_theme: Новая тема

    Returns:
        Обновленный объект Activity или None
    """
    return await _update_activity(session, activity_type, old_theme, {'theme': new_theme})


async def update_activity_description_by_name(
    session: AsyncSession, activity_type: str, theme: str, new_description: str
) -> Activity | None:
    """Обновить описание активности.

    Args:
        session: Асинхронная сессия SQLAlchemy
        activity_type: Тип активности
        theme: Тема активности
        new_description: Новое описание

    Returns:
        Обновленный объект Activity или None
    """
    return await _update_activity(
        session, activity_type, theme, {'description': new_description}
    )


async def update_activity_date_by_name(
    session: AsyncSession, activity_type: str, theme: str, new_date: date | None
) -> Activity | None:
    """Обновить дату активности.

    Args:
        session: Асинхронная сессия SQLAlchemy
        activity_type: Тип активности
        theme: Тема активности
        new_date: Новая дата или None

    Returns:
        Обновленный объект Activity или None
    """
    try:
        activity = await get_activity_by_theme_and_type(session, activity_type, theme)
        if not activity:
            logger.warning('Activity not found: %s (%s)', theme, activity_type)
            return None

        old_datetime = activity.date_time
        zone_info = get_config().zone_info

        if not new_date:
            activity.date_time = None
        elif old_datetime:
            activity.date_time = datetime.combine(
                new_date, old_datetime.time(), tzinfo=zone_info
            )
        else:
            activity.date_time = datetime(
                new_date.year, new_date.month, new_date.day, tzinfo=zone_info
            )

        async with session.begin():
            session.add(activity)

        return activity

    except SQLAlchemyError as e:
        logger.error('Update date failed for activity %s: %s', theme, e)
        return None


async def update_activity_time_by_name(
    session: AsyncSession,
    activity_type: str,
    theme: str,
    new_time: time | None = None,
) -> Activity | None:
    """Обновить время активности.

    Args:
        session: Асинхронная сессия SQLAlchemy
        activity_type: Тип активности
        theme: Тема активности
        new_time: Новое время или None

    Returns:
        Обновленный объект Activity или None
    """
    try:
        activity = await get_activity_by_theme_and_type(session, activity_type, theme)
        if not activity:
            logger.warning('Activity not found: %s (%s)', theme, activity_type)
            return None

        old_datetime = activity.date_time
        zone_info = get_config().zone_info

        if old_datetime:
            if new_time:
                activity.date_time = datetime.combine(
                    old_datetime.date(), new_time, tzinfo=zone_info
                )
            else:
                activity.date_time = datetime(
                    old_datetime.year,
                    old_datetime.month,
                    old_datetime.day,
                    tzinfo=zone_info,
                )

            async with session.begin():
                session.add(activity)

            return activity

        return None

    except SQLAlchemyError as e:
        logger.error('Update time failed for activity %s: %s', theme, e)
        return None


async def update_activity_fileid_by_name(
    session: AsyncSession,
    activity_type: str,
    theme: str,
    file_id: str,
    content_type: str,
) -> Activity | None:
    """Обновить file_id и content_type активности.

    Args:
        session: Асинхронная сессия SQLAlchemy
        activity_type: Тип активности
        theme: Тема активности
        file_id: Новый file_id
        content_type: Новый content_type

    Returns:
        Обновленный объект Activity или None
    """
    return await _update_activity(
        session,
        activity_type,
        theme,
        {'file_id': file_id, 'content_type': content_type},
    )


async def remove_activity_by_theme_and_type(
    session: AsyncSession, activity_type: str, theme: str
) -> bool:
    """Удалить активность по теме и типу.

    Args:
        session: Асинхронная сессия SQLAlchemy
        activity_type: Тип активности
        theme: Тема активности

    Returns:
        True если удалено, False если ошибка или не найдено
    """
    try:
        # Находим активность
        activity = await get_activity_by_theme_and_type(session, activity_type, theme)
        if not activity:
            logger.warning('Activity not found: %s (%s)', theme, activity_type)
            return False

        # Удаляем
        async with session.begin():
            await session.delete(activity)

        logger.info('Activity removed: %s (%s)', theme, activity_type)
        return True

    except SQLAlchemyError as e:
        logger.error('Removing activity failed: %s', e)
        return False


async def add_user(
    session: AsyncSession,
    tg_id: int,
    nickname: str | None,
    phone: str,
    name: str,
    last_name: str,
) -> User | None:
    """Добавить пользователя.

    Args:
        session: Асинхронная сессия SQLAlchemy
        tg_id: Telegram ID
        nickname: Никнейм (опционально)
        phone: Телефон
        name: Имя
        last_name: Фамилия

    Returns:
        Объект User или None при ошибке
    """
    try:
        async with session.begin():
            user = User(
                id=tg_id, nickname=nickname, phone=phone, name=name, last_name=last_name
            )
            session.add(user)

        logger.info('Added new user: %s', tg_id)
        return user

    except SQLAlchemyError as e:
        logger.error('Adding user failed: %s', e)
        return None


async def get_user(session: AsyncSession, tg_id: int) -> User | None:
    """Получить пользователя по ID.

    Args:
        session: Асинхронная сессия SQLAlchemy
        tg_id: Telegram ID

    Returns:
        Объект User или None
    """
    try:
        stmt = select(User).where(User.id == tg_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error('Error getting user %s: %s', tg_id, e)
        return None


async def get_users(session: AsyncSession) -> Sequence[User]:
    """Получить всех пользователей.

    Args:
        session: Асинхронная сессия SQLAlchemy

    Returns:
        Список пользователей
    """
    try:
        stmt = select(User).order_by(User.created_at)
        result = await session.execute(stmt)
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error('Error getting users: %s', e)
        return []


async def delete_user(session: AsyncSession, tg_id: int) -> bool:
    """Удалить пользователя.

    Args:
        session: Асинхронная сессия SQLAlchemy
        tg_id: Telegram ID

    Returns:
        True если удалено, False если ошибка или не найдено
    """
    try:
        # Получаем пользователя
        user = await get_user(session, tg_id)
        if not user:
            logger.warning('User %s not found', tg_id)
            return False

        # Удаляем
        async with session.begin():
            await session.delete(user)

        logger.info('User %s deleted', tg_id)
        return True

    except SQLAlchemyError as e:
        logger.error('Deleting user failed: %s', e)
        return False


async def update_user(session: AsyncSession, tg_id: int, update_data: dict) -> bool:
    """Обновить данные пользователя.

    Args:
        session: Асинхронная сессия SQLAlchemy
        tg_id: Telegram ID
        update_data: Словарь с полями для обновления

    Returns:
        True если обновлено, False если ошибка
    """
    try:
        async with session.begin():
            stmt = (
                update(User)
                .where(User.id == tg_id)
                .values(**update_data)
                .returning(User.id)
            )
            result = await session.execute(stmt)

            if result.scalar_one_or_none():
                logger.info('User %s updated', tg_id)
                return True

        return False

    except SQLAlchemyError as e:
        logger.error('Update user failed: %s', e)
        return False
