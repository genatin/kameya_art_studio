import logging

from sqlalchemy.ext.asyncio import async_sessionmaker

from src.application.models import UserDTO
from src.infrastracture.adapters.interfaces.repositories import UsersAbstractRepository
from src.infrastracture.database.sqlite import dao
from src.infrastracture.database.sqlite.db import async_session_maker

logger = logging.getLogger(__name__)


class RepositoryUser(UsersAbstractRepository):
    def __init__(self, session_maker: async_sessionmaker | None = None) -> None:
        if session_maker is None:
            self.__session_maker = async_session_maker
        else:
            self.__session_maker = session_maker

    async def get_user(self, user_id: int) -> UserDTO | None:
        try:
            async with self.__session_maker() as session:
                user = await dao.get_user(session, tg_id=user_id)

                if not user:
                    logger.debug('User %s not found', user_id)
                    return None

                return UserDTO(
                    id=user.id,
                    nickname=user.nickname,
                    phone=user.phone,
                    name=user.name,
                    last_name=user.last_name,
                )
        except Exception as e:
            logger.error('Error getting user %s: %s', user_id, e)
            return None

    async def get_users(self) -> list[UserDTO]:
        try:
            async with self.__session_maker() as session:
                users = await dao.get_users(session)

                if not users:
                    return []

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
        except Exception as e:
            logger.error('Error getting users: %s', e)
            return []

    async def add_user(self, user: UserDTO) -> bool:
        try:
            async with self.__session_maker() as session:
                existing_user = await dao.get_user(session, user.id)
                if existing_user:
                    logger.debug('User %s already exists, updating', user.id)
                    await self.update_user(user)
                    return False

                # Добавляем нового пользователя
                await dao.add_user(
                    session=session,
                    tg_id=user.id,
                    nickname=user.nickname,
                    phone=user.phone,
                    name=user.name,
                    last_name=user.last_name,
                )
                logger.info('User %s added', user.id)
                return True
        except Exception as e:
            logger.error('Error adding user %s: %s', user.id, e)
            return False

    async def update_user(self, user: UserDTO) -> bool:
        try:
            async with self.__session_maker() as session:
                return await dao.update_user(
                    session, user.id, user.to_dict(exclude={'id'})
                )
        except Exception as e:
            logger.error('Error updating user %s: %s', user.id, e)
            return False

    async def delete_user(self, user_id: int) -> bool:
        try:
            async with self.__session_maker() as session:
                return await dao.delete_user(session, tg_id=user_id)
        except Exception as e:
            logger.error('Error deleting user %s: %s', user_id, e)
            return False
