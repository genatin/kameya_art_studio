import contextlib
import logging
from datetime import date
from html import escape
from typing import Any

from aiogram.enums.parse_mode import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ContentType, ErrorEvent, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.common import ManagedScroll

from src.application.domen.models import LessonActivity
from src.application.domen.models.activity_type import ActivityType
from src.application.domen.text import RU
from src.config import get_config
from src.infrastracture.adapters.interfaces.repositories import (
    ActivityAbstractRepository,
)
from src.infrastracture.adapters.repositories.repo import UsersRepository
from src.infrastracture.database.redis.keys import AdminKey
from src.infrastracture.database.redis.repository import RedisRepository
from src.presentation.dialogs.states import BaseMenu

logger = logging.getLogger(__name__)

FILE_ID = 'file_id'
CONTENT_TYPE = 'content_type'

_MINUTE = 60
_HOUR = _MINUTE * 60
_DAY = _HOUR * 24
_MONTH = _DAY * 30
_SENDED = 'sended'


async def on_unknown_intent(event: ErrorEvent, dialog_manager: DialogManager) -> None:
    # Example of handling UnknownIntent Error and starting new dialog.
    logging.error('Restarting dialog: %s', event.exception)
    if event.update.callback_query:
        await event.update.callback_query.answer(
            'Bot process was restarted due to maintenance.\nRedirecting to main menu.',
        )
        if event.update.callback_query.message:
            message = event.update.callback_query.message
            with contextlib.suppress(TelegramBadRequest):
                await event.update.callback_query.message.delete()
    elif event.update.message:
        message = event.update.message
        await message.answer(
            'Bot process was restarted due to maintenance.\nRedirecting to main menu.',
            reply_markup=ReplyKeyboardRemove(),
        )
    try:
        await dialog_manager.start(
            BaseMenu.START,
            show_mode=ShowMode.SEND,
        )
    except ValueError:
        await message.answer('Завершите предыдущее действие')


async def on_unknown_state(event, dialog_manager: DialogManager) -> None:
    # Example of handling UnknownState Error and starting new dialog.
    logging.error('Restarting dialog: %s', event.exception)
    await dialog_manager.start(
        BaseMenu.START,
        show_mode=ShowMode.SEND,
    )


async def error_handler(error_event: ErrorEvent) -> None:
    message = error_event.update.message or error_event.update.callback_query.message

    await error_event.update.bot.send_message(
        get_config().DEVELOPER_ID,
        f'User_id: {message.from_user.id}\n'
        f'Username: <a href="tg://user?id={message.from_user.id}">{message.from_user.username}\n</a>'
        f'Message: {message.text} \n\\Error:\n{error_event.exception!r}',
        disable_notification=True,
        parse_mode=ParseMode.HTML,
    )
    logger.error('Failed', exc_info=error_event.exception)
    await message.answer(
        'Ой, случилось что-то непредвиденное, пока разработчик чинит ошибку, '
        f'вы всегда можете написать нам 🙂 {RU.kameya_tg_contact} '
        'или напрямую нашему разработчику через команду /report'
    )


async def get_base_menu_image(
    dialog_manager: DialogManager, repository: UsersRepository, **kwargs
) -> MediaAttachment | None:
    redis_repository: RedisRepository = dialog_manager.middleware_data['redis_repository']
    base_menu_image = await redis_repository.hgetall('menu_image')
    try:
        file_id, content_type = next(iter(base_menu_image.items()))
    except StopIteration:
        return None
    if base_menu_image:
        base_menu_image = MediaAttachment(
            file_id=MediaId(file_id),
            type=ContentType(content_type),
        )
    return base_menu_image


async def get_base_menu_data(
    dialog_manager: DialogManager, repository: UsersRepository, **kwargs
) -> dict[str, Any]:
    update_reg = dialog_manager.start_data == 'update_reg'
    event = dialog_manager.event
    if isinstance(event, ErrorEvent):
        if event.update.message:
            user_id = event.update.message.from_user.id
        elif event.update.callback_query:
            user_id = event.update.callback_query.from_user.id
    else:
        user_id = dialog_manager.event.from_user.id
    user = await repository.user.get_user(user_id, update_reg)
    is_admin = user.id in get_config().admins if user else False

    return {
        'user': user,
        'is_admin': is_admin,
        FILE_ID: await get_base_menu_image(dialog_manager, repository),
    }


async def message_is_sended(dialog_manager: DialogManager, user_id: int) -> bool:
    redis_repository: RedisRepository = dialog_manager.middleware_data['redis_repository']
    admin_mess_ids = await redis_repository.get(AdminKey(key=user_id), dict)
    if admin_mess_ids is None:
        return True
    return admin_mess_ids.get(_SENDED, False)


