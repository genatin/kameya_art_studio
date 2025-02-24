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

from src.adapters.repositories.gspread.gspread_worker import gspread_repository
from src.config import get_config
from src.dialogs.base_menu import menu_dialog, on_unknown_intent, router
from src.dialogs.first_seend import first_seen_dialog
from src.dialogs.registration import registration_dialog
from src.dialogs.sign_up import signup_dialog
from src.dialogs.utils import EnhancedJSONEncoder
from src.facade.users import users_facade
from src.handlers.setup import CheckIsUserReg


async def main():
    logging.basicConfig(level=logging.INFO)
    config = get_config()
    bot = Bot(token=config.bot_token.get_secret_value())

    storage = RedisStorage(
        Redis(host="redis", db=0, password=config.REDIS_PASSWORD.get_secret_value()),
        key_builder=DefaultKeyBuilder(with_destiny=True),
        json_dumps=partial(dumps, cls=EnhancedJSONEncoder),
    )

    dp = Dispatcher(storage=storage)
    router.message.middleware(CheckIsUserReg())
    dp.errors.register(
        on_unknown_intent,
        ExceptionTypeFilter(UnknownIntent),
    )
    dp.include_routers(
        first_seen_dialog, router, menu_dialog, registration_dialog, signup_dialog
    )
    setup_dialogs(dp)
    gspread_repository.run_background_update()
    users_facade.load_from_database_to_cache()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
