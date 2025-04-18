import logging
import traceback
from html import escape
from typing import Any

from aiogram.enums.parse_mode import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.callback_data import CallbackData
from aiogram.types import ContentType, ErrorEvent, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog import DialogManager, ShowMode, StartMode
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.common import ManagedScroll

from src.application.domen.models import LessonActivity
from src.application.domen.models.activity_type import ActivityType
from src.application.domen.text import ru
from src.application.models import UserDTO
from src.config import get_config
from src.infrastracture.adapters.interfaces.repositories import (
    ActivityAbstractRepository,
)
from src.infrastracture.adapters.repositories.repo import GspreadRepository
from src.infrastracture.database.redis.keys import AdminKey
from src.infrastracture.database.redis.repository import RedisRepository
from src.presentation.dialogs.states import BaseMenu

logger = logging.getLogger(__name__)

FILE_ID = "file_id"
_MINUTE = 60
_HOUR = _MINUTE * 60
_DAYS_2 = _HOUR * 24 * 7


class SignUpCallbackFactory(CallbackData, prefix="signup"):
    user_id: str
    activity_type: str
    num_row: str


async def on_unknown_intent(event: ErrorEvent, dialog_manager: DialogManager):
    # Example of handling UnknownIntent Error and starting new dialog.
    logging.error("Restarting dialog: %s", event.exception)
    if event.update.callback_query:
        await event.update.callback_query.answer(
            "Bot process was restarted due to maintenance.\n"
            "Redirecting to main menu.",
        )
        if event.update.callback_query.message:
            try:
                await event.update.callback_query.message.delete()
            except TelegramBadRequest:
                pass  # whatever
    elif event.update.message:
        await event.update.message.answer(
            "Bot process was restarted due to maintenance.\n"
            "Redirecting to main menu.",
            reply_markup=ReplyKeyboardRemove(),
        )
    await dialog_manager.start(
        BaseMenu.START,
        show_mode=ShowMode.SEND,
    )


async def on_unknown_state(event, dialog_manager: DialogManager):
    # Example of handling UnknownState Error and starting new dialog.
    logging.error("Restarting dialog: %s", event.exception)
    await dialog_manager.start(
        BaseMenu.START,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.SEND,
    )


async def error_handler(error_event: ErrorEvent):
    message = error_event.update.message or error_event.update.callback_query.message

    await error_event.update.bot.send_message(
        get_config().DEVELOPER_ID,
        f"User_id: {message.from_user.id}\n"
        f'Username: <a href="tg://user?id={message.from_user.id}">{message.from_user.username}\n</a>'
        f"Message: {message.text} \n\nError:\n{repr(error_event.exception)}",
        disable_notification=True,
        parse_mode=ParseMode.HTML,
    )
    logger.error("Failed", exc_info=error_event.exception)
    await message.answer(
        "Ой, случилось что-то непредвиденное, пока разработчик чинит ошибку"
        " вы всегда можете начать сначала, отправив сообщение /start"
    )


async def get_user(
    dialog_manager: DialogManager, repository: GspreadRepository, **kwargs
) -> dict[str, Any]:
    after_reg = dialog_manager.start_data == "after_reg"
    user = await repository.user.get_user(dialog_manager.event.from_user.id, after_reg)
    if user and not user.phone:
        user = None
    is_admin = user.id in get_config().ADMINS if user else False
    return {"user": user, "is_admin": is_admin}


