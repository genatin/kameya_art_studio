import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode

from src.application.domen.text import ru
from src.config import get_config
from src.infrastracture.adapters.repositories.repo import GspreadRepository
from src.presentation.dialogs.states import (
    Administration,
    AdminReply,
    BaseMenu,
    FirstSeen,
    SignUp,
)
from src.presentation.dialogs.utils import SignUpCallbackFactory

main_router = Router()


@main_router.message(Command("start"))
async def cmd_hello(
    message: Message,
    dialog_manager: DialogManager,
    repository: GspreadRepository,
):
    user = await repository.user.get_user(message.from_user.id)
    state = FirstSeen.START if not user else BaseMenu.START
    await dialog_manager.start(state, mode=StartMode.RESET_STACK)


@main_router.message(Command("sign_up"))
@main_router.message(F.text == ru.sign_up)
async def sign_up_handler(
    message: Message, dialog_manager: DialogManager, repository: GspreadRepository
):
    await dialog_manager.start(SignUp.START, mode=StartMode.RESET_STACK)


@main_router.message(Command("registration"))
async def registration_handler(
    message: Message,
    dialog_manager: DialogManager,
    repository: GspreadRepository,
):
    await repository.user.remove_user(message.from_user.id)
    await dialog_manager.start(BaseMenu.START, data="after_reg")


@main_router.callback_query(SignUpCallbackFactory.filter())
async def sign_up_callback_handler(
    cq: CallbackQuery,
    callback_data: SignUpCallbackFactory,
    dialog_manager: DialogManager,
    repository: GspreadRepository,
):
    await dialog_manager.start(
        AdminReply.REPLY, data=callback_data.dict(), mode=StartMode.RESET_STACK
    )
