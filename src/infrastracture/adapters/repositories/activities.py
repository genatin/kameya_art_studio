import logging
from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, ConfigDict, RootModel

from src.application.utils import format_date_russian
from src.infrastracture.adapters.interfaces.repositories import (
    ActivityAbstractRepository,
)
from src.infrastracture.database.redis.keys import ActivityKey
from src.infrastracture.database.redis.repository import RedisRepository
from src.infrastracture.database.sqlite import dao
from src.infrastracture.database.sqlite.base import de_emojify
from src.infrastracture.database.sqlite.db import async_session_maker

logger = logging.getLogger(__name__)


class ActivityModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    theme: str
    content_type: str | None = None
    file_id: str | None = None
    description: str | None = None
    date_time: datetime | None = None

    def model_dump(self, **kwargs) -> dict[str, Any]:
        d = super().model_dump(**kwargs)
        if self.date_time:
            d['date'] = self.date_time.date()
            d['date_repr'] = (
                format_date_russian(self.date_time.date()) if self.date_time else None
            )
            if self.date_time.time() != time(0, 0, 0):
                d['time'] = self.date_time.time()
                d['time_repr'] = (
                    self.date_time.time().strftime('%H:%M') if self.date_time else None
                )
        return d


class Activities(RootModel):
    model_config = ConfigDict(from_attributes=True)

    root: list[ActivityModel]


