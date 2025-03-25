import logging

from aiogram import F
from aiogram.types import ContentType
from aiogram_dialog import Dialog, LaunchMode, Window
from aiogram_dialog.widgets.kbd import Back, Start
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format

from src.application.domen.text import ru
from src.config import get_config
from src.presentation.dialogs.registration import send_contact
from src.presentation.dialogs.states import (
    Administration,
    BaseMenu,
    Registration,
    SignUp,
)
from src.presentation.dialogs.utils import get_user

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
        Start(
            Const(ru.admin), id="admin", when=F["is_admin"], state=Administration.START
        ),
        state=BaseMenu.START,
        getter=get_user,
    ),
    Window(
        StaticMedia(
            path=f"{get_config().WELCOME_IMAGE_PATH}",
            type=ContentType.PHOTO,
        ),
        Format(
            "{event.from_user.full_name} привет, \n\n--- здесь вы можете записаться на урок ---\n\nчтобы продолжить понадобится ваш номер телефона"
        ),
        Back(text=Const(ru.back_step)),
        state=BaseMenu.ABOUT_US,
    ),
    launch_mode=LaunchMode.ROOT,
)
