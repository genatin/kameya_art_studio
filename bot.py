import asyncio
import logging
from functools import partial
from json import dumps

from aiogram import Bot, Dispatcher
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.exceptions import UnknownIntent
from redis.asyncio.client import Redis

from src.config import get_config
from src.infrastracture import users_repository
from src.infrastracture.adapters.repositories.gspread_users import gspread_repository
from src.presentation.dialogs.base_menu import menu_dialog, on_unknown_intent, router
from src.presentation.dialogs.first_seend import first_seen_dialog
from src.presentation.dialogs.registration import registration_dialog
from src.presentation.dialogs.sign_up import signup_dialog
from src.presentation.dialogs.utils import EnhancedJSONEncoder, error_handler
from src.presentation.handlers.setup import CheckIsUserReg

logger = logging.getLogger(__name__)


async def main():
    config = get_config()
    bot = Bot(token=config.bot_token.get_secret_value())
    logging.basicConfig(level=logging.INFO)
    logger.info("lllol")
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
    router.message.middleware(CheckIsUserReg())
    dp.errors.register(
        on_unknown_intent,
        ExceptionTypeFilter(UnknownIntent),
    )
    dp.errors.register(error_handler)
    dp.include_routers(
        first_seen_dialog,
        router,
        signup_dialog,
        menu_dialog,
        registration_dialog,
    )
    setup_dialogs(dp)
    gspread_repository.run_background_update()
    users = gspread_repository.load_users_from_gsheet()
    users_repository.collector.update_cache(users)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
