import logging

from src.application.models import UserDTO
from src.infrastracture.adapters.interfaces.repositories import UsersAbstractRepository
from src.infrastracture.database.sqlite import dao
from src.infrastracture.database.sqlite.db import async_session_maker

logger = logging.getLogger(__name__)


class RepositoryUser(UsersAbstractRepository):
    def __init__(self) -> None:
        self.__session_maker = async_session_maker

    async def get_user(self, id: int) -> UserDTO | None:
        async with self.__session_maker() as session:
            user = await dao.get_user(session, tg_id=id)
            if not user:
                return user
            return UserDTO(
                id=user.id,
                nickname=user.nickname,
                phone=user.phone,
                name=user.name,
                last_name=user.last_name,
            )

    async def get_users(self) -> list[UserDTO] | None:
        async with self.__session_maker() as session:
            users = await dao.get_users(session)
            if not users:
                return users
            return [
                UserDTO(
                    id=user.id,
                    nickname=user.nickname,
                    phone=user.phone,
                    name=user.name,
                    last_name=user.last_name,
                )
                for user in users
            ]

    async def add_user(self, user: UserDTO) -> bool:
        async with self.__session_maker() as session:
            if await dao.get_user(session, user.id):
                await self.update_user(user)
                return False
            await dao.add_user(
                session=session,
                tg_id=user.id,
                nickname=user.nickname,
                phone=user.phone,
                name=user.name,
                last_name=user.last_name,
            )
            return True

    async def update_user(self, user: UserDTO) -> bool:
        async with self.__session_maker() as session:
            return await dao.update_user(session, user.id, user.to_dict(exclude={'id'}))

    async def delete_user(self, id: int) -> bool:
        async with self.__session_maker() as session:
            return await dao.delete_user(session, tg_id=id)
