from aiogram.types import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.api.entities import ShowMode
from aiogram_dialog.widgets.kbd import Start
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const

from src.config import get_config
from src.presentation.dialogs.states import BaseMenu, FirstSeen

first_seen_dialog = Dialog(
    Window(
        StaticMedia(path=get_config().first_photo_path, type=ContentType.PHOTO),
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
    )
)
