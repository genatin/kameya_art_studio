import pytest
from aiogram import Dispatcher
from aiogram_dialog.test_tools import BotClient


@pytest.mark.asyncio
async def test_click(dp: Dispatcher, client: BotClient, message_manager):
    await client.send("/start")
    first_message = message_manager.one_message()
    assert (
        first_message.text
        == "mock_user, добро пожаловать в нашу творческую мастерскую! 🎨"
    )
