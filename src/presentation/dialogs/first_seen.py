from typing import Any

from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities import ShowMode
from aiogram_dialog.widgets.kbd import Start
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const

from src.infrastracture.adapters.repositories.repo import UsersRepository
from src.presentation.dialogs.states import BaseMenu, FirstSeen
from src.presentation.dialogs.utils import FILE_ID, get_base_menu_image


async def get_base_menu_data(
    dialog_manager: DialogManager, repository: UsersRepository, **kwargs
) -> dict[str, Any]:
    return {FILE_ID: await get_base_menu_image(dialog_manager, repository)}


first_seen_dialog = Dialog(
    Window(
        DynamicMedia(FILE_ID, when=FILE_ID),
        Const(
            'Приветствуем в творческом пространстве 🎨✨\n'
            'Рады видеть вас в нашей арт-студии Камея! '
            '\nЗдесь вы найдете мастер-классы, '
            'уроки и вдохновение для любого уровня.'
        ),
        Start(
            Const('Войти в мастерскую'),
            id='first_seen',
            state=BaseMenu.START,
            show_mode=ShowMode.SEND,
        ),
        state=FirstSeen.START,
        getter=get_base_menu_data,
    )
)