class ActivityRepository(ActivityAbstractRepository):
    """Репозиторий для работы с активностями.

    Реализует паттерн Repository, отделяя бизнес-логику от деталей доступа к данным.
    """

    def __init__(self, redis: RedisRepository) -> None:
        """Инициализировать репозиторий.

        Args:
            redis: Репозиторий Redis для кэширования
        """
        self._session_maker = async_session_maker
        self._redis = redis

    @classmethod
    def get_activity_key(cls, activity_type: str) -> ActivityKey:
        """Получить ключ для кэширования активностей по типу.

        Args:
            activity_type: Тип активности

        Returns:
            Ключ для Redis
        """
        return ActivityKey(key=de_emojify(activity_type))

    async def _invalidate_cache(self, activity_type: str) -> None:
        """Инвалидировать кэш для типа активности.

        Args:
            activity_type: Тип активности
        """
        try:
            cache_key = self.get_activity_key(activity_type)
            await self._redis.delete(cache_key)
            logger.debug('Cache invalidated for activity type: %s', activity_type)
        except Exception as e:
            logger.error('Failed to invalidate cache for %s: %s', activity_type, e)

    async def _execute_with_session(self, operation, *args, **kwargs) -> Any:
        """Выполнить операцию в контексте сессии.

        Args:
            operation: Функция DAO для выполнения
            *args: Аргументы для операции
            **kwargs: Ключевые аргументы для операции

        Returns:
            Результат выполнения операции
        """
        async with self._session_maker() as session:
            return await operation(session, *args, **kwargs)

    async def add_activity(
        self,
        activity_type: str,
        theme: str,
        image_id: str,
        content_type: str,
        description: str | None = None,
        date_time: datetime | None = None,
    ) -> ActivityModel | None:
        """Добавить новую активность.

        Args:
            activity_type: Тип активности
            theme: Тема активности
            image_id: ID изображения
            content_type: Тип контента
            description: Описание (опционально)
            date_time: Дата и время (опционально)

        Returns:
            Словарь с данными активности или None при ошибке
        """
        try:
            # Создаем активность через DAO
            activity = await self._execute_with_session(
                dao.add_activity,
                activity_type=activity_type,
                theme=theme,
                image_id=image_id,
                content_type=content_type,
                description=description,
                date_time=date_time,
            )

            if not activity:
                logger.warning('Failed to add activity: %s', theme)
                return None

            # Инвалидируем кэш
            await self._invalidate_cache(activity_type)

            # Преобразуем ORM в словарь
            return ActivityModel.model_validate(activity)

        except Exception as e:
            logger.error('Error adding activity %s: %s', theme, e)
            return None

    async def get_all_activity_by_type(self, activity_type: str) -> list[ActivityModel]:
        """Получить все активности по типу с кэшированием.

        Args:
            activity_type: Тип активности

        Returns:
            Список активностей в виде словарей
        """
        # Проверяем кэш
        cache_key = self.get_activity_key(activity_type)
        cached_data = await self._redis.get(cache_key, list)

        if cached_data is not None:
            logger.debug('Cache hit for activity type: %s', activity_type)
            return cached_data

        try:
            # Получаем данные из БД
            activities = await self._execute_with_session(
                dao.get_all_activity_by_type, activity_type=activity_type
            )

            # Преобразуем ORM объекты в словари
            activities_data = [
                ActivityModel.model_validate(activity).model_dump()
                for activity in activities
                if activity
            ]

            # Кэшируем на 2 минуты
            if activities_data:
                await self._redis.set(cache_key, activities_data, 120)
                logger.debug(
                    'Cached %s activities for type: %s',
                    len(activities_data),
                    activity_type,
                )

            return activities_data

        except Exception as e:
            logger.error('Error getting activities for type %s: %s', activity_type, e)
            return []

    async def update_activity_name_by_name(
        self, activity_type: str, old_theme: str, new_theme: str
    ) -> ActivityModel | None:
        """Обновить название активности.

        Args:
            activity_type: Тип активности
            old_theme: Старое название темы
            new_theme: Новое название темы

        Returns:
            Обновленные данные активности или None при ошибке
        """
        try:
            activity = await self._execute_with_session(
                dao.update_activity_name_by_name,
                activity_type=activity_type,
                old_theme=old_theme,
                new_theme=new_theme,
            )

            if activity:
                await self._invalidate_cache(activity_type)
                return ActivityModel.model_validate(activity)

            logger.warning(
                'Activity not found for update: %s -> %s', old_theme, new_theme
            )
            return None

        except Exception as e:
            logger.error('Error updating activity name %s: %s', old_theme, e)
            return None

    async def update_activity_description_by_name(
        self, activity_type: str, theme: str, new_description: str
    ) -> ActivityModel | None:
        """Обновить описание активности.

        Args:
            activity_type: Тип активности
            theme: Тема активности
            new_description: Новое описание

        Returns:
            Обновленные данные активности или None при ошибке
        """
        try:
            activity = await self._execute_with_session(
                dao.update_activity_description_by_name,
                activity_type=activity_type,
                theme=theme,
                new_description=new_description,
            )

            if activity:
                await self._invalidate_cache(activity_type)
                return ActivityModel.model_validate(activity)

            logger.warning('Activity not found for description update: %s', theme)
            return None

        except Exception as e:
            logger.error('Error updating activity description %s: %s', theme, e)
            return None

    async def update_activity_date_by_name(
        self,
        activity_type: str,
        theme: str,
        new_date: date | None,
    ) -> ActivityModel | None:
        """Обновить дату активности.

        Args:
            activity_type: Тип активности
            theme: Тема активности
            new_date: Новая дата или None

        Returns:
            Обновленные данные активности или None при ошибке
        """
        try:
            activity = await self._execute_with_session(
                dao.update_activity_date_by_name,
                activity_type=activity_type,
                theme=theme,
                new_date=new_date,
            )

            if activity:
                await self._invalidate_cache(activity_type)
                return ActivityModel.model_validate(activity)

            logger.warning('Activity not found for date update: %s', theme)
            return None

        except Exception as e:
            logger.error('Error updating activity date %s: %s', theme, e)
            return None

    async def update_activity_time_by_name(
        self,
        activity_type: str,
        theme: str,
        new_time: time | None,
    ) -> ActivityModel | None:
        """Обновить время активности.

        Args:
            activity_type: Тип активности
            theme: Тема активности
            new_time: Новое время или None

        Returns:
            Обновленные данные активности или None при ошибке
        """
        try:
            activity = await self._execute_with_session(
                dao.update_activity_time_by_name,
                activity_type=activity_type,
                theme=theme,
                new_time=new_time,
            )

            if activity:
                await self._invalidate_cache(activity_type)
                return ActivityModel.model_validate(activity)

            logger.warning('Activity not found for time update: %s', theme)
            return None

        except Exception as e:
            logger.error('Error updating activity time %s: %s', theme, e)
            return None

    async def get_activity_by_theme_and_type(
        self,
        activity_type: str,
        theme: str,
    ) -> ActivityModel | None:
        """Получить активность по теме и типу.

        Args:
            activity_type: Тип активности
            theme: Тема активности

        Returns:
            Данные активности или None если не найдено
        """
        try:
            activity = await self._execute_with_session(
                dao.get_activity_by_theme_and_type,
                activity_type=activity_type,
                theme=theme,
            )

            if activity:
                return ActivityModel.model_validate(activity)

            logger.debug('Activity not found: %s (%s)', theme, activity_type)
            return None

        except Exception as e:
            logger.error('Error getting activity %s: %s', theme, e)
            return None

    async def update_activity_fileid_by_name(
        self, activity_type: str, theme: str, file_id: str, content_type: str
    ) -> ActivityModel | None:
        """Обновить file_id и content_type активности.

        Args:
            activity_type: Тип активности
            theme: Тема активности
            file_id: Новый file_id
            content_type: Новый content_type

        Returns:
            Обновленные данные активности или None при ошибке
        """
        try:
            activity = await self._execute_with_session(
                dao.update_activity_fileid_by_name,
                activity_type=activity_type,
                theme=theme,
                file_id=file_id,
                content_type=content_type,
            )

            if not activity:
                logger.warning('Activity not found for file update: %s', theme)
                return None

            # Инвалидируем кэш
            await self._invalidate_cache(activity_type)

            # Преобразуем ORM в словарь
            return ActivityModel.model_validate(activity)

        except Exception as e:
            logger.error('Error updating activity file %s: %s', theme, e)
            return None

    async def remove_activity_by_theme_and_type(
        self, activity_type: str, theme: str
    ) -> bool:
        """Удалить активность.

        Args:
            activity_type: Тип активности
            theme: Тема активности

        Returns:
            True если успешно удалено, False если ошибка
        """
        try:
            result = await self._execute_with_session(
                dao.remove_activity_by_theme_and_type,
                activity_type=activity_type,
                theme=theme,
            )

            if result:
                await self._invalidate_cache(activity_type)
                logger.info('Activity removed: %s (%s)', theme, activity_type)
            else:
                logger.warning('Activity not found for removal: %s', theme)

            return result

        except Exception as e:
            logger.error('Error removing activity %s: %s', theme, e)
            return False


# Опционально: Фабрика для создания репозитория
class RepositoryFactory:
    """Фабрика для создания репозиториев."""

    @staticmethod
    def create_activity_repository(redis: RedisRepository) -> ActivityRepository:
        """Создать репозиторий активностей.

        Args:
            redis: Репозиторий Redis

        Returns:
            Экземпляр ActivityRepository
        """
        return ActivityRepository(redis)
