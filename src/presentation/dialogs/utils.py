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
from aiogram_dialog.api.entities.events import ChatEvent

from src.application.domen.models import LessonActivity
from src.application.domen.text import ru
from src.application.models import UserDTO
from src.config import get_config
from src.infrastracture.adapters.repositories.repo import GspreadRepository
from src.presentation.dialogs.states import BaseMenu

logger = logging.getLogger(__name__)


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
        f"Message: {message.text} \n\nError:\n{traceback.format_exc()}",
        disable_notification=True,
        parse_mode=ParseMode.HTML,
    )
    logger.error(f"Failed", exc_info=error_event.exception)
    await message.answer(
        "Ой, случилось что-то непредвиденное, пока разработчик чинит ошибку"
        " вы всегда можете оборвать действие нажав или отправив сообщение /start"
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
    event: ChatEvent, user: UserDTO, lesson_activity: LessonActivity, num_row: int
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

    for admin_id in get_config().ADMINS:
        try:
            await event.bot.send_message(
                admin_id,
                message_to_admin,
                parse_mode="HTML",
                reply_markup=builder.as_markup(),
            )
        except Exception as e:
            logger.error(repr(e))


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
                f"<a href='{url}'>{escape(original_text[entity.offset:entity.offset+entity.length])}</a>"
            )
            last_pos = entity.offset + entity.length

    # Добавляем остаток текста
    parts.append(escape(original_text[last_pos:]))

    return "".join(parts)
