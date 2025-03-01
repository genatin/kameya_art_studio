import dataclasses
import json
from typing import Any

from aiogram.types import ErrorEvent
from aiogram_dialog import DialogManager
from pydantic import BaseModel

from src.application.models import UserDTO
from src.config import get_config
from src.infrastracture import users_repository


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


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        elif isinstance(o, BaseModel):
            return o.model_dump()
        return super().default(o)
