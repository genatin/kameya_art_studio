from src.application.in_memory.interfaces import InMemoryUsersAbstractRepository
from src.application.models import UserDTO
from src.infrastracture.adapters.interfaces.repositories import UsersAbstractRepository


class UsersRepository:

    def __init__(self, repository, users_collector) -> None:
        self.collector: InMemoryUsersAbstractRepository = users_collector
        self.repository: UsersAbstractRepository = repository

    def add_user(self, user: UserDTO) -> None:
        self.repository.add_user(user)
        self.collector.update_cache(user)

    def update_user(self, user: UserDTO) -> bool:
        if success := self.repository.update_user(user) is not None:
            self.collector.update_cache(user)
        return success
