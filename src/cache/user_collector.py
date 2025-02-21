from typing import TypeAlias

from src.cache.dto import UserDTO

UserTgId: TypeAlias = int


class UserCollector:
    def __init__(self):
        self.__cached_users: dict[UserTgId, UserDTO] = {}

    def get_user(self, user_id: UserTgId) -> UserDTO | None:
        return self.__cached_users.get(user_id)

    def update_cache(self, user: dict[UserTgId, UserDTO] | UserDTO) -> None:
        if isinstance(user, UserDTO):
            self.__cached_users[user.id] = user
        self.__cached_users.update(user)


user_collector = UserCollector()
