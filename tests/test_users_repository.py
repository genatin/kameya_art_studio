import pytest

from src.application.models import UserDTO
from src.infrastracture.adapters.repositories.users import RepositoryUser


class TestRepositoryUser:
    """Тесты репозитория пользователей."""

    @pytest.mark.asyncio
    async def test_add_and_get_user(
        self, user_repository: RepositoryUser, sample_user_data
    ):
        user_dto = UserDTO(**sample_user_data)

        result = await user_repository.add_user(user_dto)
        assert result is True

        retrieved_user = await user_repository.get_user(sample_user_data["id"])
        assert retrieved_user is not None
        assert retrieved_user.id == sample_user_data["id"]
        assert retrieved_user.name == sample_user_data["name"]
        assert retrieved_user.nickname == sample_user_data["nickname"]

    @pytest.mark.asyncio
    async def test_add_duplicate_user(
        self, user_repository: RepositoryUser, sample_user_data
    ):
        """Тест добавления дублирующегося пользователя."""
        user_dto = UserDTO(**sample_user_data)

        # Первое добавление
        result1 = await user_repository.add_user(user_dto)
        assert result1 is True

        # Второе добавление того же пользователя
        result2 = await user_repository.add_user(user_dto)
        assert result2 is False  # Должно вернуть False

    @pytest.mark.asyncio
    async def test_update_user(self, user_repository: RepositoryUser, sample_user_data):
        """Тест обновления пользователя."""
        # Добавляем пользователя
        user_dto = UserDTO(**sample_user_data)
        await user_repository.add_user(user_dto)

        # Обновляем данные
        updated_data = sample_user_data.copy()
        updated_data["name"] = "Updated Name"
        updated_dto = UserDTO(**updated_data)

        result = await user_repository.update_user(updated_dto)
        assert result is True

        # Проверяем обновление
        retrieved_user = await user_repository.get_user(sample_user_data["id"])
        assert retrieved_user.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_user(self, user_repository: RepositoryUser, sample_user_data):
        """Тест удаления пользователя."""
        user_dto = UserDTO(**sample_user_data)

        # Добавляем
        await user_repository.add_user(user_dto)

        # Удаляем
        result = await user_repository.delete_user(sample_user_data["id"])
        assert result is True

        # Проверяем, что пользователь удален
        retrieved_user = await user_repository.get_user(sample_user_data["id"])
        assert retrieved_user is None

    @pytest.mark.asyncio
    async def test_get_all_users(self, user_repository: RepositoryUser):
        """Тест получения всех пользователей."""
        # Добавляем несколько пользователей
        users_data = [
            {
                "id": 1,
                "nickname": "user1",
                "phone": "+79111111111",
                "name": "User1",
                "last_name": "Test",
            },
            {
                "id": 2,
                "nickname": "user2",
                "phone": "+79222222222",
                "name": "User2",
                "last_name": "Test",
            },
            {
                "id": 3,
                "nickname": "user3",
                "phone": "+79333333333",
                "name": "User3",
                "last_name": "Test",
            },
        ]

        for data in users_data:
            await user_repository.add_user(UserDTO(**data))

        # Получаем всех пользователей
        users = await user_repository.get_users()
        assert len(users) == 3
        assert {user.id for user in users} == {1, 2, 3}
