from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import ContentType, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Cancel, Start, SwitchTo
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format

from src.database.interfaces.models import UserDTO
from src.dialogs.registration import send_contact
from src.dialogs.states import BaseMenu, FirstSeen, Registration, SignUp
from src.dialogs.utils import get_cached_user

router = Router()


menu_dialog = Dialog(
    Window(
        StaticMedia(
            path="src/data/welcome_photo.jpg",
            type=ContentType.PHOTO,
        ),
        Format(
            "{event.from_user.full_name} привет, \n\n--- здесь вы можете записаться на ---"
        ),
        Start(
            Const("✍️ Записаться"),
            id="as",
            state=SignUp.START,
            when="user",
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
        getter=get_cached_user,
    ),
    Window(
        StaticMedia(
            path="src/data/welcome_photo.jpg",
            type=ContentType.PHOTO,
        ),
        Format(
            "{event.from_user.full_name} привет, \n\n--- здесь вы можете записаться на урок ---\n\nчтобы продолжить понадобится ваш номер телефона"
        ),
        Cancel(text=Const("Назад")),
        state=BaseMenu.ABOUT_US,
    ),
)


@router.message(Command("start"))
async def cmd_hello(message: Message, dialog_manager: DialogManager, user: UserDTO):
    if not user:
        await dialog_manager.start(FirstSeen.START)
    else:
        await dialog_manager.start(
            BaseMenu.START,
            data={"user": user.to_dict(exclude_none=True)},
        )


@router.message(Command("sign_up"))
async def sign_up_handler(
    message: Message, dialog_manager: DialogManager, user: UserDTO
):
    await dialog_manager.start(
        SignUp.START,
        data={"user": user.to_dict(exclude_none=True) if user else None},
    )
