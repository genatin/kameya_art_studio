import logging

from aiogram import F
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import ContentType
from aiogram_dialog import Dialog
from aiogram_dialog import LaunchMode
from aiogram_dialog import Window
from aiogram_dialog.widgets.kbd import Back
from aiogram_dialog.widgets.kbd import Next
from aiogram_dialog.widgets.kbd import Start
from aiogram_dialog.widgets.kbd import Url
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.text import Format

from src.application.domen.text import RU
from src.config import get_config
from src.presentation.dialogs.registration import send_contact
from src.presentation.dialogs.states import Administration
from src.presentation.dialogs.states import BaseMenu
from src.presentation.dialogs.states import Registration
from src.presentation.dialogs.states import SignUp
from src.presentation.dialogs.utils import get_user
from src.presentation.middlewares.middleware import RegistrationMiddleware

logger = logging.getLogger(__name__)

menu_dialog = Dialog(
    Window(
        StaticMedia(
            path=get_config().welcome_image_path,
            type=ContentType.PHOTO,
        ),
        Format(
            '{user.name}, добро пожаловать в нашу творческую мастерскую! 🎨',
            when=F['user'],
        ),
        Start(
            Const('✍️ Записаться'),
            id='as',
            state=SignUp.START,
            when=F['user'],
        ),
        Format(
            '👋 {event.from_user.full_name} '
            'приветствуем в Арт-Студии Камея.\n\n'
            '<i>Для регистрации нажмите кнопку ниже</i>',
            when=~F['user'],
        ),
        Start(
            Const('📝 Зарегистрироваться'),
            id='sign_up',
            when=~F['user'],
            state=Registration.GET_CONTACT,
            on_click=send_contact,
        ),
        Start(Const('О студии'), id='aaa', state=BaseMenu.ABOUT_US),
        Start(
            Const(RU.admin), id='admin', when=F['is_admin'], state=Administration.START
        ),
        state=BaseMenu.START,
        getter=get_user,
        parse_mode=ParseMode.HTML,
    ),
    Window(
        StaticMedia(
            path=get_config().about_video_path,
            type=ContentType.VIDEO,
        ),
        Format(
            '<b>О нашей арт-студии 🎨✨\n\n'
            'Мы — пространство, где рождается творчество!'
            '\nНаша студия объединяет художников, новичков и всех, '
            'кто хочет раскрыть свой творческий потенциал.\n'
            '🔹 Мастер-классы и уроки для любого уровня\n'
            '🔹 Уютная атмосфера и индивидуальный подход\n'
            '🔹 Профессиональные материалы и поддержка педагогов\n'
            'Приходите за вдохновением!</b>\n'
            '\n<i>Творите с удовольствием! 🖌️</i>'
        ),
        Url(
            Const('Отзывы о нас'),
            Const(RU.reviews_yandex),
        ),
        Next(Const('Как к нам добраться'), when=F['user']),
        Back(text=Const(RU.back_step)),
        state=BaseMenu.ABOUT_US,
        parse_mode=ParseMode.HTML,
        getter=get_user,
    ),
    Window(
        StaticMedia(path=get_config().how_to_video_path, type=ContentType.VIDEO),
        Const(
            f'<i>{RU.how_to}</i>'
            '\n\n<b>Адрес: шоссе Энтузиастов 72а, 5 этаж, 55 \n'
            'Домофон - 55.</b>'
        ),
        Url(
            Const('Маршрут. Яндекс Карты.'),
            Const(RU.coordinates_yandex),
        ),
        Back(text=Const(RU.back_step)),
        state=BaseMenu.HOW_TO,
        parse_mode=ParseMode.HTML,
    ),
    launch_mode=LaunchMode.ROOT,
)

menu_dialog.message.middleware(RegistrationMiddleware())
