from typing import Any, Optional, Type, TypeVar
from unittest.mock import AsyncMock, MagicMock

from pydantic import BaseModel

from src.application.domen.models.activity_type import ActivityEnum
from src.application.models import UserDTO, UserTgId


class UsersServiceMock:
    async def get_user(
        self, user_id: UserTgId, update_reg: bool = False
    ) -> list[UserDTO]:
        return UserDTO(1, "gromo", "+79999999999", "mock_user", "mock_last_name")


class MockRepository:
    def __init__(
        self,
        user_repo,
    ) -> None:
        self.user: UsersServiceMock = user_repo


T = TypeVar("T")


class MockRedisRepository:
    """Мок-класс для RedisRepository"""

    def __init__(self):
        # Создаем моки для всех асинхронных методов
        self.get = AsyncMock()
        self.hgetall = AsyncMock()
        self.getdel = AsyncMock()
        self.rpush = AsyncMock()
        self.lrem = AsyncMock()
        self.set = AsyncMock()
        self.hset = AsyncMock()
        self.delete = AsyncMock()
        self.close = AsyncMock()
        self.save_user = AsyncMock()
        self.get_user = AsyncMock()
        self.delete_user = AsyncMock()

        # Настраиваем стандартное поведение
        self._setup_default_behavior()

    def _setup_default_behavior(self) -> None:
        """Настройка стандартного поведения методов"""
        # get возвращает None по умолчанию
        self.get.return_value = None

        # hgetall возвращает пустой словарь
        self.hgetall.return_value = {}

        # getdel возвращает None по умолчанию
        self.getdel.return_value = None

        # Методы без возвращаемого значения
        self.rpush.return_value = None
        self.lrem.return_value = None
        self.set.return_value = None
        self.hset.return_value = None
        self.delete.return_value = None
        self.close.return_value = None
        self.save_user.return_value = None
        self.delete_user.return_value = None

        # get_user возвращает None по умолчанию
        self.get_user.return_value = None

    def reset_mock(self) -> None:
        """Сброс всех моков"""
        for attr_name in dir(self):
            if not attr_name.startswith("_"):
                attr = getattr(self, attr_name)
                if hasattr(attr, "reset_mock"):
                    attr.reset_mock()
        self._setup_default_behavior()

    # Вспомогательные методы для настройки поведения

    def setup_get_return_value(self, value: Any) -> None:
        """Настройка возвращаемого значения для метода get"""
        self.get.return_value = value

    def setup_get_side_effect(self, side_effect) -> None:
        """Настройка side_effect для метода get"""
        self.get.side_effect = side_effect

    def setup_hgetall_return_value(self, value: dict) -> None:
        """Настройка возвращаемого значения для метода hgetall"""
        self.hgetall.return_value = value

    def setup_get_user_return_value(self, user_dto: Any) -> None:
        """Настройка возвращаемого значения для метода get_user"""
        self.get_user.return_value = user_dto

    def setup_getdel_return_value(self, value: Any) -> None:
        """Настройка возвращаемого значения для метода getdel"""
        self.getdel.return_value = value

    # Методы для проверки вызовов

    def assert_get_called_with(self, key: Any, validator: Type[T]) -> None:
        """Проверка вызова метода get с определенными параметрами"""
        self.get.assert_called_with(key, validator)

    def assert_get_called_once(self) -> None:
        """Проверка что метод get был вызван один раз"""
        self.get.assert_called_once()

    def assert_set_called_with(self, key: Any, value: Any, ex: Any = None) -> None:
        """Проверка вызова метода set с определенными параметрами"""
        if ex is not None:
            self.set.assert_called_with(key, value, ex)
        else:
            self.set.assert_called_with(key, value)

    def assert_save_user_called_with(
        self, key: Any, value: Any, ex: Any = None
    ) -> None:
        """Проверка вызова метода save_user с определенными параметрами"""
        if ex is not None:
            self.save_user.assert_called_with(key, value, ex)
        else:
            self.save_user.assert_called_with(key, value)

    def assert_delete_user_called_with(self, key: Any) -> None:
        """Проверка вызова метода delete_user с определенными параметрами"""
        self.delete_user.assert_called_with(key)

    # Свойства для доступа к информации о вызовах

    @property
    def get_call_count(self) -> int:
        """Количество вызовов метода get"""
        return self.get.call_count

    @property
    def set_call_count(self) -> int:
        """Количество вызовов метода set"""
        return self.set.call_count

    @property
    def get_calls(self) -> list:
        """Список всех вызовов метода get"""
        return self.get.call_args_list

    @property
    def set_calls(self) -> list:
        """Список всех вызовов метода set"""
        return self.set.call_args_list
