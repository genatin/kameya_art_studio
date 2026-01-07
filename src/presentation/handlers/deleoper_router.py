import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager

from src.config import get_config
from src.infrastracture.adapters.repositories.repo import Repository
from src.presentation.dialogs.states import Developer
from src.presentation.notifier import Notifier

logger = logging.getLogger(__name__)
developer_router = Router()


@developer_router.message(Command('report'))
async def cmd_report(
    message: Message,
    dialog_manager: DialogManager,
    repository: Repository,
) -> None:
    try:
        await dialog_manager.start(Developer.START)
    except ValueError:
        await message.answer('Завершите предыдущее действие')


@developer_router.message(
    Command('send_to_admins'), F.from_user.id == get_config().DEVELOPER_ID
)
async def send_to_admins_handler(
    message: Message,
    dialog_manager: DialogManager,
    notifier: Notifier,
) -> None:
    try:
        await dialog_manager.start(Developer.TO_ADMIN)
    except ValueError:
        await message.answer('Завершите предыдущее действие')