async def notify_admins(
    manager: DialogManager, user: UserDTO, lesson_activity: LessonActivity, num_row: int
):
    message_to_admin = (
        "<u>Пользователь создал заявку:</u>\n\n"
        f"Имя: <b>{user.name}</b>\n"
        f"Фамилия: <b>{user.last_name}</b>\n"
        f"Телефон: <b>{user.phone}</b>\n"
        f"Количество билетов: {lesson_activity.num_tickets or 1}\n"
        f"Занятие: {lesson_activity.activity_type.human_name}\n"
        f"Тема: {lesson_activity.topic}\n"
        f"Вариант посещения: <b><u>{lesson_activity.lesson_option.human_name}</u></b>"
        f'\n\n<a href="https://t.me/{user.phone}">Связаться с пользователем</a>'
    )
    builder = InlineKeyboardBuilder()
    builder.button(
        text=ru.reply_to_user_form,
        callback_data=SignUpCallbackFactory(
            user_id=str(user.id),
            activity_type=lesson_activity.activity_type.name,
            num_row=num_row,
        ),
    )
    redis_repository: RedisRepository = manager.middleware_data["redis_repository"]
    send_mes_ids = {}
    for admin_id in get_config().ADMINS:
        try:
            mess = await manager.event.bot.send_message(
                admin_id,
                message_to_admin,
                parse_mode=ParseMode.HTML,
                reply_markup=builder.as_markup(),
            )
            send_mes_ids[admin_id] = mess.message_id
        except Exception as exc:
            logger.error("Failed while notify admins", exc_info=exc)
    # при ответе одним из администраторов у других уведомление (сообщение)
    # о заявке редактируется (удаляется кнопка). актуально 2 дня
    await redis_repository.set(AdminKey(key=user.id), send_mes_ids, ex=_DAYS_2)


async def close_app_form_for_other_admins(
    dialog_manager: DialogManager, user_id: int, responding_admin_id: int
):
    redis_repository: RedisRepository = dialog_manager.middleware_data[
        "redis_repository"
    ]
    admin_mess_ids = await redis_repository.getdel(AdminKey(key=user_id), dict)
    for admin_id in get_config().ADMINS:
        if responding_admin_id == admin_id:
            continue
        try:
            await dialog_manager.event.bot.edit_message_reply_markup(
                chat_id=admin_id,
                message_id=admin_mess_ids[str(admin_id)],
                reply_markup=None,
            )
        except Exception as exc:
            logger.error("Failed while edit admin message", exc_info=exc)


def safe_text_with_link(message: Message) -> str:
    original_text = message.text or message.caption
    entities = message.entities or []

    parts = []
    last_pos = 0

    for entity in entities:
        if entity.type == "url":
            # Экранируем текст до ссылки
            parts.append(escape(original_text[last_pos : entity.offset]))
            # Берем URL без изменений
            url = original_text[entity.offset : entity.offset + entity.length]
            # Экранируем текст ссылки и создаем HTML-тег
            parts.append(
                f"<a href='{url}'>{escape(original_text[entity.offset:entity.offset + entity.length])}</a>"
            )
            last_pos = entity.offset + entity.length

    # Добавляем остаток текста
    parts.append(escape(original_text[last_pos:]))

    return "".join(parts)


async def get_activity_page(dialog_manager: DialogManager, **_kwargs):
    scroll: ManagedScroll | None = dialog_manager.find("scroll")
    media_number = await scroll.get_page() if scroll else 0
    activities = dialog_manager.dialog_data.get("activities", [])
    len_activities = len(activities)
    if not activities:
        return {FILE_ID: None, "activity": None, "media_number": 0, "len_activities": 0}
    activity = activities[media_number]
    dialog_manager.dialog_data["activity"] = activity
    image = None
    if activity[FILE_ID]:
        image = MediaAttachment(
            file_id=MediaId(activity[FILE_ID]),
            type=ContentType.PHOTO,
        )
    return {
        "media_number": media_number,
        "next_p": (len_activities - media_number) > 1,
        "len_activities": len_activities,
        "activity": activity,
        FILE_ID: image,
    }


async def store_activities_by_type(start_data: Any, manager: DialogManager):
    # function passed getter on start dialog
    # you can pass ActivityType
    act_type: ActivityType | None = None
    if start_data:
        if isinstance(start_data, dict):
            la: LessonActivity | None = start_data.get("lesson_activity")
            if la:
                act_type = la.activity_type
        if not act_type:
            act_type = start_data["act_type"]

    activity_repository: ActivityAbstractRepository = manager.middleware_data[
        "activity_repository"
    ]

    manager.dialog_data["act_type"] = act_type.human_name
    manager.dialog_data["activities"] = (
        await activity_repository.get_all_activity_by_type(act_type.human_name)
    )
