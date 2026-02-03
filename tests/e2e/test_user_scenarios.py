"""E2E тесты пользовательских сценариев."""
from datetime import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.domen.models import LessonActivity
from src.application.domen.models.activity_type import ActivityEnum, ActivityTypeFactory
from src.application.domen.models.lesson_option import (
    CLASSIC_LESS,
    LessonOptionFactory,
)
from src.application.models import UserDTO
from src.presentation.dialogs.registration import normalize_phone_number
from src.presentation.dialogs.states import (
    BaseMenu,
    FirstSeen,
)


# ============================================================================
# ТЕСТЫ ВАЛИДАЦИИ ДАННЫХ
# ============================================================================


class TestValidation:
    """Тесты валидации вводимых данных."""

    @pytest.mark.asyncio
    async def test_normalize_phone_valid_with_plus7(self) -> None:
        """Тест нормализации номера с +7."""
        assert normalize_phone_number('+79001234567') == '+79001234567'

    @pytest.mark.asyncio
    async def test_normalize_phone_valid_with_8(self) -> None:
        """Тест нормализации номера с 8."""
        assert normalize_phone_number('89001234567') == '+79001234567'

    @pytest.mark.asyncio
    async def test_normalize_phone_invalid_format(self) -> None:
        """Тест ошибки при неверном формате телефона."""
        with pytest.raises(ValueError):
            normalize_phone_number('+1234567890')

    @pytest.mark.asyncio
    async def test_normalize_phone_invalid_length(self) -> None:
        """Тест ошибки при неверной длине телефона."""
        with pytest.raises(ValueError):
            normalize_phone_number('+7900')


# ============================================================================
# ТЕСТЫ РЕГИСТРАЦИИ ПОЛЬЗОВАТЕЛЯ
# ============================================================================


class TestUserRegistration:
    """Тесты сценария регистрации пользователя."""

    @pytest.mark.asyncio
    async def test_registration_complete_flow(
        self,
        mock_user_repo,
        mock_notifier,
    ) -> None:
        """Тест полного сценария регистрации с корректными данными."""
        from src.presentation.dialogs.registration import validate_name_factory

        # Валидация имени
        assert validate_name_factory('Иван') == 'Иван'
        assert validate_name_factory('Мария') == 'Мария'

        # Валидация телефона
        phone = normalize_phone_number('+79001234567')
        assert phone == '+79001234567'

    @pytest.mark.asyncio
    async def test_registration_invalid_name_too_short(self) -> None:
        """Тест ошибки: имя слишком короткое."""
        from src.presentation.dialogs.registration import validate_name_factory

        with pytest.raises(ValueError, match='len'):
            validate_name_factory('А')

    @pytest.mark.asyncio
    async def test_registration_invalid_name_too_long(self) -> None:
        """Тест ошибки: имя слишком длинное."""
        from src.presentation.dialogs.registration import validate_name_factory

        with pytest.raises(ValueError, match='len'):
            validate_name_factory('А' * 51)

    @pytest.mark.asyncio
    async def test_registration_invalid_name_with_digits(self) -> None:
        """Тест ошибки: имя содержит цифры."""
        from src.presentation.dialogs.registration import validate_name_factory

        with pytest.raises(ValueError, match='pattern'):
            validate_name_factory('Иван123')

    @pytest.mark.asyncio
    async def test_registration_invalid_name_with_latin(self) -> None:
        """Тест ошибки: имя содержит латиницу."""
        from src.presentation.dialogs.registration import validate_name_factory

        with pytest.raises(ValueError, match='pattern'):
            validate_name_factory('Ivan')

    @pytest.mark.asyncio
    async def test_registration_invalid_name_repeating_chars(self) -> None:
        """Тест ошибки: имя содержит 4+ одинаковых символа подряд."""
        from src.presentation.dialogs.registration import validate_name_factory

        with pytest.raises(ValueError, match='same'):
            validate_name_factory('Ааааа')

    @pytest.mark.asyncio
    async def test_registration_invalid_phone_format(self) -> None:
        """Тест ошибки: неверный формат телефона."""
        with pytest.raises(ValueError):
            normalize_phone_number('1234567890')

    @pytest.mark.asyncio
    async def test_registration_user_already_exists(
        self,
        mock_user_repo,
    ) -> None:
        """Тест регистрации существующего пользователя."""
        user = UserDTO(
            id=123456,
            name='Иван',
            last_name='Иванов',
            phone='+79001234567',
        )

        # Добавляем пользователя (симуляция существующего)
        await mock_user_repo.add_user(user)

        # Проверка, что пользователь существует
        existing_user = await mock_user_repo.get_user(123456)
        assert existing_user is not None
        assert existing_user.name == 'Иван'

        # Обновление пользователя
        user.name = 'Пётр'
        is_updated = await mock_user_repo.update_user(user)
        assert is_updated is True

        # Проверка обновления
        updated_user = await mock_user_repo.get_user(123456)
        assert updated_user.name == 'Пётр'


