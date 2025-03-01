from aiogram import types

from src.presentation.keyboards.text import ru

button_phone = types.KeyboardButton(text=ru.send_phone, request_contact=True)
keyboard_phone = types.ReplyKeyboardMarkup(
    keyboard=[[button_phone]], row_width=1, resize_keyboard=True, one_time_keyboard=True
)
