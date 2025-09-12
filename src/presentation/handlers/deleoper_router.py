import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager

from src.infrastracture.adapters.repositories.repo import UsersRepository
from src.presentation.dialogs.states import Developer

logger = logging.getLogger(__name__)
developer_router = Router()


@developer_router.message(Command('report'))
async def cmd_report(
    message: Message,
    dialog_manager: DialogManager,
    repository: UsersRepository,
) -> None:
    try:
        await dialog_manager.start(Developer.START)
    except ValueError:
        await message.answer('Завершите предыдущее действие')
