"""Конфигурация pytest для E2E тестов с дополнительными фикстурами."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from aiogram import Bot
from aiogram_dialog import DialogManager

from src.application.domen.models.activity_type import ActivityEnum
from src.application.models import UserDTO
from src.infrastracture.adapters.repositories.repo import UsersRepository

# ============================================================================
# E2E СПЕЦИФИЧНЫЕ ФИКСТУРЫ
# ============================================================================


@pytest_asyncio.fixture
async def e2e_bot() -> AsyncGenerator[MagicMock, None]:
    """Mock бота для E2E тестов."""
    bot_mock = MagicMock(spec=Bot)

    # Настраиваем методы бота
    bot_mock.send_message = AsyncMock()
    bot_mock.edit_message_text = AsyncMock()
    bot_mock.edit_message_reply_markup = AsyncMock()
    bot_mock.delete_message = AsyncMock()
    bot_mock.answer_callback_query = AsyncMock()

    yield bot_mock


@pytest_asyncio.fixture
async def e2e_dialog_manager(
    e2e_bot: MagicMock,
    mock_repository: UsersRepository,
    mock_redis: MagicMock,
    mock_notifier: AsyncMock,
) -> AsyncGenerator[DialogManager, None]:
    """Mock DialogManager для E2E тестов."""
    manager_mock = MagicMock(spec=DialogManager)

    # Настраиваем middleware_data
    manager_mock.middleware_data = {
        'repository': mock_repository,
        'redis_repository': mock_redis,
        'notifier': mock_notifier,
    }

    # Настраиваем event
    manager_mock.event = MagicMock()
    manager_mock.event.bot = e2e_bot
    manager_mock.event.from_user = MagicMock()
    manager_mock.event.from_user.id = 123456
    manager_mock.event.chat = MagicMock()
    manager_mock.event.chat.id = 123456

    # Настраиваем message
    manager_mock.event.message = MagicMock()
    manager_mock.event.message.message_id = 1
    manager_mock.event.message.chat = MagicMock()
    manager_mock.event.message.chat.id = 123456
    manager_mock.event.message.answer = AsyncMock()
    manager_mock.event.message.delete = AsyncMock()
    manager_mock.event.message.edit_text = AsyncMock()

    # Настраиваем callback_query
    manager_mock.event.callback_query = MagicMock()
    manager_mock.event.callback_query.message = MagicMock()
    manager_mock.event.callback_query.message.answer = AsyncMock()
    manager_mock.event.callback_query.message.delete = AsyncMock()
    manager_mock.event.callback_query.message.edit_text = AsyncMock()
    manager_mock.event.callback_query.answer = AsyncMock()

    # Настраиваем dialog_data и start_data
    manager_mock.dialog_data = {}
    manager_mock.start_data = None
    manager_mock.has_context = MagicMock(return_value=True)

    # Настраиваем методы менеджера
    manager_mock.start = AsyncMock()
    manager_mock.done = AsyncMock()
    manager_mock.switch_to = AsyncMock()
    manager_mock.next = AsyncMock()
    manager_mock.back = AsyncMock()
    manager_mock.find = MagicMock()

    # Настраиваем current_context
    context_mock = MagicMock()
    context_mock.widget_data = {}
    context_mock.state = MagicMock()
    context_mock.state.group = MagicMock(return_value='test_group')
    context_mock.start_data = {}
    manager_mock.current_context = MagicMock(return_value=context_mock)

    yield manager_mock


@pytest_asyncio.fixture
async def e2e_registered_user(mock_user_repo) -> UserDTO:
    """Создаёт зарегистрированного пользователя для E2E тестов."""
    user = UserDTO(
        id=123456,
        nickname='@e2e_test_user',
        phone='+79001234567',
        name='Тест',
        last_name='Пользователь',
    )

    await mock_user_repo.add_user(user)
    return user


@pytest_asyncio.fixture
async def e2e_admin_user(mock_user_repo) -> UserDTO:
    """Создаёт пользователя-администратора для E2E тестов."""
    user = UserDTO(
        id=123,  # ID из mock_config
        nickname='@admin',
        phone='+70000000000',
        name='Админ',
        last_name='Админов',
    )

    await mock_user_repo.add_user(user)
    return user


# ============================================================================
# ФИКСТУРЫ ДЛЯ ТЕСТОВ АКТИВНОСТЕЙ
# ============================================================================


@pytest.fixture
def sample_activities() -> list[dict]:
    """Сэмпл активностей для тестов."""
    return [
        {
            'id': 1,
            'activity_type': 'lesson',
            'theme': 'Урок акварели',
            'description': 'Основы работы с акварелью',
            'image_id': 'test_image_1',
            'content_type': 'photo',
            'date_time': None,
        },
        {
            'id': 2,
            'activity_type': 'child_studio',
            'theme': 'Детское творчество',
            'description': 'Занятия для детей от 6 лет',
            'image_id': 'test_image_2',
            'content_type': 'photo',
            'date_time': None,
        },
        {
            'id': 3,
            'activity_type': 'mass_class',
            'theme': 'Вечерний мастер-класс',
            'description': 'Мастер-класс для взрослых',
            'image_id': 'test_image_3',
            'content_type': 'photo',
            'date_time': None,
        },
        {
            'id': 4,
            'activity_type': 'evening_sketch',
            'theme': 'Вечерние наброски',
            'description': 'Рисование с натуры',
            'image_id': 'test_image_4',
            'content_type': 'photo',
            'date_time': None,
        },
    ]


@pytest.fixture
def activity_type_buttons() -> dict[str, str]:
    """Соответствие кнопок типам активностей."""
    return {
        'child_studio': ActivityEnum.CHILD_STUDIO.value,
        'mass_class': ActivityEnum.MASS_CLASS.value,
        'lesson': ActivityEnum.LESSON.value,
        'evening_sketch': ActivityEnum.EVENING_SKETCH.value,
    }


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФИКСТУРЫ ДЛЯ ТЕСТИРОВАНИЯ ДИАЛОГОВ
# ============================================================================


@pytest.fixture
def dialog_state_transitions() -> dict[str, dict[str, str]]:
    """Таблица переходов между состояниями диалогов."""
    return {
        'Registration': {
            'START': 'GET_CONTACT',
            'NAME': 'LASTNAME',
            'LASTNAME': 'GET_CONTACT',
            'GET_CONTACT': 'EDIT_CONTACT',
            'EDIT_CONTACT': 'END',
        },
        'BaseMenu': {
            'START': 'ABOUT_US',
            'ABOUT_US': 'HOW_TO',
            'HOW_TO': 'START',
        },
        'SignUp': {
            'START': 'STAY_FORM',
        },
        'ActivityPages': {
            'START': 'TICKETS',
            'TICKETS': 'START',
        },
    }


@pytest.fixture
def validation_patterns() -> dict[str, dict[str, list]]:
    """Паттерны валидации для полей ввода."""
    return {
        'name': {
            'valid': ['Иван', 'Мария', 'Александр', 'Анна'],
            'invalid': ['Ivan', 'Иван123', 'А', 'А' * 51, 'Ааааа'],
            'error_messages': ['pattern', 'len', 'same'],
        },
        'phone': {
            'valid': ['+79001234567', '89001234567'],
            'invalid': ['1234567890', '+7900', 'abc'],
            'error_messages': ['Номер должен состоять из 11 цифр'],
        },
    }


# ============================================================================
# ФИКСТУРЫ ДЛЯ ТЕСТИРОВАНИЯ УВЕДОМЛЕНИЙ
# ============================================================================


@pytest.fixture
def notification_templates() -> dict[str, str]:
    """Шаблоны уведомлений для проверки."""
    return {
        'new_user': 'К нам пожаловало новое дарование',
        'new_signup': 'Пользователь создал заявку',
        'admin_notify': 'Уведомление администраторам',
    }


# ============================================================================
# ФИКСТУРЫ ДЛЯ MOCKING TELEGRAM API
# ============================================================================


@pytest.fixture
def mock_telegram_api() -> Generator[MagicMock, None]:
    """Mock Telegram API для тестов."""
    api_mock = MagicMock()

    # Mock для send_message
    api_mock.send_message = AsyncMock(
        return_value=MagicMock(
            message_id=1,
            chat=MagicMock(id=123456),
        )
    )

    # Mock для edit_message_text
    api_mock.edit_message_text = AsyncMock(
        return_value=MagicMock(
            message_id=1,
            chat=MagicMock(id=123456),
        )
    )

    # Mock для delete_message
    api_mock.delete_message = AsyncMock(return_value=True)

    # Mock для answer_callback_query
    api_mock.answer_callback_query = AsyncMock(return_value=True)

    yield api_mock


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ТЕСТОВ
# ============================================================================


@pytest.fixture
def assert_message_sent() -> callable:
    """Функция для проверки отправки сообщения."""

    def _assert(
        bot_mock: MagicMock,
        text: str | None = None,
        chat_id: int = 123456,
        call_count: int = 1,
    ) -> None:
        """Проверяет, что сообщение было отправлено."""
        assert bot_mock.send_message.call_count == call_count

        if text is not None and call_count > 0:
            call_args = bot_mock.send_message.call_args
            assert call_args is not None

            # Проверяем chat_id
            if call_args[1]:
                assert call_args[1].get('chat_id') == chat_id

            # Проверяем текст
            if call_args[1] and 'text' in call_args[1]:
                assert text in call_args[1]['text']

    return _assert


@pytest.fixture
def assert_callback_answered() -> callable:
    """Функция для проверки ответа на callback."""

    def _assert(
        callback_mock: MagicMock,
        text: str | None = None,
        show_alert: bool = False,
        call_count: int = 1,
    ) -> None:
        """Проверяет, что callback был обработан."""
        assert callback_mock.answer.call_count == call_count

        if text is not None and call_count > 0:
            call_args = callback_mock.answer.call_args
            assert call_args is not None

            if call_args[1]:
                assert call_args[1].get('text') == text
                assert call_args[1].get('show_alert') == show_alert

    return _assert
