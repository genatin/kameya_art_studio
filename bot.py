import asyncio
from aiogram import Bot, Dispatcher
from config import config
from setup import setup_bot

from handlers import base_router



# Запуск бота
async def main():
    bot = Bot(token=config.bot_token.get_secret_value())
    dp = Dispatcher()
    dp.include_routers(base_router)
    setup_bot()
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())