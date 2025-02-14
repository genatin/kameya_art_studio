from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import ContentType, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Cancel, Start
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format

from src.database.dto import UserDTO
from src.database.user_collector import user_collector
from src.dialogs.registration import send_contact
from src.dialogs.states import BaseMenu, Registration

router = Router()


async def getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    return {"user": user_collector.get_user(dialog_manager.event.from_user.id)}


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
            state=BaseMenu.END,
            when=F["start_data"]["user"],
        ),
        Start(
            Const("✍️ Записаться"),
            id="sign_up",
            when=~F["start_data"]["user"],
            state=Registration.GET_CONTACT,
            on_click=send_contact,
        ),
        Start(Const("О студии"), id="aaa", state=BaseMenu.ABOUT_US),
        state=BaseMenu.START,
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
    Window(Format("{user}"), state=BaseMenu.END),
    getter=getter,
)


@router.message(Command("start"))
async def cmd_hello(message: Message, dialog_manager: DialogManager, user: UserDTO):
    await dialog_manager.start(
        BaseMenu.START,
        data={"user": user.model_dump(exclude_none=True) if user else None},
    )


@router.message(Command("sign_up"))
async def sign_up_handler(
    message: Message, dialog_manager: DialogManager, user: UserDTO
):
    await dialog_manager.start(
        BaseMenu.END,
        data={"user": user.model_dump(exclude_none=True) if user else None},
    )
