from typing import TypeAlias

from src.database.dto import UserDTO

UserTgId: TypeAlias = int


class UserCollector:
    def __init__(self):
        self.__cached_users: dict[UserTgId, UserDTO] = {}

    def get_user(self, user_id: UserTgId) -> UserDTO | None:
        return self.__cached_users.get(user_id)

    def update_cache(self, user_ids_phone: dict[UserTgId, UserDTO]) -> None:
        self.__cached_users.update(user_ids_phone)


user_collector = UserCollector()
