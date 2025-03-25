import asyncio
import logging

import gspread
from aiogram import Bot
from aiogram.filters import ExceptionTypeFilter
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.exceptions import OutdatedIntent, UnknownIntent, UnknownState
from redis.asyncio.client import Redis

from src.application.factory.telegram import create_dispatcher
from src.config import get_config
from src.infrastracture.adapters.repositories.lessons import (
    ChildLessonsRepository,
    LessonsRepository,
)
from src.infrastracture.adapters.repositories.repo import GspreadRepository
from src.infrastracture.adapters.repositories.users import RepositoryUser
from src.infrastracture.database.redis.repository import RedisRepository
from src.infrastracture.database.sqlite.base import create_tables
from src.infrastracture.repository.users import UsersService
from src.presentation.dialogs.admin import (
    admin_dialog,
    admin_reply_dialog,
    change_mclass,
)
from src.presentation.dialogs.base_menu import menu_dialog
from src.presentation.dialogs.first_seen import first_seen_dialog
from src.presentation.dialogs.registration import registration_dialog
from src.presentation.dialogs.sign_up import (
    child_lessons_dialog,
    lessons_dialog,
    mass_classes_dialog,
    signup_dialog,
)
from src.presentation.dialogs.utils import (
    error_handler,
    on_unknown_intent,
    on_unknown_state,
)
from src.presentation.handlers.router import main_router

logger = logging.getLogger(__name__)


async def polling_startup(bots: list[Bot]) -> None:
    for bot in bots:
        await bot.delete_webhook(drop_pending_updates=True)


async def main():
    config = get_config()
    bot = Bot(token=config.bot_token.get_secret_value())
    logging.basicConfig(level=logging.INFO)

    spreadsheet = gspread.service_account(filename=config.SERVICE_FILE_NAME).open(
        config.GSHEET_NAME
    )
    await create_tables()
    gspread_user = RepositoryUser(spreadsheet.worksheet(config.USERS_PAGE))
    gspread_user.run_background_update()
    redis = Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD.get_secret_value(),
    )
    if get_config().LOCAL:
        await redis.flushdb()

    users_repo = UsersService(
        config=get_config(), redis=RedisRepository(redis), repository=gspread_user
    )

    lesssons_repo = LessonsRepository(spreadsheet.worksheet(config.LESSONS_PAGE))
    child_repo = ChildLessonsRepository(spreadsheet.worksheet(config.CHILD_PAGE))
    mclasses_repo = ChildLessonsRepository(spreadsheet.worksheet(config.MASTER_CL_PAGE))

    gspread_repository = GspreadRepository(
        users_repo, lesssons_repo, child_repo, mclasses_repo
    )
    dp = create_dispatcher(redis, repository=gspread_repository)

    dp.errors.register(
        on_unknown_intent,
        ExceptionTypeFilter(UnknownIntent, OutdatedIntent),
    )
    dp.errors.register(
        on_unknown_state,
        ExceptionTypeFilter(UnknownState),
    )
    dp.errors.register(error_handler)
    dp.include_routers(
        main_router,
        registration_dialog,
        first_seen_dialog,
        menu_dialog,
        signup_dialog,
        lessons_dialog,
        mass_classes_dialog,
        child_lessons_dialog,
        admin_reply_dialog,
        admin_dialog,
        change_mclass,
    )
    dp.startup.register(polling_startup)
    setup_dialogs(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
