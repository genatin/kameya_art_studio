from src.adapters.repositories.gspread.gspread_worker import gspread_repository
from src.config import get_config
from src.database.interfaces.models import UserDTO
from src.database.interfaces.repositories import UsersAbstractRepository
from src.database.user_collector import UsersCollector

__all__ = ["users_facade"]


class UsersFacade:

    def __init__(self, repository, users_collector) -> None:
        self.collector: UsersCollector = users_collector
        self.repository: UsersAbstractRepository = repository

    def add_user(self, user: UserDTO) -> None:
        self.repository.add_user(user)
        self.collector.update_cache(user)

    def update_user(self, user: UserDTO) -> None:
        self.repository.update_user(user)
        self.collector.update_cache(user)

    def load_from_database_to_cache(self) -> None:
        users = gspread_repository.load_users_from_gsheet()
        self.collector.update_cache(users)


users_facade = UsersFacade(
    users_collector=UsersCollector(), repository=gspread_repository
)
