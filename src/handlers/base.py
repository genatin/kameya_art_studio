from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.formatting import Bold, Text

command_start = Command("start")

router = Router()


@router.message(command_start)
async def cmd_hello(message: Message):
    content = Text("Приветствуем Вас, ", Bold(message.from_user.full_name))
    await message.answer(**content.as_kwargs())


# @router.message(F.text)
# async def message_handler_text(message: Message):
#     content = Text(
#         Bold("Список команд:"),
#         "\n\n/start",)

#     await message.answer(**content.as_kwargs())
