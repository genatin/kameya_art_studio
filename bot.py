import asyncio

from aiogram import Bot, Dispatcher
from aiogram_dialog import setup_dialogs

from src.cache.user_collector import user_collector
from src.config import config
from src.dialogs.base_menu import menu_dialog, router
from src.dialogs.first_seend import first_seen_dialog
from src.dialogs.registration import registration_dialog
from src.dialogs.sign_up import signup_dialog
from src.gspread_handler.gspread_worker import gspread_worker
from src.handlers.setup import CheckIsUserReg


async def main():
    bot = Bot(token=config.bot_token.get_secret_value())
    dp = Dispatcher()
    router.message.middleware(CheckIsUserReg())
    dp.include_routers(
        first_seen_dialog, router, menu_dialog, registration_dialog, signup_dialog
    )
    setup_dialogs(dp)
    users = gspread_worker.load_users_from_gsheet()
    gspread_worker.run_background_update()
    user_collector.update_cache(users)
    await dp.start_polling(bot)


asyncio.run(main())
