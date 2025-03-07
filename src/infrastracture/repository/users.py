import logging
from typing import Iterator

from src.application.in_memory.interfaces import InMemoryUsersAbstractRepository
from src.application.models import UserDTO, UserTgId
from src.infrastracture.adapters.interfaces.repositories import UsersAbstractRepository

logger = logging.getLogger(__name__)


class UsersRepository:

    def __init__(self, repository, users_collector) -> None:
        self.__collector: InMemoryUsersAbstractRepository = users_collector
        self.__repository: UsersAbstractRepository = repository

    def add_user(self, user: UserDTO) -> None:
        self.__repository.add_user(user)
        self.__collector.update_cache(user)

    def update_user(self, user: UserDTO) -> bool:
        if success := self.__repository.update_user(user) is not None:
            self.__collector.update_cache(user)
        return success

    def get_user(self, user_id: UserTgId, cached: bool = True) -> UserDTO | None:
        if (user := self.__collector.get_user(user_id)) or cached:
            return user
        return self.__repository.get_user(user_id)

    def remove_user(self, user_id: UserTgId) -> UserDTO | None:
        self.__collector.remove_user(user_id)

    def update_cache(self) -> None:
        users = self.__repository.load_users_from_gsheet()
        self.__collector.update_cache(users)

    def get_admins(self) -> Iterator[UserDTO]:
        for admin in self.__collector.get_admins():
            yield admin