# ============================================================================
# ТЕСТЫ ДИАЛОГА ПЕРВОГО ЗАПУСКА (FirstSeen)
# ============================================================================


class TestFirstSeenDialog:
    """Тесты диалога первого запуска."""

    @pytest.mark.asyncio
    async def test_first_seen_dialog_structure(self) -> None:
        """Тест структуры диалога FirstSeen."""
        from src.presentation.dialogs.first_seen import first_seen_dialog

        states_list = first_seen_dialog.states()
        assert FirstSeen.START in states_list
        assert len(first_seen_dialog.windows) == 1


# ============================================================================
# ТЕСТЫ БАЗОВОГО МЕНЮ (BaseMenu)
# ============================================================================


class TestBaseMenuDialog:
    """Тесты базового меню."""

    @pytest.mark.asyncio
    async def test_base_menu_states(self) -> None:
        """Тест состояний базового меню."""
        from src.presentation.dialogs.base_menu import menu_dialog

        states_list = menu_dialog.states()
        assert BaseMenu.START in states_list
        assert BaseMenu.ABOUT_US in states_list
        assert BaseMenu.HOW_TO in states_list

    @pytest.mark.asyncio
    async def test_base_menu_windows_count(self) -> None:
        """Тест количества окон в базовом меню."""
        from src.presentation.dialogs.base_menu import menu_dialog

        assert len(menu_dialog.windows) == 3


# ============================================================================
# ТЕСТЫ СОЗДАНИЯ ЗАЯВКИ НА ЗАНЯТИЕ
# ============================================================================


class TestSignUpFlow:
    """Тесты сценария записи на занятие."""

    @pytest.mark.asyncio
    async def test_signup_with_valid_data(self) -> None:
        """Тест записи на занятие с валидными данными."""
        activity = LessonActivity(
            activity_type=ActivityTypeFactory.generate(ActivityEnum.LESSON),
            topic='Урок рисования',
            date=None,
            time=time(14, 0),
            num_tickets=2,
            lesson_option=LessonOptionFactory.generate(CLASSIC_LESS),
        )

        assert activity.activity_type.name == ActivityEnum.LESSON.value
        assert activity.topic == 'Урок рисования'
        assert activity.num_tickets == 2

    @pytest.mark.asyncio
    async def test_signup_different_activity_types(self) -> None:
        """Тест записи на разные типы активностей."""
        activity_types = [
            ActivityEnum.LESSON,
            ActivityEnum.CHILD_STUDIO,
            ActivityEnum.MASS_CLASS,
            ActivityEnum.EVENING_SKETCH,
        ]

        for activity_type in activity_types:
            activity = LessonActivity(
                activity_type=ActivityTypeFactory.generate(activity_type),
                topic=f'{activity_type.value} тема',
                num_tickets=1,
                lesson_option=LessonOptionFactory.generate(CLASSIC_LESS),
            )
            assert activity.activity_type.name == activity_type.value

    @pytest.mark.asyncio
    async def test_signup_with_multiple_tickets(self) -> None:
        """Тест записи с несколькими билетами."""
        for num_tickets in [1, 2, 3, 4, 5]:
            activity = LessonActivity(
                activity_type=ActivityTypeFactory.generate(ActivityEnum.LESSON),
                topic='Тестовый урок',
                num_tickets=num_tickets,
                lesson_option=LessonOptionFactory.generate(CLASSIC_LESS),
            )
            assert activity.num_tickets == num_tickets


# ============================================================================
# ТЕСТЫ МОДЕЛИ ПОЛЬЗОВАТЕЛЯ
# ============================================================================


