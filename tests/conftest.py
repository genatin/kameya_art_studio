import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Dispatcher
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ChatMemberMember, ChatMemberOwner
from aiogram_dialog import Dialog, DialogManager, StartMode, Window, setup_dialogs
from aiogram_dialog.test_tools import BotClient, MockMessageManager
from aiogram_dialog.test_tools.memory_storage import JsonMemoryStorage
from aiogram_dialog.widgets.text import Format
from aiosqlite import IntegrityError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.application.domen.models.activity_type import ActivityEnum
from src.infrastracture.adapters.repositories.users import RepositoryUser
from src.infrastracture.database.sqlite.base import de_emojify, init_db
from src.infrastracture.database.sqlite.db import Base
from src.infrastracture.database.sqlite.models import (
    Activity,
    ActivityType,
    ActivityTypeEnum,
    User,
)
from src.infrastracture.repository.users import UsersService
from src.presentation.dialogs.admin import (
    admin_dialog,
    admin_payments_dialog,
    admin_reply_dialog,
    change_activity_dialog,
)
from src.presentation.dialogs.base_menu import menu_dialog
from src.presentation.dialogs.developer import developer_dialog
from src.presentation.dialogs.first_seen import first_seen_dialog
from src.presentation.dialogs.payments_approve import payments_approve_dialog
from src.presentation.dialogs.registration import registration_dialog
from src.presentation.dialogs.sign_up import activity_pages_dialog, signup_dialog
from src.presentation.handlers.deleoper_router import developer_router
from src.presentation.handlers.router import main_router, not_handled_router
from tests.config import get_test_config
from tests.mocks import MockRedisRepository, MockRepository, UsersServiceMock


@pytest.fixture(scope='session')
async def test_engine():
    """Создание тестового engine."""
    config = get_test_config()

    # Создаем engine с параметрами для тестов
    engine = create_async_engine(
        config.db_url,
    )
    yield engine

    # Закрываем соединения и удаляем БД
    await engine.dispose()
    config.cleanup()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Создание тестовой сессии."""
    # Создаем sessionmaker для тестов
    TestAsyncSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with TestAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture(scope='session')
async def test_session_maker(test_engine):
    """Создание тестового session maker."""
    session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    await init_db(session)


@pytest.fixture
async def clean_db(test_session: AsyncSession):
    """Очистка базы данных перед тестом."""
    # Удаляем все данные из таблиц в правильном порядке (с учетом внешних ключей)
    async with test_session.begin():
        await test_session.execute(User.__table__.delete())
        await test_session.execute(Activity.__table__.delete())
        await test_session.execute(ActivityType.__table__.delete())

    yield test_session


# Фикстуры для репозиториев
@pytest.fixture
def user_repository(test_session_maker):
    """Создание тестового репозитория пользователей."""

    return RepositoryUser(test_session_maker)


@pytest.fixture
def activity_repository(test_session_maker):
    """Создание тестового репозитория активностей."""
    from src.infrastracture.adapters.repositories.activities import ActivityRepository

    # Мокаем Redis для тестов
    mock_redis = MagicMock()
    mock_redis.delete = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()

    return ActivityRepository(mock_redis, test_session_maker)


# Фикстуры для сервисов
@pytest.fixture
def users_service(user_repository):
    """Создание тестового сервиса пользователей."""

    # Мокаем Redis для тестов
    mock_redis = MagicMock()
    mock_redis.save_user = AsyncMock()
    mock_redis.get_user = AsyncMock(return_value=None)
    mock_redis.delete_user = AsyncMock()

    return UsersService(cache_time=300, repository=user_repository, redis=mock_redis)


# Тестовые данные
@pytest.fixture
def sample_user_data():
    """Тестовые данные пользователя."""
    return {
        'id': 123456789,
        'nickname': 'test_user',
        'phone': '+79123456789',
        'name': 'Test',
        'last_name': 'User',
    }


@pytest.fixture
def sample_activity_data():
    """Тестовые данные активности."""
    return {
        'activity_type': 'masterclass',
        'theme': 'Тестовый мастер-класс',
        'image_id': 'test_image_123',
        'content_type': 'photo',
        'description': 'Тестовое описание',
    }


@pytest.fixture
async def seeded_activity_types(test_session: AsyncSession):
    """Создание тестовых типов активностей."""
    async with test_session.begin():
        existing_types = (await test_session.execute(select(ActivityType.name))).all()
        try:
            # Создаем предопределенные типы, если их нет
            for activity_type in ActivityTypeEnum:
                safe_str = de_emojify(activity_type)
                if safe_str not in existing_types:
                    test_session.add(ActivityType(name=safe_str))

            await test_session.commit()
        except IntegrityError:
            await test_session.rollback()
        finally:
            await test_session.close()


@pytest.fixture
def message_manager():
    return MockMessageManager()


@pytest.fixture
def dp(message_manager):
    dp = Dispatcher(
        storage=JsonMemoryStorage(),
        repository=MockRepository(UsersServiceMock()),
        redis_repository=MockRedisRepository(),
    )
    dp.include_routers(
        main_router,
        developer_router,
        registration_dialog,
        first_seen_dialog,
        menu_dialog,
        signup_dialog,
        activity_pages_dialog,
        admin_reply_dialog,
        admin_dialog,
        admin_payments_dialog,
        payments_approve_dialog,
        change_activity_dialog,
        developer_dialog,
        not_handled_router,
    )
    setup_dialogs(dp, message_manager=message_manager)
    return dp


@pytest.fixture
def client(dp):
    return BotClient(dp)
