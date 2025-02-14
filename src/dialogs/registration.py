from typing import Any

from aiogram import F
from aiogram.types import (
    CallbackQuery,
    ContentType,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from aiogram_dialog import Data, Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back, Button, Next, SwitchTo
from aiogram_dialog.widgets.text import Const, Format

from src.database.dto import UserDTO
from src.database.user_collector import user_collector
from src.dialogs.states import BaseMenu, Registration
from src.gspread_handler.gspread_worker import gspread_worker


async def send_contact(cq: CallbackQuery, _, dialog_manager: DialogManager):
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Поделиться контактом", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    message = await cq.message.answer(
        "Вы пока не зарегистрированы, для регистрации потребуется ваш номер телефона",
        reply_markup=markup,
    )
    dialog_manager.dialog_data["message_id"] = message.message_id


async def get_contact(msg: Message, _, dialog_manager: DialogManager):
    phone = "+" + msg.contact.phone_number.replace("+", "")
    new_user = UserDTO(id=msg.from_user.id, phone=phone)
    dialog_manager.dialog_data["user"] = new_user
    user_collector.update_cache({msg.from_user.id: new_user})
    gspread_worker.add_user(new_user)
    await dialog_manager.next()


async def get_name(msg: Message | CallbackQuery, _, dialog_manager: DialogManager):
    if isinstance(msg, Message):
        dialog_manager.dialog_data["user"].name = msg.text
        await dialog_manager.next()
    else:
        dialog_manager.dialog_data["user"].name = msg.from_user.first_name


async def get_lastname(msg: Message, _, dialog_manager: DialogManager):
    if isinstance(msg, Message):
        dialog_manager.dialog_data["user"].last_name = msg.text
    else:
        dialog_manager.dialog_data["user"].last_name = msg.from_user.last_name

    await dialog_manager.next()


async def registration_complete(
    start_data: Data, result: Any, dialog_manager: DialogManager
):
    user = dialog_manager.dialog_data["user"]
    gspread_worker.update_data_user(user)
    user_collector.update_cache(user)
    await dialog_manager.start(state=BaseMenu.END)


registration_dialog = Dialog(
    Window(
        Const("Нажмите кнопку ниже"),
        MessageInput(get_contact, content_types=ContentType.CONTACT),
        state=Registration.GET_CONTACT,
    ),
    Window(
        Format(
            "Вас зовут {event.from_user.first_name}?\n\nЕсли нет, введите Ваше имя ниже"
        ),
        MessageInput(get_name),
        SwitchTo(Const("Да"), id="yes", on_click=get_name, state=Registration.LASTNAME),
        state=Registration.NAME,
    ),
    Window(
        Format("Ваше имя: {dialog_data[user].name}?"),
        Next(Const("Да")),
        Back(Const("Нет")),
        state=Registration.NAME_IS,
    ),
    Window(
        Format(
            "Ваша фамилия {event.from_user.last_name}?\n\nЕсли нет, введите Вашу фамилию ниже",
            when=F["event"].from_user.last_name,
        ),
        Next(
            Const("Да"),
            on_click=get_lastname,
            when=F["event"].from_user.last_name,
        ),
        Const("Введите вашу фамилию", when=~F["event"].from_user.last_name),
        Back(Const("Назад")),
        MessageInput(get_lastname),
        state=Registration.LASTNAME,
    ),
    Window(
        Format("Ваша фамилия: {dialog_data[user].last_name}?"),
        Button(Const("Да"), id="reg_complete", on_click=registration_complete),
        Back(Const("Нет")),
        state=Registration.LASTNAME_IS,
    ),
)
