import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import ContentType, ErrorEvent, Message, ReplyKeyboardRemove
from aiogram_dialog import Dialog, DialogManager, ShowMode, StartMode, Window
from aiogram_dialog.widgets.kbd import Cancel, Start
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format

from src.application.domen.text import ru
from src.application.models import UserDTO
from src.infrastracture import users_repository
from src.presentation.dialogs.registration import send_contact
from src.presentation.dialogs.states import BaseMenu, FirstSeen, Registration, SignUp
from src.presentation.dialogs.utils import get_cached_user

router = Router()


async def on_unknown_intent(event: ErrorEvent, dialog_manager: DialogManager):
    # Example of handling UnknownIntent Error and starting new dialog.
    logging.error("Restarting dialog: %s", event.exception)
    if event.update.callback_query:
        await event.update.callback_query.answer(
            "Bot process was restarted due to maintenance.\n"
            "Redirecting to main menu.",
        )
        if event.update.callback_query.message:
            try:
                await event.update.callback_query.message.delete()
            except TelegramBadRequest:
                pass  # whatever
    elif event.update.message:
        await event.update.message.answer(
            "Bot process was restarted due to maintenance.\n"
            "Redirecting to main menu.",
            reply_markup=ReplyKeyboardRemove(),
        )
    await dialog_manager.start(
        BaseMenu.START,
        mode=StartMode.NEW_STACK,
        show_mode=ShowMode.SEND,
    )


menu_dialog = Dialog(
    Window(
        StaticMedia(
            path="src/static_data/welcome_photo.jpg",
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
        getter=get_cached_user,
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


@router.message(Command("registration"))
async def registration_handler(
    message: Message, dialog_manager: DialogManager, user: UserDTO
):
    users_repository.collector.remove_user(user.id)
    await dialog_manager.start(BaseMenu.START)
