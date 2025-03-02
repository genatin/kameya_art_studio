import dataclasses
import json
import logging
from typing import Any

from aiogram import Bot
from aiogram.types import ErrorEvent
from aiogram_dialog import DialogManager
from pydantic import BaseModel

from src.application.domen.models import LessonActivity
from src.application.models import UserDTO
from src.config import get_config
from src.infrastracture import users_repository

logger = logging.getLogger(__name__)


async def error_handler(error_event: ErrorEvent):
    message_from_user = error_event.update.message.from_user
    await error_event.update.bot.send_message(
        get_config().ADMIN_ID,
        f"User_id: {message_from_user.id}\n",
        f'Username: <a href="tg://user?id={message_from_user.id}">{message_from_user.username}\n</a>'
        f"Message: {error_event.update.message.text} \n\nError:",
        disable_notification=True,
        parse_mode="HTML",
    )
    await error_event.update.message.answer(
        "Ой, случилось что-то непредвиденное, пока разработчик чинит ошибку"
        " вы всегда можете оборвать действие нажав или отправив сообщение /cancel"
    )


async def get_cached_user(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    user = None
    user_pret: UserDTO = users_repository.collector.get_user(
        dialog_manager.event.from_user.id
    )
    if user_pret and user_pret.phone:
        user = user_pret
    dialog_manager.dialog_data["user"] = user
    return {"user": user}


async def notify_admins(bot: Bot, user: UserDTO, lesson_activity: LessonActivity):
    message_to_admin = (
        "<u>Пользователь создал заявку:</u>\n\n"
        f"Имя: <b>{user.name}</b>\n"
        f"Фамилия: <b>{user.last_name}</b>\n"
        f"Телефоне: <b>+{user.phone}</b>\n"
        f"Занятие: {lesson_activity.activity_type.human_name}\n"
        f"Вариант посещения: <b><u>{lesson_activity.lesson_option.human_name}</u></b>"
    )
    for admin in users_repository.collector.get_admins():
        try:
            await bot.send_message(admin.id, message_to_admin, parse_mode="HTML")
        except Exception as e:
            logger.error(repr(e))


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        elif isinstance(o, BaseModel):
            return o.model_dump()
        return super().default(o)
