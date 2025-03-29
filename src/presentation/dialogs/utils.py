import logging
import traceback
from html import escape
from typing import Any

from aiogram.enums.parse_mode import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.callback_data import CallbackData
from aiogram.types import ErrorEvent, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog import DialogManager, ShowMode, StartMode

from src.application.domen.models import LessonActivity
from src.application.domen.text import ru
from src.application.models import UserDTO
from src.config import get_config
from src.infrastracture.adapters.repositories.repo import GspreadRepository
from src.infrastracture.database.redis.keys import AdminKey
from src.infrastracture.database.redis.repository import RedisRepository
from src.presentation.dialogs.states import BaseMenu

logger = logging.getLogger(__name__)
_DAYS_2 = 60 * 60 * 24 * 7


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
        mode=StartMode.NEW_STACK,
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
        f"Телефоне: <b>{user.phone}</b>\n"
        f"Количество билетов: {lesson_activity.num_tickets or 1}\n"
        f"Занятие: {lesson_activity.activity_type.human_name}\n"
        f"Тема: {lesson_activity.topic}\n"
        f"Вариант посещения: <b><u>{lesson_activity.lesson_option.human_name}</u></b>"
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
            await dialog_manager.event.bot.edit_message_text(
                "Другой администратор уже ответил на заявку",
                chat_id=admin_id,
                message_id=admin_mess_ids[str(admin_id)],
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
