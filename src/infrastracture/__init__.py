from src.infrastracture.adapters.repositories.gspread_users import gspread_repository
from src.infrastracture.in_memory.users import InMemoryUsers
from src.infrastracture.repository.users import UsersRepository

users_repository = UsersRepository(
    users_collector=InMemoryUsers(), repository=gspread_repository
)
