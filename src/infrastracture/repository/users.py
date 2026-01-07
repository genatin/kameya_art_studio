import logging

from src.application.models import UserDTO, UserTgId
from src.infrastracture.adapters.interfaces.repositories import UsersAbstractRepository
from src.infrastracture.database.redis.repository import RedisRepository

logger = logging.getLogger(__name__)


class UsersService:
    def __init__(self, cache_time, user_repository, redis) -> None:
        self.cache_time_for_users: int = cache_time
        self._redis: RedisRepository = redis
        self._user_repo: UsersAbstractRepository = user_repository

    async def add_user(self, user: UserDTO) -> UserDTO:
        await self._user_repo.add_user(user)
        await self._save_user(user)
        return user

    async def _save_user(self, user: UserDTO) -> None:
        await self._redis.save_user(user.id, user, self.cache_time_for_users)

    async def update_user(self, user: UserDTO) -> bool:
        if success := await self._user_repo.update_user(user):
            await self._save_user(user)
        return success

    async def get_user(
        self, user_id: UserTgId, update_reg: bool = False
    ) -> UserDTO | None:
        if (user := await self._redis.get_user(user_id)) or update_reg:
            return user
        user = await self._user_repo.get_user(user_id)
        if user:
            await self._save_user(user)
        return user

    async def get_users(self) -> list[UserDTO]:
        users = await self._user_repo.get_users()
        return users

    async def remove_user(self, user_id: UserTgId, only_cache: bool = False) -> bool:
        await self._redis.delete_user(user_id)
        if not only_cache:
            return await self._user_repo.delete_user(user_id)
