import logging
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities import ShowMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const

from src.infrastracture.adapters.repositories.repo import UsersRepository
from src.presentation.dialogs.states import BaseMenu, FirstSeen
from src.presentation.dialogs.utils import FILE_ID, get_base_menu_image

logger = logging.getLogger(__name__)


async def get_base_menu_data(
    dialog_manager: DialogManager, repository: UsersRepository, **kwargs
) -> dict[str, Any]:
    return {FILE_ID: await get_base_menu_image(dialog_manager, repository)}


async def start_base_menu_with_dat(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.start(BaseMenu.START, data=manager.start_data, show_mode=ShowMode.SEND)


first_seen_dialog = Dialog(
    Window(
        DynamicMedia(FILE_ID, when=FILE_ID),
        Const(
            'Приветствуем в творческом пространстве 🎨✨\n'
            'Рады видеть вас в нашей арт-студии Камея! '
            '\nЗдесь вы найдете мастер-классы, '
            'уроки и вдохновение для любого уровня.'
        ),
        Button(
            Const('Войти в мастерскую'),
            id='first_seen',
            on_click=start_base_menu_with_dat,
        ),
        state=FirstSeen.START,
        getter=get_base_menu_data,
    )
)
