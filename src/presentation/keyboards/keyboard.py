from aiogram import types

from src.application.domen.text import ru

button_phone = types.KeyboardButton(text=ru.send_phone, request_contact=True)
keyboard_phone = types.ReplyKeyboardMarkup(
    keyboard=[[button_phone]], row_width=1, one_time_keyboard=True, resize_keyboard=True
)


signup_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[[types.KeyboardButton(text=ru.sign_up)]],
    resize_keyboard=True,
)


add_or_remove_mc = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text=ru.admin_create)],
        [types.KeyboardButton(text=ru.admin_remove)],
    ],
    resize_keyboard=True,
)
