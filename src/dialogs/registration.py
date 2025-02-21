from aiogram.types import (
    CallbackQuery,
    ContentType,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities.modes import ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back, Button, Next
from aiogram_dialog.widgets.text import Const, Format

from src.cache.dto import UserDTO
from src.cache.user_collector import user_collector
from src.dialogs.states import Registration, SignUp
from src.gspread_handler.gspread_worker import gspread_worker


async def send_contact(cq: CallbackQuery, _, manager: DialogManager):
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Поделиться контактом", request_contact=True)]],
        one_time_keyboard=True,
    )
    message = await cq.message.answer(
        "Вы пока не зарегистрированы, для регистрации потребуется ваш номер телефона",
        reply_markup=markup,
    )
    manager.dialog_data["message_id"] = message.message_id


async def get_contact(msg: Message, _, manager: DialogManager):
    phone = "+" + msg.contact.phone_number.replace("+", "")
    new_user = UserDTO(
        id=msg.from_user.id, nickname="@" + msg.from_user.username, phone=phone
    )
    manager.dialog_data["user"] = new_user
    gspread_worker.add_user(new_user)
    await manager.next()


async def get_name(msg: Message | CallbackQuery, _, manager: DialogManager):
    manager.dialog_data["user"].name = msg.text
    await manager.next()


async def get_lastname(msg: Message, _, manager: DialogManager):
    manager.dialog_data["user"].last_name = msg.text
    await manager.next()


async def registration_complete(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    user = manager.dialog_data["user"]
    gspread_worker.update_data_user(user)
    user_collector.update_cache(user)
    await callback.message.answer(
        "Ура! Регистрация завершена, теперь Вы можете творить вместе с нами!",
        reply_markup=ReplyKeyboardRemove(),
    )
    await manager.done(show_mode=ShowMode.SEND)


registration_dialog = Dialog(
    Window(
        Const("Нажмите кнопку ниже"),
        MessageInput(get_contact, content_types=ContentType.CONTACT),
        state=Registration.GET_CONTACT,
    ),
    Window(
        Format("Введите Ваше имя кириллицей ниже"),
        MessageInput(get_name),
        state=Registration.NAME,
    ),
    Window(
        Format("Ваше имя: {dialog_data[user].name}?"),
        Next(Const("Да")),
        Back(Const("Нет")),
        state=Registration.NAME_IS,
    ),
    Window(
        Const("Введите вашу фамилию кириллицей ниже"),
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
