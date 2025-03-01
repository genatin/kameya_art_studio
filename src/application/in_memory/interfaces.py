from abc import ABC, abstractmethod

from src.application.models import UserDTO, UserTgId


class InMemoryUsersAbstractRepository(ABC):

    @abstractmethod
    def get_user(self, user_id: UserTgId) -> UserDTO | None:
        raise NotImplementedError

    @abstractmethod
    def remove_user(self, user_id: UserTgId) -> None:
        raise NotImplementedError

    @abstractmethod
    def update_cache(self, user: dict[UserTgId, UserDTO] | UserDTO) -> None:
        raise NotImplementedError
