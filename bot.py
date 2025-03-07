import asyncio
import logging
from functools import partial
from json import dumps

import gspread
from aiogram import Bot, Dispatcher
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.exceptions import UnknownIntent, UnknownState
from redis.asyncio.client import Redis

from src.config import get_config
from src.infrastracture.adapters.repositories.lessons import (
    ChildLessonsRepository,
    LessonsRepository,
)
from src.infrastracture.adapters.repositories.repo import GspreadRepository
from src.infrastracture.adapters.repositories.users import RepositoryUser
from src.infrastracture.in_memory.users import InMemoryUsers
from src.infrastracture.repository.users import UsersRepository
from src.presentation.dialogs.base_menu import menu_dialog, router
from src.presentation.dialogs.first_seen import first_seen_dialog
from src.presentation.dialogs.registration import registration_dialog
from src.presentation.dialogs.sign_up import (
    child_lessons_dialog,
    lessons_dialog,
    signup_dialog,
)
from src.presentation.dialogs.utils import (
    EnhancedJSONEncoder,
    error_handler,
    on_unknown_intent,
    on_unknown_state,
)

logger = logging.getLogger(__name__)


async def main():
    config = get_config()
    bot = Bot(token=config.bot_token.get_secret_value())
    logging.basicConfig(level=logging.INFO)
    redis = Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD.get_secret_value(),
    )
    storage = RedisStorage(
        redis,
        key_builder=DefaultKeyBuilder(with_destiny=True),
        json_dumps=partial(dumps, cls=EnhancedJSONEncoder),
    )
    dp = Dispatcher(storage=storage)

    spreadsheet = gspread.service_account(filename=config.SERVICE_FILE_NAME).open(
        config.GSHEET_NAME
    )

    gspread_user = RepositoryUser(spreadsheet.worksheet(config.USERS_PAGE))
    gspread_user.run_background_update()

    users_repo = UsersRepository(
        users_collector=InMemoryUsers(), repository=gspread_user
    )
    users_repo.update_cache()

    lesssons_repo = LessonsRepository(spreadsheet.worksheet(config.LESSONS_PAGE))
    child_repo = ChildLessonsRepository(spreadsheet.worksheet(config.CHILD_PAGE))

    gspread_repository = GspreadRepository(users_repo, lesssons_repo, child_repo)

    dp.errors.register(
        on_unknown_intent,
        ExceptionTypeFilter(UnknownIntent),
    )
    dp.errors.register(
        on_unknown_state,
        ExceptionTypeFilter(UnknownState),
    )
    # dp.errors.register(error_handler)
    dp.include_routers(
        registration_dialog,
        router,
        first_seen_dialog,
        menu_dialog,
        signup_dialog,
        lessons_dialog,
        child_lessons_dialog,
    )
    setup_dialogs(dp)
    await dp.start_polling(bot, repository=gspread_repository)


if __name__ == "__main__":
    asyncio.run(main())
