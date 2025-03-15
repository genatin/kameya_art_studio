import logging

import aiogram.utils.markdown as fmt
from aiogram import F, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import CallbackQuery, ContentType, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities import MediaAttachment, MediaId, ShowMode, StartMode
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import Back, Button
from aiogram_dialog.widgets.media import DynamicMedia, StaticMedia
from aiogram_dialog.widgets.text import Const, Format

from src.application.domen.text import ru
from src.application.models import UserDTO
from src.config import get_config
from src.infrastracture.adapters.repositories.repo import GspreadRepository
from src.presentation.dialogs.states import Admin
from src.presentation.dialogs.utils import SignUpCallbackFactory

logger = logging.getLogger(__name__)
_PARSE_MODE_TO_USER = ParseMode.MARKDOWN


async def message_admin_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    manager.dialog_data["admin_message"] = (
        f"Ответ от Камея Арт Студии:\n\n_{message.text or message.caption}_"
    )

    if message.photo or message.document:
        manager.dialog_data["admin_message"] += "\n\n_(Ниже прикрепляем документ)_"
        if message.photo:
            manager.dialog_data["image"] = message.photo[0].file_id
        if message.document:
            manager.dialog_data["document"] = message.document.file_id

    await manager.next()


async def send_to_user(
    callback: CallbackQuery, button: Button, manager: DialogManager, *_
):

    if manager.dialog_data["admin_message"]:
        await manager.event.bot.send_message(
            chat_id=manager.start_data["user_id"],
            text=manager.dialog_data["admin_message"],
            parse_mode=_PARSE_MODE_TO_USER,
        )
    if manager.dialog_data.get("image"):
        await manager.event.bot.send_photo(
            chat_id=manager.start_data["user_id"], photo=manager.dialog_data["image"]
        )
    if manager.dialog_data.get("document"):
        await manager.event.bot.send_document(
            chat_id=manager.start_data["user_id"],
            document=manager.dialog_data["document"],
        )
    await callback.message.answer("Сообщение отправлено пользователю")
    await manager.done()


async def get_image(dialog_manager: DialogManager, **kwargs):
    image = None
    if image_id := dialog_manager.dialog_data.get("image"):
        image = MediaAttachment(ContentType.PHOTO, file_id=MediaId(image_id))
    elif document_id := dialog_manager.dialog_data.get("document"):
        image = MediaAttachment(ContentType.DOCUMENT, file_id=MediaId(document_id))
    return {"image": image}


admin_dialog = Dialog(
    Window(
        Const(
            "Введите сообщение, которое хотите отправить пользователю \n\n*(можно прикрепить файл ИЛИ фото)*"
        ),
        MessageInput(message_admin_handler),
        state=Admin.REPLY,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Format("Сообщение будет выглядеть так: \n\n{dialog_data[admin_message]}"),
        DynamicMedia("image", when="image"),
        Back(Const("Исправить")),
        Button(Const("Отправить"), id="good", on_click=send_to_user),
        state=Admin.SEND,
        getter=get_image,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
)
