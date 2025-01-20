import asyncio

from aiogram import Bot, Dispatcher
from aiogram_dialog import setup_dialogs

from src.config import config
from src.database.user_collector import user_collector
from src.dialogs.sign_up import master, registration, router
from src.gspread_handler.gspread_worker import gspread_worker
from src.handlers.setup import CheckIsUserReg


async def main():
    bot = Bot(token=config.bot_token.get_secret_value())
    dp = Dispatcher()
    router.message.middleware(CheckIsUserReg())
    dp.include_routers(router, registration, master)
    setup_dialogs(dp)
    users = gspread_worker.load_users_from_gsheet()
    gspread_worker.run_background_update()
    user_collector.update_cache(users)
    await dp.start_polling(bot)


asyncio.run(main())
