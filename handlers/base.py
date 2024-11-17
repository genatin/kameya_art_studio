from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.formatting import Text, Bold
from aiogram import Router


router = Router()

@router.message(Command("start"))
async def cmd_hello(message: Message):
    content = Text(
        "Приветствуем Вас, ",
        Bold(message.from_user.full_name)
    )
    await message.answer(
        **content.as_kwargs()
    )