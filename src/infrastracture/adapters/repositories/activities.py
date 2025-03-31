import logging
from typing import AsyncContextManager, Sequence

import emoji
from pydantic import BaseModel, ConfigDict, RootModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastracture.adapters.interfaces.repositories import (
    ActivityAbstractRepository,
)
from src.infrastracture.database.redis.keys import ActivityKey
from src.infrastracture.database.redis.repository import RedisRepository
from src.infrastracture.database.sqlite import dao
from src.infrastracture.database.sqlite.db import async_session_maker
from src.infrastracture.database.sqlite.models import Activity, ActivityType

logger = logging.getLogger(__name__)


def de_emojify(text):
    return emoji.replace_emoji(text, replace="")


class Activity(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    theme: str
    file_id: str
    description: str


class Acitivities(RootModel):
    model_config = ConfigDict(from_attributes=True)

    root: list[Activity]


class ActivityRepository(ActivityAbstractRepository):

    def __init__(self, redis) -> None:
        self.__session_maker: AsyncContextManager[AsyncSession] = async_session_maker
        self.__redis: RedisRepository = redis

    @classmethod
    def get_activity_key(cls, activity_type: str) -> ActivityKey:
        return ActivityKey(key=de_emojify(activity_type))

    async def get_act_type_by_name(self, name: str) -> ActivityType | None:
        async with self.__session_maker() as session:
            return await dao.get_act_type_by_name(session, name=name)

    async def add_activity(
        self,
        activity_type: str,
        theme: str,
        image_id: str,
        description: str = None,
    ) -> Activity | None:
        async with self.__session_maker() as session:
            return await dao.add_activity(
                session,
                activity_type=activity_type,
                theme=theme,
                image_id=image_id,
                description=description,
            )

    async def get_all_activity_by_type(self, activity_type: str) -> Sequence[Activity]:
        activity_key = self.get_activity_key(activity_type)
        if redis_activities := await self.__redis.get(activity_key, list):
            return redis_activities

        async with self.__session_maker() as session:
            activities = Acitivities.from_orm(
                await dao.get_all_activity_by_type(session, activity_type=activity_type)
            )
            activities = [act.model_dump() for act in activities.root]
            if activities:
                await self.__redis.set(activity_key, activities, 60 * 2)
            return activities

    async def update_activity_name_by_name(
        self, activity_type: str, old_theme: str, new_theme: str
    ) -> Activity | None:
        async with self.__session_maker() as session:
            return await dao.update_activity_name_by_name(
                session,
                activity_type=activity_type,
                old_theme=old_theme,
                new_theme=new_theme,
            )

    async def update_activity_description_by_name(
        self, type_name: str, theme: str, new_description: str
    ) -> Activity | None:
        async with self.__session_maker() as session:
            return await dao.update_activity_description_by_name(
                session,
                type_name=type_name,
                theme=theme,
                new_description=new_description,
            )

    async def get_activity_by_theme_and_type(
        self,
        act_type: str,
        theme: str,
    ) -> Activity:
        async with self.__session_maker() as session:
            return await dao.get_activity_by_theme_and_type(
                session, act_type=act_type, theme=theme
            )

    async def update_activity_fileid_by_name(
        self, type_name: str, theme: str, file_id: str
    ) -> Activity | None:
        async with self.__session_maker() as session:
            return await dao.update_activity_fileid_by_name(
                session, type_name=type_name, theme=theme, file_id=file_id
            )

    async def remove_activity_by_theme_and_type(
        self, act_type: str, theme: str
    ) -> None:
        async with self.__session_maker() as session:
            await dao.remove_activity_by_theme_and_type(
                session, type_name=act_type, theme=theme
            )
            await self.__redis.delete(self.get_activity_key(act_type))
