"""Тестовые фикстуры для пользователей."""
from src.application.models import UserDTO


# Валидные данные для тестирования
VALID_USER_DATA = {
    'id': 123456,
    'nickname': '@test_user',
    'phone': '+79001234567',
    'name': 'Иван',
    'last_name': 'Иванов',
}

# Минимальные валидные данные (только required поля)
MINIMAL_USER_DATA = {
    'id': 123456,
}

# Данные для проверки валидации имени
INVALID_NAME_DATA = {
    'too_short': 'А',  # Меньше 2 символов
    'too_long': 'А' * 51,  # Больше 50 символов
    'with_digits': 'Иван123',  # Содержит цифры
    'with_latin': 'Ivan',  # Латиница
    'with_spaces': 'Иван Иванов',  # Пробелы
    'with_special_chars': 'Иван!',  # Спецсимволы
    'with_repeating_chars': 'Ааааа',  # Повторяющиеся символы
}

# Данные для проверки валидации телефона
INVALID_PHONE_DATA = {
    'too_short': '+7900',  # Меньше 11 цифр
    'too_long': '+790012345678',  # Больше 11 цифр
    'without_prefix': '9001234567',  # Без +7 или 8
    'with_letters': '+7abc1234567',  # Содержит буквы
    'with_wrong_prefix': '+69001234567',  # Неправильный код страны
}

# Валидные номера телефонов
VALID_PHONES = [
    '+79001234567',
    '89001234567',
    '+7 (900) 123-45-67',  # С форматированием (нужно очистить)
]

# Валидные имена
VALID_NAMES = [
    'Иван',
    'Мария',
    'Александр',
    'Анна-Мария',  # С дефисом (может быть невалидным по вашим правилам)
]

# Фикстуры для различных сценариев тестирования
class UserFixtures:
    """Класс с фабриками тестовых пользователей."""

    @staticmethod
    def create_valid_user(**kwargs) -> UserDTO:
        """Создать валидного пользователя."""
        data = VALID_USER_DATA.copy()
        data.update(kwargs)
        return UserDTO(**data)

    @staticmethod
    def create_minimal_user(user_id: int = 123456) -> UserDTO:
        """Создать минимального пользователя (только ID)."""
        return UserDTO(id=user_id)

    @staticmethod
    def create_unregistered_user(user_id: int = 789) -> UserDTO:
        """Создать незарегистрированного пользователя (без name, phone, last_name)."""
        return UserDTO(
            id=user_id,
            nickname='@unregistered',
        )

    @staticmethod
    def create_admin_user(user_id: int = 123) -> UserDTO:
        """Создать пользователя-администратора."""
        return UserDTO(
            id=user_id,
            nickname='@admin',
            phone='+70000000000',
            name='Админ',
            last_name='Админов',
        )

    @staticmethod
    def create_multiple_users(count: int = 5, start_id: int = 1000) -> list[UserDTO]:
        """Создать несколько тестовых пользователей."""
        users = []
        for i in range(count):
            user_id = start_id + i
            users.append(
                UserDTO(
                    id=user_id,
                    nickname=f'@user_{i}',
                    phone=f'+7900123456{i}',
                    name=f'Имя{i}',
                    last_name=f'Фамилия{i}',
                )
            )
        return users

    @staticmethod
    def create_user_with_custom_phone(phone: str) -> UserDTO:
        """Создать пользователя с кастомным номером телефона."""
        data = VALID_USER_DATA.copy()
        data['phone'] = phone
        return UserDTO(**data)

    @staticmethod
    def create_user_with_custom_name(name: str, last_name: str = 'Иванов') -> UserDTO:
        """Создать пользователя с кастомным именем."""
        data = VALID_USER_DATA.copy()
        data['name'] = name
        data['last_name'] = last_name
        return UserDTO(**data)
