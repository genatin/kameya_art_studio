import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode

from src.application.domen.text import RU
from src.infrastracture.adapters.repositories.repo import UsersRepository
from src.infrastracture.database.redis.repository import RedisRepository
from src.presentation.callbacks import PaymentCallback, SignUpCallback
from src.presentation.dialogs.states import Developer
from src.presentation.middlewares.middleware import RegistrationMiddleware

logger = logging.getLogger(__name__)
developer_router = Router()


@developer_router.message(Command("report"))
async def cmd_report(
    message: Message,
    dialog_manager: DialogManager,
    repository: UsersRepository,
) -> None:
    try:
        await dialog_manager.start(Developer.START)
    except ValueError:
        await message.answer("Завершите предыдущее действие")
