import asyncio

from aiogram import Bot, Dispatcher
from aiogram_dialog import setup_dialogs

from src.adapters.repositories.gspread.gspread_worker import gspread_repository
from src.config import get_config
from src.dialogs.base_menu import menu_dialog, router
from src.dialogs.first_seend import first_seen_dialog
from src.dialogs.registration import registration_dialog
from src.dialogs.sign_up import signup_dialog
from src.facade.users import users_facade
from src.handlers.setup import CheckIsUserReg


async def main():
    bot = Bot(token=get_config().bot_token.get_secret_value())
    dp = Dispatcher()
    router.message.middleware(CheckIsUserReg())
    dp.include_routers(
        first_seen_dialog, router, menu_dialog, registration_dialog, signup_dialog
    )
    setup_dialogs(dp)
    gspread_repository.run_background_update()
    users_facade.load_from_database_to_cache()
    await dp.start_polling(bot)


asyncio.run(main())
