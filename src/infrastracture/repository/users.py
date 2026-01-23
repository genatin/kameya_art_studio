import csv
import io
import logging
from dataclasses import fields

from src.application.models import UserDTO, UserTgId
from src.infrastracture.adapters.interfaces.repositories import UsersAbstractRepository
from src.infrastracture.database.redis.repository import RedisRepository

logger = logging.getLogger(__name__)


def generate_csv_buffer(users: list[UserDTO]) -> tuple[io.BytesIO, str]:
    if not users:
        raise ValueError('Список пользователей пуст')
    buffer = io.BytesIO()
    text_buffer = io.StringIO()
    fieldnames = [field.name for field in fields(UserDTO)]

    writer = csv.DictWriter(text_buffer, fieldnames=fieldnames)
    writer.writeheader()

    for user in users:
        writer.writerow(
            {
                'id': user.id,
                'nickname': user.nickname or '',
                'phone': user.phone or '',
                'name': user.name or '',
                'last_name': user.last_name or '',
            }
        )

    buffer.write(text_buffer.getvalue().encode('utf-8-sig'))
    buffer.seek(0)

    # Генерируем имя файла
    filename = f'kameya_users_{len(users)}.csv'

    return buffer, filename


class UsersService:
    def __init__(self, cache_time, repository, redis) -> None:
        self.cache_time_for_users: int = cache_time
        self.__redis: RedisRepository = redis
        self.__repository: UsersAbstractRepository = repository

    async def add_user(self, user: UserDTO) -> UserDTO:
        await self.__repository.add_user(user)
        await self._save_user(user)
        return user

    async def _save_user(self, user: UserDTO) -> None:
        await self.__redis.save_user(user.id, user, self.cache_time_for_users)

    async def update_user(self, user: UserDTO) -> bool:
        if success := await self.__repository.update_user(user):
            await self._save_user(user)
        return success

    async def get_user(
        self, user_id: UserTgId, update_reg: bool = False
    ) -> UserDTO | None:
        if (user := await self.__redis.get_user(user_id)) or update_reg:
            return user
        user = await self.__repository.get_user(user_id)
        if user:
            await self._save_user(user)
        return user

    async def get_users(self) -> list[UserDTO]:
        users = await self.__repository.get_users()
        return users

    async def remove_user(self, user_id: UserTgId, only_cache: bool = False) -> bool:
        await self.__redis.delete_user(user_id)
        if not only_cache:
            return await self.__repository.delete_user(user_id)
