import asyncio
import logging

from aiogram import F
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import (
    CallbackQuery,
    ContentType,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities import LaunchMode, MediaAttachment, MediaId, ShowMode
from aiogram_dialog.widgets.common import ManagedScroll
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    CurrentPage,
    FirstPage,
    LastPage,
    Next,
    NextPage,
    PrevPage,
    Row,
    Start,
    StubScroll,
    SwitchTo,
)
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from src.application.domen.models.activity_type import (
    child_studio_act,
    evening_sketch_act,
    lesson_act,
    mclass_act,
)
from src.application.domen.text import RU
from src.config import get_config
from src.infrastracture.adapters.interfaces.repositories import (
    ActivityAbstractRepository,
)
from src.infrastracture.adapters.repositories.repo import UsersRepository
from src.infrastracture.database.redis.repository import RedisRepository
from src.presentation.callbacks import PaymentCallback, SignUpCallback
from src.presentation.dialogs.states import BaseMenu, Developer
from src.presentation.reminders.payment_reminder import PaymentReminder

_DEV_REPORT = "dev_report"


async def send_to_developer(
    event: Message, widget, dialog_manager: DialogManager, *_
) -> None:
    report = d.get_value() if (d := dialog_manager.find(_DEV_REPORT)) else ""
    await dialog_manager.event.bot.send_message(
        chat_id=get_config().DEVELOPER_ID,
        text="Сообщение об ошибке/пожелание от пользователя: \n\n"
        + "<i>"
        + report
        + "</i>",
        parse_mode=ParseMode.HTML,
    )
    await event.answer("Сообщение отправлено. Благодарим Вас!")
    await dialog_manager.start(BaseMenu.START)


developer_dialog = Dialog(
    Window(
        Format(
            "Мы очень хотим, чтобы Вам было удобно пользоваться нашим ботом, "
            "поэтому здесь можно оставить свои пожелания или сообщить об ошибках. "
            "Чем подробнее получится описать ошибку, тем быстрее мы её исправим. "
            "\n\n<i>Опишите проблему и отправьте обычным сообщением прямо тут</i>"
        ),
        TextInput(id=_DEV_REPORT, on_success=send_to_developer),
        Cancel(Const("Назад")),
        state=Developer.START,
        parse_mode=ParseMode.HTML,
    ),
)
