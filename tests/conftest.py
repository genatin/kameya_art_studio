"""Конфигурация pytest с фикстурами для тестов."""
import asyncio
from collections.abc import AsyncGenerator, Generator, Sequence
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from aiogram import Bot
from aiogram.types import CallbackQuery, Chat, Message, User
from aiogram_dialog import DialogManager

from src.application.domen.models import LessonActivity
from src.application.domen.models.activity_type import ActivityEnum
from src.application.domen.models.lesson_option import LessonOption
from src.application.models import UserDTO
from src.config import get_config
from src.infrastracture.adapters.interfaces.repositories import (
    ActivityAbstractRepository,
    UsersAbstractRepository,
)
from src.infrastracture.adapters.repositories.repo import UsersRepository
from src.infrastracture.database.sqlite.models import Activity
from src.presentation.notifier import Notifier


# ============================================================================
# ASYNCIO SETUP
# ============================================================================


@pytest.fixture(scope='session')
def event_loop_policy() -> Any:
    """Политика для event loop в pytest-asyncio."""
    return asyncio.DefaultEventLoopPolicy()


# ============================================================================
# MOCK DATABASE (SQLite in-memory)
# ============================================================================


@pytest_asyncio.fixture
async def mock_database() -> AsyncGenerator[MagicMock, None]:
    """In-memory SQLite база данных для тестов."""
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:',
        connect_args={'check_same_thread': False},
    )

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Создаём таблицы
    from src.infrastracture.database.sqlite.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_mock = MagicMock()
    session_mock.async_session_maker = async_session_maker
    session_mock.engine = engine

    yield session_mock

    await engine.dispose()


# ============================================================================
# MOCK REDIS
# ============================================================================


@pytest_asyncio.fixture
async def mock_redis() -> AsyncGenerator[MagicMock, None]:
    """Mock Redis repository."""
    redis_mock = MagicMock()

    # Моки для операций с Redis
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.hset = AsyncMock(return_value=True)
    redis_mock.hget = AsyncMock(return_value=None)
    redis_mock.hgetall = AsyncMock(return_value={})
    redis_mock.hdel = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=0)
    redis_mock.expire = AsyncMock(return_value=True)

    yield redis_mock


# ============================================================================
# MOCK USER REPOSITORY
# ============================================================================


class MockUserRepository(UsersAbstractRepository):
    """Mock репозиторий пользователей для тестов."""

    def __init__(self) -> None:
        self._users: dict[int, UserDTO] = {}
        self._counter = 0

    async def add_user(self, user: UserDTO) -> bool:
        """Добавление пользователя."""
        if user.id not in self._users:
            self._users[user.id] = user
            return True
        return False

    async def update_user(self, user: UserDTO) -> bool:
        """Обновление пользователя."""
        if user.id in self._users:
            self._users[user.id] = user
            return True
        return False

    async def get_user(self, id: int) -> UserDTO | None:
        """Получение пользователя по ID."""
        return self._users.get(id)

    async def get_users(self) -> list[UserDTO] | None:
        """Получение всех пользователей."""
        return list(self._users.values())

    async def delete_user(self, id: int) -> UserDTO | None:
        """Удаление пользователя."""
        return self._users.pop(id, None)

    def clear(self) -> None:
        """Очистка хранилища."""
        self._users.clear()


@pytest_asyncio.fixture
async def mock_user_repo() -> AsyncGenerator[MockUserRepository, None]:
    """Mock репозиторий пользователей."""
    repo = MockUserRepository()
    yield repo
    repo.clear()


# ============================================================================
# MOCK ACTIVITY REPOSITORY
# ============================================================================