async def close_app_form_for_other_admins(
    dialog_manager: DialogManager, user_id: int, responding_admin_id: int
) -> None:
    redis_repository: RedisRepository = dialog_manager.middleware_data['redis_repository']
    admin_mess_ids = await redis_repository.get(AdminKey(key=user_id), dict)
    builder = InlineKeyboardBuilder()
    builder.button(text='Ждём пользователя 👻', callback_data='ignore_this_callback')
    if not admin_mess_ids:
        return None
    for admin_id in get_config().admins:
        if responding_admin_id == admin_id:
            continue
        try:
            await dialog_manager.event.bot.edit_message_reply_markup(
                chat_id=admin_id,
                message_id=admin_mess_ids[str(admin_id)],
                reply_markup=builder.as_markup(),
                request_timeout=1,
            )
        except Exception as exc:
            logger.error('Failed while edit admin message', exc_info=exc)
    admin_mess_ids[_SENDED] = True
    await redis_repository.set(AdminKey(key=user_id), admin_mess_ids, ex=_MONTH)


async def approve_form_for_other_admins(
    dialog_manager: DialogManager,
    user_id: int,
    responding_admin_id: int,
    message_text: str,
) -> None:
    redis_repository: RedisRepository = dialog_manager.middleware_data['redis_repository']
    admin_mess_ids = await redis_repository.getdel(AdminKey(key=user_id), dict)
    if not admin_mess_ids:
        return None
    builder = InlineKeyboardBuilder()
    builder.button(text=message_text, callback_data='ignore_this_callback')
    for admin_id in get_config().admins:
        if responding_admin_id == admin_id:
            continue
        try:
            await dialog_manager.event.bot.edit_message_reply_markup(
                chat_id=admin_id,
                message_id=admin_mess_ids[str(admin_id)],
                reply_markup=builder.as_markup(),
                request_timeout=1,
            )
        except Exception as exc:
            logger.error('Failed while edit admin message', exc_info=exc)


def safe_text_with_link(message: Message) -> str:
    original_text = message.text or message.caption
    entities = message.entities or []

    parts = []
    last_pos = 0

    for entity in entities:
        if entity.type == 'url':
            # Экранируем текст до ссылки
            parts.append(escape(original_text[last_pos : entity.offset]))
            # Берем URL без изменений
            url = original_text[entity.offset : entity.offset + entity.length]
            # Экранируем текст ссылки и создаем HTML-тег
            link = escape(original_text[entity.offset : entity.offset + entity.length])
            parts.append(f'<a href="{url}">{link}</a>')
            last_pos = entity.offset + entity.length

    # Добавляем остаток текста
    parts.append(escape(original_text[last_pos:]))

    return ''.join(parts)


async def get_activity_page(dialog_manager: DialogManager, **_kwargs) -> dict[str, Any]:
    scroll: ManagedScroll | None = dialog_manager.find('scroll')
    media_number = await scroll.get_page() if scroll else 0
    activities = dialog_manager.dialog_data.get('activities', [])
    len_activities = len(activities)
    if not activities:
        return {FILE_ID: None, 'activity': None, 'media_number': 0, 'len_activities': 0}
    activity = activities[media_number]
    dialog_manager.dialog_data['activity'] = activity
    image = None
    if activity[FILE_ID]:
        image = MediaAttachment(
            file_id=MediaId(activity[FILE_ID]),
            type=ContentType(activity[CONTENT_TYPE]),
        )
    return {
        'media_number': media_number,
        'next_p': (len_activities - media_number) > 1,
        'len_activities': len_activities,
        'activity': activity,
        FILE_ID: image,
    }


async def validate_sign_ups(dialog_manager: DialogManager, **_kwargs) -> dict[str, Any]:
    activities = dialog_manager.dialog_data.get('activities', [])
    not_valid = []
    for i in range(len(activities)):
        if activities[i]['description'] > 1024:
            not_valid.append(i)
            continue
    not_valid.sort(reverse=True)
    for index in not_valid:
        del activities[index]


def validate_activities_inplace(activities: list[Any]) -> None:
    not_valid = []
    for i in range(len(activities)):
        if len(activities[i]['description']) > 1024:
            not_valid.append(i)
            continue
    not_valid.sort(reverse=True)
    for index in not_valid:
        del activities[index]


async def store_activities_by_type(start_data: Any, manager: DialogManager) -> dict[str]:
    act_type: ActivityType | None = None
    if start_data:
        if isinstance(start_data, dict):
            la: LessonActivity | None = start_data.get('lesson_activity')
            if la:
                act_type = la.activity_type
        if not act_type:
            act_type = start_data['act_type']

    activity_repository: ActivityAbstractRepository = manager.middleware_data[
        'activity_repository'
    ]

    manager.dialog_data['act_type'] = act_type.human_name
    return await activity_repository.get_all_activity_by_type(act_type.human_name)


def format_date_russian(dt: date) -> str:
    weekdays = [
        'Понедельник',
        'Вторник',
        'Среда',
        'Четверг',
        'Пятница',
        'Суббота',
        'Воскресенье',
    ]
    months = [
        'Января',
        'Февраля',
        'Марта',
        'Апреля',
        'Мая',
        'Июня',
        'Июля',
        'Фвгуста',
        'Сентября',
        'Октября',
        'Ноября',
        'Декабря',
    ]
    return f'{weekdays[dt.weekday()]}, {dt.day} {months[dt.month - 1]} {dt.year}'
