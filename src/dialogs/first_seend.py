from aiogram.types import CallbackQuery, ContentType
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities import MediaAttachment, ShowMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const

from src.cache.dto import UserDTO
from src.dialogs.states import BaseMenu, FirstSeen
from src.gspread_handler.gspread_worker import gspread_worker


async def getter_first_seen_video(**kwargs):
    return {
        "video": MediaAttachment(ContentType.VIDEO, path="src/data/welcome_video.MOV")
    }


async def add_user_firstly(cq: CallbackQuery, _, manager: DialogManager):
    gspread_worker.add_user(
        UserDTO(id=cq.from_user.id, nickname="@" + cq.from_user.username)
    )
    await manager.start(BaseMenu.START, show_mode=ShowMode.SEND)


first_seen_dialog = Dialog(
    Window(
        DynamicMedia("video"),
        Const("---------- О нас\n\n----"),
        Button(Const("Поехали!"), id="first_seend", on_click=add_user_firstly),
        state=FirstSeen.START,
        getter=getter_first_seen_video,
    )
)