class MockActivityRepository(ActivityAbstractRepository):
    """Mock репозиторий активностей для тестов."""

    def __init__(self) -> None:
        self._activities: dict[str, Activity] = {}
        self._counter = 0

    async def add_activity(
        self,
        activity_type: str,
        theme: str,
        image_id: str,
        content_type: str,
        description: str | None = None,
        date_time: datetime | None = None,
    ) -> Activity | None:
        """Добавление активности."""
        self._counter += 1
        activity = Activity(
            id=self._counter,
            activity_type=activity_type,
            theme=theme,
            image_id=image_id,
            content_type=content_type,
            description=description,
            date_time=date_time,
        )
        key = f'{activity_type}:{theme}'
        self._activities[key] = activity
        return activity

    async def get_all_activity_by_type(
        self, activity_type: str
    ) -> Sequence[dict]:
        """Получение всех активностей по типу."""
        return [
            {
                'id': a.id,
                'activity_type': a.activity_type,
                'theme': a.theme,
                'image_id': a.image_id,
                'content_type': a.content_type,
                'description': a.description,
                'date_time': a.date_time,
            }
            for a in self._activities.values()
            if a.activity_type == activity_type
        ]

    async def update_activity_name_by_name(
        self, activity_type: str, old_theme: str, new_theme: str
    ) -> Activity | None:
        """Обновление названия активности."""
        key = f'{activity_type}:{old_theme}'
        if key in self._activities:
            activity = self._activities.pop(key)
            activity.theme = new_theme
            new_key = f'{activity_type}:{new_theme}'
            self._activities[new_key] = activity
            return activity
        return None

    async def update_activity_date_by_name(
        self,
        activity_type: str,
        theme: str,
        new_date: datetime | None = None,
    ) -> Activity | None:
        """Обновление даты активности."""
        key = f'{activity_type}:{theme}'
        if key in self._activities:
            self._activities[key].date_time = new_date
            return self._activities[key]
        return None

    async def update_activity_time_by_name(
        self,
        activity_type: str,
        theme: str,
        new_time: datetime | None = None,
    ) -> Activity | None:
        """Обновление времени активности."""
        key = f'{activity_type}:{theme}'
        if key in self._activities:
            self._activities[key].date_time = new_time
            return self._activities[key]
        return None

    async def update_activity_description_by_name(
        self, activity_type: str, theme: str, new_description: str
    ) -> Activity | None:
        """Обновление описания активности."""
        key = f'{activity_type}:{theme}'
        if key in self._activities:
            self._activities[key].description = new_description
            return self._activities[key]
        return None

    async def get_activity_by_theme_and_type(
        self,
        activity_type: str,
        theme: str,
    ) -> Activity:
        """Получение активности по теме и типу."""
        key = f'{activity_type}:{theme}'
        return self._activities.get(key)

    async def update_activity_fileid_by_name(
        self, activity_type: str, theme: str, file_id: str, content_type: str
    ) -> Activity | None:
        """Обновление файла активности."""
        key = f'{activity_type}:{theme}'
        if key in self._activities:
            self._activities[key].image_id = file_id
            self._activities[key].content_type = content_type
            return self._activities[key]
        return None

    async def remove_activity_by_theme_and_type(
        self, activity_type: str, theme: str
    ) -> None:
        """Удаление активности."""
        key = f'{activity_type}:{theme}'
        self._activities.pop(key, None)

    def clear(self) -> None:
        """Очистка хранилища."""
        self._activities.clear()
        self._counter = 0


@pytest_asyncio.fixture
async def mock_activity_repo() -> AsyncGenerator[MockActivityRepository, None]:
    """Mock репозиторий активностей."""
    repo = MockActivityRepository()
    yield repo
    repo.clear()


# ============================================================================
# MOCK USERS REPOSITORY (агрегатор)
# ============================================================================


@pytest_asyncio.fixture
async def mock_repository(
    mock_user_repo: MockUserRepository,
) -> AsyncGenerator[UsersRepository, None]:
    """Mock агрегированного репозитория UsersRepository."""
    # Создаём моки для дочерних репозиториев
    from unittest.mock import MagicMock

    mock_lessons_repo = MagicMock()
    mock_lessons_repo._sign_up_user = MagicMock(return_value='1')

    mock_child_lessons_repo = MagicMock()
    mock_child_lessons_repo._sign_up_user = MagicMock(return_value='1')

    mock_mclasses_repo = MagicMock()
    mock_mclasses_repo._sign_up_user = MagicMock(return_value='1')

    mock_evening_sketch_repo = MagicMock()
    mock_evening_sketch_repo._sign_up_user = MagicMock(return_value='1')

    repo = UsersRepository(
        user_repo=mock_user_repo,
        lessons_repo=mock_lessons_repo,
        child_lessons_repo=mock_child_lessons_repo,
        mclasses_repo=mock_mclasses_repo,
        evening_sketch_repo=mock_evening_sketch_repo,
    )

    yield repo


# ============================================================================
# MOCK NOTIFIER
# ============================================================================


@pytest_asyncio.fixture
async def mock_notifier() -> AsyncGenerator[AsyncMock, None]:
    """Mock для Notifier."""
    notifier_mock = AsyncMock(spec=Notifier)
    notifier_mock.admin_notify = AsyncMock()
    notifier_mock.sign_up_notify = AsyncMock()
    yield notifier_mock


# ============================================================================
# MOCK BOT
# ============================================================================


@pytest_asyncio.fixture
async def mock_bot() -> AsyncGenerator[MagicMock, None]:
    """Mock для aiogram Bot."""
    bot_mock = MagicMock(spec=Bot)

    # Моки для методов отправки сообщений
    bot_mock.send_message = AsyncMock()
    bot_mock.edit_message_text = AsyncMock()
    bot_mock.edit_message_reply_markup = AsyncMock()
    bot_mock.delete_message = AsyncMock()

    yield bot_mock


# ============================================================================
# MOCK DIALOG MANAGER
# ============================================================================


@pytest_asyncio.fixture
async def mock_dialog_manager(
    mock_bot: MagicMock,
    mock_repository: UsersRepository,
    mock_redis: MagicMock,
    mock_notifier: AsyncMock,
) -> AsyncGenerator[DialogManager, None]:
    """Mock для DialogManager."""
    manager_mock = MagicMock(spec=DialogManager)

    # Настройка middleware_data
    manager_mock.middleware_data = {
        'repository': mock_repository,
        'redis_repository': mock_redis,
        'notifier': mock_notifier,
    }

    # Настройка event
    manager_mock.event = MagicMock()
    manager_mock.event.bot = mock_bot
    manager_mock.event.from_user = MagicMock()
    manager_mock.event.from_user.id = 123456
    manager_mock.event.message = MagicMock()

    # Настройка dialog_data
    manager_mock.dialog_data = {}
    manager_mock.start_data = None

    # Моки для методов
    manager_mock.start = AsyncMock()
    manager_mock.done = AsyncMock()
    manager_mock.switch_to = AsyncMock()
    manager_mock.next = AsyncMock()

    yield manager_mock


