import logging
from typing import Iterator

from aiogram.types import User as AiogramUser

from src.application.models import UserDTO, UserTgId
from src.config import Config
from src.infrastracture.adapters.interfaces.repositories import UsersAbstractRepository
from src.infrastracture.database.redis.repository import RedisRepository

logger = logging.getLogger(__name__)


class UsersService:

    def __init__(self, config, repository, redis) -> None:
        self.config: Config = config
        self.__redis: RedisRepository = redis
        self.__repository: UsersAbstractRepository = repository

    async def add_user(self, user: UserDTO | AiogramUser) -> UserDTO:
        if isinstance(user, AiogramUser):
            user = UserDTO(id=user.id, nickname="@" + user.username)
        self.__repository.add_user(user)
        await self._save_user(user)
        return user

    async def _save_user(self, user: UserDTO) -> None:
        await self.__redis.save_user(user.id, user, self.config.users_cache_time)

    async def update_user(self, user: UserDTO) -> bool:
        if success := self.__repository.update_user(user) is not None:
            await self._save_user(user)
        return success

    async def get_user(self, user_id: UserTgId) -> UserDTO | None:
        if user := await self.__redis.get_user(user_id):
            return user
        user = self.__repository.get_user(user_id)
        if user:
            await self._save_user(user)
        return user

    async def remove_user(self, user_id: UserTgId) -> UserDTO | None:
        await self.__redis.delete_user(user_id)
