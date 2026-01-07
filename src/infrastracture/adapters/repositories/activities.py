import logging
from datetime import date, datetime, time
from typing import Any

import emoji
from pydantic import BaseModel, ConfigDict, RootModel

from src.infrastracture.adapters.interfaces.repositories import (
    ActivityAbstractRepository,
)
from src.infrastracture.database.redis.keys import ActivityKey
from src.infrastracture.database.redis.repository import RedisRepository
from src.infrastracture.database.sqlite import dao
from src.infrastracture.database.sqlite.db import async_session_maker
from src.presentation.dialogs.utils import format_date_russian

logger = logging.getLogger(__name__)


def de_emojify(text) -> str:
    return emoji.replace_emoji(text, replace='')


class ActivityModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    theme: str
    content_type: str
    activity_type: str
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


class AcitivitiesModel(RootModel):
    model_config = ConfigDict(from_attributes=True)

    root: list[ActivityModel]


class ActivityRepository(ActivityAbstractRepository):
    def __init__(self, redis) -> None:
        self.__session_maker = async_session_maker
        self.__redis: RedisRepository = redis

    @classmethod
    def get_activity_key(cls, activity_type: str) -> ActivityKey:
        return ActivityKey(key=de_emojify(activity_type))

    async def add_activity(
        self,
        activity_type: str,
        theme: str,
        image_id: str,
        content_type: str,
        description: str | None = None,
        date_time: datetime | None = None,
    ) -> ActivityModel | None:
        async with self.__session_maker() as session:
            activity = await dao.add_activity(
                session,
                activity_type=activity_type,
                theme=theme,
                image_id=image_id,
                content_type=content_type,
                description=description,
                date_time=date_time,
            )
        if activity:
            activity_key = self.get_activity_key(activity_type)
            await self.__redis.delete(activity_key)
            return activity

    async def get_all_activity_by_type(self, activity_type: str) -> list[dict]:
        activity_key = self.get_activity_key(activity_type)
        if redis_activities := await self.__redis.get(activity_key, list):
            return redis_activities

        async with self.__session_maker() as session:
            activities = await dao.get_all_activity_by_type(
                session, activity_type=activity_type
            )
            activities = AcitivitiesModel.model_validate(activities)
            activities = [act.model_dump() for act in activities.root]
            if activities:
                await self.__redis.set(activity_key, activities, 60 * 2)
            return activities

    async def update_activity_name_by_name(
        self, activity_type: str, old_theme: str, new_theme: str
    ) -> ActivityModel | None:
        async with self.__session_maker() as session:
            activity = await dao.update_activity_name_by_name(
                session,
                activity_type=activity_type,
                old_theme=old_theme,
                new_theme=new_theme,
            )
            if activity:
                activity_key = self.get_activity_key(activity_type)
                await self.__redis.delete(activity_key)
                return activity

    async def update_activity_description_by_name(
        self, activity_type: str, theme: str, new_description: str
    ) -> ActivityModel | None:
        async with self.__session_maker() as session:
            activity = await dao.update_activity_description_by_name(
                session,
                activity_type=activity_type,
                theme=theme,
                new_description=new_description,
            )
            if activity:
                activity_key = self.get_activity_key(activity_type)
                await self.__redis.delete(activity_key)
                return activity

    async def update_activity_date_by_name(
        self,
        activity_type: str,
        theme: str,
        new_date: date | None,
    ) -> AcitivitiesModel | None:
        async with self.__session_maker() as session:
            activity = await dao.update_activity_date_by_name(
                session,
                activity_type=activity_type,
                theme=theme,
                new_date=new_date,
            )
            if activity:
                activity_key = self.get_activity_key(activity_type)
                await self.__redis.delete(activity_key)
                return activity

    async def update_activity_time_by_name(
        self,
        activity_type: str,
        theme: str,
        new_time: date | None,
    ) -> AcitivitiesModel | None:
        async with self.__session_maker() as session:
            activity = await dao.update_activity_time_by_name(
                session,
                activity_type=activity_type,
                theme=theme,
                new_time=new_time,
            )
            if activity:
                activity_key = self.get_activity_key(activity_type)
                await self.__redis.delete(activity_key)
                return activity

    async def get_activity_by_theme_and_type(
        self,
        activity_type: str,
        theme: str,
    ) -> ActivityModel:
        async with self.__session_maker() as session:
            return await dao.get_activity_by_theme_and_type(
                session, activity_type=activity_type, theme=theme
            )

    async def get_activity_by_id(
        self,
        activity_id: str,
    ) -> ActivityModel:
        async with self.__session_maker() as session:
            return ActivityModel.model_validate(
                await dao.get_activity_by_id(session, activity_id=activity_id)
            )

    async def update_activity_fileid_by_name(
        self, activity_type: str, theme: str, file_id: str, content_type: str
    ) -> ActivityModel | None:
        async with self.__session_maker() as session:
            activity = await dao.update_activity_fileid_by_name(
                session,
                activity_type=activity_type,
                theme=theme,
                file_id=file_id,
                content_type=content_type,
            )
            if activity:
                activity_key = self.get_activity_key(activity_type)
                await self.__redis.delete(activity_key)
                return activity

    async def remove_activity_by_theme_and_type(
        self, activity_type: str, theme: str
    ) -> None:
        async with self.__session_maker() as session:
            await dao.remove_activity_by_theme_and_type(
                session, activity_type=activity_type, theme=theme
            )
            await self.__redis.delete(self.get_activity_key(activity_type))