# ============================================================================
# MOCK TELEGRAM OBJECTS
# ============================================================================


@pytest.fixture
def mock_telegram_user() -> User:
    """Mock Telegram User."""
    return User(
        id=123456,
        is_bot=False,
        first_name='Test',
        username='test_user',
    )


@pytest.fixture
def mock_telegram_chat() -> Chat:
    """Mock Telegram Chat."""
    return Chat(id=123456, type='private')


@pytest.fixture
def mock_telegram_message(
    mock_telegram_user: User,
    mock_telegram_chat: Chat,
) -> MagicMock:
    """Mock Telegram Message."""
    message_mock = MagicMock(spec=Message)
    message_mock.message_id = 1
    message_mock.from_user = mock_telegram_user
    message_mock.chat = mock_telegram_chat
    message_mock.text = '/start'
    message_mock.date = datetime.now()
    message_mock.reply_markup = None
    message_mock.answer = AsyncMock()
    message_mock.delete = AsyncMock()
    message_mock.edit_text = AsyncMock()
    return message_mock


@pytest.fixture
def mock_telegram_callback() -> MagicMock:
    """Mock Telegram CallbackQuery."""
    callback_mock = MagicMock(spec=CallbackQuery)
    callback_mock.id = 'test_callback'
    callback_mock.from_user = MagicMock()
    callback_mock.from_user.id = 123456
    callback_mock.data = 'test_data'
    callback_mock.message = MagicMock()
    callback_mock.message.answer = AsyncMock()
    callback_mock.message.delete = AsyncMock()
    callback_mock.message.edit_text = AsyncMock()
    return callback_mock


# ============================================================================
# MOCK CONFIG
# ============================================================================


@pytest.fixture
def mock_config() -> Generator[MagicMock, None]:
    """Mock конфигурации приложения."""
    config_mock = MagicMock()
    config_mock.bot_token = 'test_token'
    config_mock.admins = [123, 456]
    config_mock.DEVELOPER_ID = 123
    yield config_mock


# ============================================================================
# MOCK GOOGLE SHEETS
# ============================================================================


@pytest_asyncio.fixture
async def mock_google_sheets() -> AsyncGenerator[MagicMock, None]:
    """Mock для Google Sheets API."""
    sheets_mock = MagicMock()

    # Мок для worksheet
    worksheet_mock = MagicMock()
    worksheet_mock.row_values = MagicMock(return_value=['header1', 'header2'])
    worksheet_mock.find = MagicMock(return_value=MagicMock(col=1))
    worksheet_mock.update_cell = MagicMock()
    worksheet_mock.insert_row = MagicMock(return_value={'updates': {'updatedRange': 'A1'}})
    worksheet_mock.batch_update = MagicMock()
    worksheet_mock.get_all_values = MagicMock(return_value=[['header1', 'header2']])

    sheets_mock.open_by_key = MagicMock(return_value=MagicMock(
        worksheet=MagicMock(return_value=worksheet_mock)
    ))

    yield sheets_mock


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================


@pytest.fixture
def test_user_data() -> dict[str, Any]:
    """Тестовые данные пользователя."""
    return {
        'id': 123456,
        'nickname': '@test_user',
        'phone': '+79001234567',
        'name': 'Иван',
        'last_name': 'Иванов',
    }


@pytest.fixture
def test_user(test_user_data: dict[str, Any]) -> UserDTO:
    """Тестовый пользователь."""
    return UserDTO(**test_user_data)


@pytest.fixture
def test_activity_data() -> dict[str, Any]:
    """Тестовые данные активности."""
    return {
        'activity_type': ActivityEnum.LESSON,
        'topic': 'Тестовая активность',
        'description': 'Описание тестовой активности',
        'date': datetime(2024, 12, 1),
        'time': datetime(2024, 12, 1, 14, 0),
        'num_tickets': 2,
    }


@pytest.fixture
def test_lesson_activity(test_activity_data: dict[str, Any]) -> LessonActivity:
    """Тестовая активность для урока."""
    return LessonActivity(
        activity_type=ActivityEnum.LESSON,
        topic=test_activity_data['topic'],
        description=test_activity_data['description'],
        date=test_activity_data['date'],
        time=test_activity_data['time'],
        num_tickets=test_activity_data['num_tickets'],
        lesson_option=LessonOption.SIGN_UP,
    )


# ============================================================================
# PATCH FIXTURES
# ============================================================================


@pytest.fixture
def patch_get_config(mock_config: MagicMock) -> Generator[MagicMock, None]:
    """Patch для get_config."""
    with patch('src.config.get_config', return_value=mock_config):
        yield mock_config
