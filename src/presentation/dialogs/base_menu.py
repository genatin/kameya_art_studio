import logging

from aiogram import F
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import ContentType
from aiogram_dialog import Dialog, LaunchMode, Window
from aiogram_dialog.widgets.kbd import Back, Start, Url
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
        Format(
            "{user.name}, добро пожаловать в нашу творческую мастерскую! 🎨",
            when=F["user"],
        ),
        Start(
            Const("✍️ Записаться"),
            id="as",
            state=SignUp.START,
            when=F["user"],
        ),
        Format(
            "👋 {event.from_user.full_name} приветствуем в Арт-Студии Камея.\n\n<i>Для регистрации нажмите кнопку ниже</i>",
            when=~F["user"],
        ),
        Start(
            Const("📝 Зарегистрироваться"),
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
        parse_mode=ParseMode.HTML,
    ),
    Window(
        StaticMedia(
            path=f"{get_config().WELCOME_IMAGE_PATH}",
            type=ContentType.PHOTO,
        ),
        Format(
            """<b>О нашей арт-студии 🎨✨\n\nМы — пространство, где рождается творчество! Наша студия объединяет художников, новичков и всех, кто хочет раскрыть свой творческий потенциал.\n🔹 Мастер-классы и уроки для любого уровня\n🔹 Уютная атмосфера и индивидуальный подход\n🔹 Профессиональные материалы и поддержка педагогов\nПриходите за вдохновением, оставайтесь за результатом!</b>\n<i>Творите с удовольствием! 🖌️</i>"""
        ),
        Url(
            Const("Как к нам добраться"),
            Const("https://yandex.ru/maps/-/CHRzUEOc"),
        ),
        Back(text=Const(ru.back_step)),
        state=BaseMenu.ABOUT_US,
        parse_mode=ParseMode.HTML,
    ),
    launch_mode=LaunchMode.ROOT,
)
