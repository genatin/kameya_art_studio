from typing import Any

from aiogram_dialog import Dialog, DialogManager

from src.cache.user_collector import user_collector


async def get_cached_user(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    if dialog_manager.start_data and (user := dialog_manager.start_data.get("user")):
        return {"user": user}
    return {"user": user_collector.get_user(dialog_manager.event.from_user.id)}
