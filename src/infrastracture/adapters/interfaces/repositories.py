from abc import ABC, abstractmethod

from src.application.models import UserDTO


class UsersAbstractRepository(ABC):

    @abstractmethod
    def add_user(self, user: UserDTO) -> None:
        raise NotImplementedError

    @abstractmethod
    def update_user(self, user: UserDTO) -> None | str:
        raise NotImplementedError

    @abstractmethod
    def get_user(self, id: int) -> UserDTO | None:
        raise NotImplementedError
