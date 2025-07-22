import asyncio
import logging

import gspread

from aiogram import Bot
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.redis import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.exceptions import OutdatedIntent
from aiogram_dialog.api.exceptions import UnknownIntent
from aiogram_dialog.api.exceptions import UnknownState
from redis.asyncio.client import Redis

from src.application.factory.telegram import create_dispatcher
from src.application.utils import mjson
from src.config import get_config
from src.infrastracture.adapters.repositories.activities import ActivityRepository
from src.infrastracture.adapters.repositories.lessons import ChildLessonsRepository
from src.infrastracture.adapters.repositories.lessons import EveningSketchRepository
from src.infrastracture.adapters.repositories.lessons import LessonsRepository
from src.infrastracture.adapters.repositories.lessons import MCLassesRepository
from src.infrastracture.adapters.repositories.repo import UsersRepository
from src.infrastracture.adapters.repositories.users import RepositoryUser
from src.infrastracture.database.redis.repository import RedisRepository
from src.infrastracture.database.sqlite.base import init_db
from src.infrastracture.repository.users import UsersService
from src.presentation.dialogs.admin import admin_dialog
from src.presentation.dialogs.admin import admin_payments_dialog
from src.presentation.dialogs.admin import admin_reply_dialog
from src.presentation.dialogs.admin import change_activity_dialog
from src.presentation.dialogs.base_menu import menu_dialog
from src.presentation.dialogs.first_seen import first_seen_dialog
from src.presentation.dialogs.registration import registration_dialog
from src.presentation.dialogs.sign_up import activity_pages_dialog
from src.presentation.dialogs.sign_up import signup_dialog
from src.presentation.dialogs.utils import error_handler
from src.presentation.dialogs.utils import on_unknown_intent
from src.presentation.dialogs.utils import on_unknown_state
from src.presentation.handlers.router import main_router
from src.presentation.handlers.router import not_handled_router
from src.presentation.middlewares.throttling import ThrottlingMiddleware
from src.presentation.notifier import Notifier
from src.presentation.reminders.payment_reminder import PaymentReminder

logger = logging.getLogger(__name__)


async def polling_startup(bots: list[Bot]) -> None:
    for bot in bots:
        await bot.delete_webhook(drop_pending_updates=True)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    config = get_config()

    logger.info('Config init: %s', config.model_dump(exclude={'GOOGLE_SETTINGS'}))

    bot = Bot(token=config.bot_token.get_secret_value())

    spreadsheet = gspread.service_account_from_dict(
        config.google_settings.model_dump()
    ).open(config.GSHEET_NAME)
    await init_db()
    user_repository = RepositoryUser()
    redis = Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD.get_secret_value(),
        decode_responses=True,
    )
    # if get_config().LOCAL:
    #     await redis.flushdb()

    redis_repository = RedisRepository(redis)
    users_service = UsersService(
        cache_time=get_config().users_cache_time,
        redis=redis_repository,
        repository=user_repository,
    )

    lesssons_repo = LessonsRepository(spreadsheet.worksheet(config.LESSONS_PAGE))
    child_repo = ChildLessonsRepository(spreadsheet.worksheet(config.CHILD_PAGE))
    mclasses_repo = MCLassesRepository(spreadsheet.worksheet(config.MASTER_CL_PAGE))
    evening_sketch_repo = EveningSketchRepository(
        spreadsheet.worksheet(config.EVENING_PAGE)
    )

    gspread_repository = UsersRepository(
        users_service, lesssons_repo, child_repo, mclasses_repo, evening_sketch_repo
    )
    activity_repository = ActivityRepository(redis=redis_repository)

    storage = RedisStorage(
        redis,
        key_builder=DefaultKeyBuilder(with_destiny=True),
        json_dumps=mjson.encode,
        json_loads=mjson.decode,
    )
    payment_reminder = PaymentReminder(bot, redis_repository)
    await payment_reminder.start()

    dp = create_dispatcher(
        storage=storage,
        repository=gspread_repository,
        redis_repository=redis_repository,
        activity_repository=activity_repository,
        notifier=Notifier(),
        payment_notifier=payment_reminder,
    )
    dp.message.middleware.register(ThrottlingMiddleware(storage=storage))

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
        activity_pages_dialog,
        admin_reply_dialog,
        admin_dialog,
        admin_payments_dialog,
        change_activity_dialog,
        not_handled_router,
    )
    dp.startup.register(polling_startup)

    setup_dialogs(dp)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
