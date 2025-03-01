from src.application.in_memory.interfaces import InMemoryUsersAbstractRepository
from src.application.models import UserDTO, UserTgId


class InMemoryUsers(InMemoryUsersAbstractRepository):
    def __init__(self):
        self.__cached_users: dict[UserTgId, UserDTO] = {}

    def get_user(self, user_id: UserTgId) -> UserDTO | None:
        return self.__cached_users.get(user_id)

    def update_cache(self, user: dict[UserTgId, UserDTO] | UserDTO) -> None:
        if isinstance(user, UserDTO):
            self.__cached_users[user.id] = user
        elif isinstance(user, dict):
            self.__cached_users.update(user)
        else:
            raise NotImplementedError
