import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import ContentType, Message
from aiogram_dialog import Dialog, DialogManager, LaunchMode, StartMode, Window
from aiogram_dialog.widgets.kbd import Cancel, Start
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format

from src.application.domen.text import ru
from src.config import get_config
from src.infrastracture.adapters.repositories.repo import GspreadRepository
from src.presentation.dialogs.registration import send_contact
from src.presentation.dialogs.states import BaseMenu, FirstSeen, Registration, SignUp
from src.presentation.dialogs.utils import get_user

router = Router()
logger = logging.getLogger(__name__)


menu_dialog = Dialog(
    Window(
        StaticMedia(
            path=get_config().WELCOME_IMAGE_PATH,
            type=ContentType.PHOTO,
        ),
        Format("Рады тебя видеть, {user.name}!", when=F["user"]),
        Format(
            "{event.from_user.full_name} привет, \n\n--- здесь вы можете записаться на ---",
            when=~F["user"],
        ),
        Start(
            Const("✍️ Записаться"),
            id="as",
            state=SignUp.START,
            when=F["user"],
        ),
        Start(
            Const("✍️ Записаться"),
            id="sign_up",
            when=~F["user"],
            state=Registration.GET_CONTACT,
            on_click=send_contact,
        ),
        Start(Const("О студии"), id="aaa", state=BaseMenu.ABOUT_US),
        state=BaseMenu.START,
        getter=get_user,
    ),
    Window(
        StaticMedia(
            path="src/static_data/welcome_photo.jpg",
            type=ContentType.PHOTO,
        ),
        Format(
            "{event.from_user.full_name} привет, \n\n--- здесь вы можете записаться на урок ---\n\nчтобы продолжить понадобится ваш номер телефона"
        ),
        Cancel(text=Const(ru.back_step)),
        state=BaseMenu.ABOUT_US,
    ),
    launch_mode=LaunchMode.ROOT,
)


@router.message(Command("start"))
async def cmd_hello(
    message: Message,
    dialog_manager: DialogManager,
    repository: GspreadRepository,
):
    user = await repository.user.get_user(message.from_user.id)
    state = FirstSeen.START if not user else BaseMenu.START
    await dialog_manager.start(state, mode=StartMode.RESET_STACK)


@router.message(Command("sign_up"))
@router.message(F.text == ru.sign_up)
async def sign_up_handler(
    message: Message, dialog_manager: DialogManager, repository: GspreadRepository
):
    await dialog_manager.start(SignUp.START, mode=StartMode.RESET_STACK)


@router.message(Command("registration"))
async def registration_handler(
    message: Message,
    dialog_manager: DialogManager,
    repository: GspreadRepository,
):
    await repository.user.remove_user(message.from_user.id)
    await dialog_manager.start(BaseMenu.START)