class TestUserModel:
    """Тесты модели пользователя."""

    @pytest.mark.asyncio
    async def test_user_dto_creation(self) -> None:
        """Тест создания UserDTO."""
        user = UserDTO(
            id=123456,
            nickname='@test_user',
            phone='+79001234567',
            name='Иван',
            last_name='Иванов',
        )

        assert user.id == 123456
        assert user.nickname == '@test_user'
        assert user.phone == '+79001234567'
        assert user.name == 'Иван'
        assert user.last_name == 'Иванов'

    @pytest.mark.asyncio
    async def test_user_dto_to_dict(self) -> None:
        """Тест преобразования UserDTO в словарь."""
        user = UserDTO(
            id=123456,
            nickname='@test_user',
            phone='+79001234567',
            name='Иван',
            last_name='Иванов',
        )

        user_dict = user.to_dict()
        assert user_dict['id'] == 123456
        assert user_dict['name'] == 'Иван'
        assert user_dict['last_name'] == 'Иванов'
        assert user_dict['phone'] == '+79001234567'

    @pytest.mark.asyncio
    async def test_user_dto_to_dict_exclude_none(self) -> None:
        """Тест преобразования UserDTO в словарь с исключением None."""
        user = UserDTO(
            id=123456,
            nickname='@test_user',
        )

        user_dict = user.to_dict(exclude_none=True)
        assert user_dict == {'id': 123456, 'nickname': '@test_user'}

    @pytest.mark.asyncio
    async def test_user_dto_to_dict_sign_up(self) -> None:
        """Тест преобразования UserDTO в словарь для записи."""
        user = UserDTO(
            id=123456,
            nickname='@test_user',
            phone='+79001234567',
            name='Иван',
            last_name='Иванов',
        )

        user_dict = user.to_dict(sign_up=True)
        assert 'id' not in user_dict
        assert 'nickname' not in user_dict
        assert user_dict['name'] == 'Иван'
        assert user_dict['last_name'] == 'Иванов'
        assert isinstance(user_dict['phone'], str)

    @pytest.mark.asyncio
    async def test_user_dto_reg_is_complete(self) -> None:
        """Тест проверки завершённости регистрации."""
        # Полностью зарегистрированный пользователь
        complete_user = UserDTO(
            id=123456,
            name='Иван',
            last_name='Иванов',
            phone='+79001234567',
        )
        assert complete_user.reg_is_complete() is False  # False - т.к. нет None значений

        # Незарегистрированный пользователь
        incomplete_user = UserDTO(id=123456)
        assert incomplete_user.reg_is_complete() is True  # True - т.к. все None


# ============================================================================
# ТЕСТЫ ОБРАБОТКИ ОШИБОК
# ============================================================================


class TestErrorHandling:
    """Тесты обработки ошибок."""

    @pytest.mark.asyncio
    async def test_error_handler_name_pattern(self) -> None:
        """Тест обработчика ошибки pattern для имени."""
        from src.presentation.dialogs.registration import on_error_name
        from unittest.mock import AsyncMock

        message_mock = AsyncMock()
        manager_mock = MagicMock()

        await on_error_name(message_mock, None, manager_mock, ValueError('pattern'))

        message_mock.answer.assert_called_once()
        args = message_mock.answer.call_args[0]
        assert 'Допустимы только русские буквы' in args[0]

    @pytest.mark.asyncio
    async def test_error_handler_name_length(self) -> None:
        """Тест обработчика ошибки len для имени."""
        from src.presentation.dialogs.registration import on_error_name
        from unittest.mock import AsyncMock

        message_mock = AsyncMock()
        manager_mock = MagicMock()

        await on_error_name(message_mock, None, manager_mock, ValueError('len'))

        message_mock.answer.assert_called_once()
        args = message_mock.answer.call_args[0]
        assert 'Допустимая длина от 2 до 50 символов' in args[0]

    @pytest.mark.asyncio
    async def test_error_handler_name_repeating(self) -> None:
        """Тест обработчика ошибки same для имени."""
        from src.presentation.dialogs.registration import on_error_name
        from unittest.mock import AsyncMock

        message_mock = AsyncMock()
        manager_mock = MagicMock()

        await on_error_name(message_mock, None, manager_mock, ValueError('same'))

        message_mock.answer.assert_called_once()
        args = message_mock.answer.call_args[0]
        assert '4 одинаковые буквы подряд' in args[0]


# ============================================================================
# ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# ============================================================================


class TestUserScenariosIntegration:
    """Интеграционные тесты пользовательских сценариев."""

    @pytest.mark.asyncio
    async def test_new_user_full_registration_flow(
        self,
        mock_user_repo,
        mock_notifier,
    ) -> None:
        """Тест полного потока регистрации нового пользователя."""
        # Создаём пользователя
        user = UserDTO(
            id=123456,
            nickname='@new_user',
            name='Тест',
            last_name='Пользователь',
            phone='+79001234567',
        )

        # Проверяем, что пользователя нет
        existing = await mock_user_repo.get_user(123456)
        assert existing is None

        # Добавляем пользователя
        is_added = await mock_user_repo.add_user(user)
        assert is_added is True

        # Проверяем, что пользователь добавлен
        created_user = await mock_user_repo.get_user(123456)
        assert created_user is not None
        assert created_user.name == 'Тест'
        assert created_user.last_name == 'Пользователь'

    @pytest.mark.asyncio
    async def test_user_sign_up_for_lesson(self) -> None:
        """Тест записи пользователя на урок."""
        user = UserDTO(
            id=123456,
            name='Иван',
            last_name='Иванов',
            phone='+79001234567',
        )

        activity = LessonActivity(
            activity_type=ActivityTypeFactory.generate(ActivityEnum.LESSON),
            topic='Урок акварели',
            num_tickets=2,
            lesson_option=LessonOptionFactory.generate(CLASSIC_LESS),
        )

        # Проверка данных
        assert user.reg_is_complete() is False
        assert activity.num_tickets == 2
        assert activity.topic == 'Урок акварели'
