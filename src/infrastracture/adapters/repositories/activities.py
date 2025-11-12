import logging
from collections.abc import Sequence

import emoji
from pydantic import BaseModel, ConfigDict, RootModel

from src.infrastracture.adapters.interfaces.repositories import (
    ActivityAbstractRepository,
)
from src.infrastracture.database.redis.keys import ActivityKey
from src.infrastracture.database.redis.repository import RedisRepository
from src.infrastracture.database.sqlite import dao
from src.infrastracture.database.sqlite.db import async_session_maker

logger = logging.getLogger(__name__)


def de_emojify(text) -> str:
    return emoji.replace_emoji(text, replace='')


class Activity(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    theme: str
    file_id: str
    content_type: str
    description: str


class Acitivities(RootModel):
    model_config = ConfigDict(from_attributes=True)

    root: list[Activity]


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
    ) -> Activity | None:
        async with self.__session_maker() as session:
            activity = await dao.add_activity(
                session,
                activity_type=activity_type,
                theme=theme,
                image_id=image_id,
                content_type=content_type,
                description=description,
            )
        if activity:
            activity_key = self.get_activity_key(activity_type)
            await self.__redis.delete(activity_key)
            return activity

    async def get_all_activity_by_type(self, activity_type: str) -> Sequence[Activity]:
        activity_key = self.get_activity_key(activity_type)
        if redis_activities := await self.__redis.get(activity_key, list):
            return redis_activities

        async with self.__session_maker() as session:
            activities = await dao.get_all_activity_by_type(
                session, activity_type=activity_type
            )
            activities = Acitivities.model_validate(activities)
            activities = [act.model_dump() for act in activities.root]
            if activities:
                await self.__redis.set(activity_key, activities, 60 * 2)
            return activities

    async def update_activity_name_by_name(
        self, activity_type: str, old_theme: str, new_theme: str
    ) -> Activity | None:
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
    ) -> Activity | None:
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

    async def get_activity_by_theme_and_type(
        self,
        activity_type: str,
        theme: str,
    ) -> Activity:
        async with self.__session_maker() as session:
            return await dao.get_activity_by_theme_and_type(
                session, activity_type=activity_type, theme=theme
            )

    async def update_activity_fileid_by_name(
        self, activity_type: str, theme: str, file_id: str, content_type: str
    ) -> Activity | None:
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
