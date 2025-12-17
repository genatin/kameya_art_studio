import asyncio
from typing import Any

from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode
from aiogram_dialog import DialogManager


async def send_messages_to_user(
    bot: Bot,
    messages: list[str],
    user_id: Any,
    parse_mode: ParseMode = ParseMode.HTML,
) -> None:
    for m in messages:
        await bot.send_message(
            chat_id=user_id,
            text=m,
            parse_mode=parse_mode,
        )
        await bot.send_chat_action(user_id, "typing")
        await asyncio.sleep(2)
