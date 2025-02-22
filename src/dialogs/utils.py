from typing import Any

from aiogram_dialog import DialogManager

from src.facade.users import users_facade


async def get_cached_user(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    user = None
    if user_pret := users_facade.collector.get_user(dialog_manager.event.from_user.id):
        if user_pret.phone:
            user = user_pret
    return {"user": user}
