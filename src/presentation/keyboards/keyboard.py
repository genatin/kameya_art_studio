from aiogram import types

from src.application.domen.text import RU

button_phone = types.KeyboardButton(text=RU.send_phone, request_contact=True)
keyboard_phone = types.ReplyKeyboardMarkup(
    keyboard=[[button_phone]], row_width=1, one_time_keyboard=True, resize_keyboard=True
)


add_or_remove_mc = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text=RU.admin_create)],
        [types.KeyboardButton(text=RU.admin_remove)],
    ],
    resize_keyboard=True,
)
