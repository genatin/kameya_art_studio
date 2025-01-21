from dataclasses import dataclass
from threading import Thread

from aiogram import Router
from aiogram.filters import Command, Filter
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    ContentType,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities.modes import ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Next, Row
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format

from src.database.dto import UserDTO
from src.database.user_collector import user_collector
from src.gspread_handler.gspread_worker import gspread_worker

router = Router()


class Registration(StatesGroup):
    START = State()
    CONTACT = State()
    NAME = State()
    LASTNAME = State()
    SIGN_UP = State()


@dataclass
class NameMasters:
    nazar_az = "Назар Азаматов"
    kirill_solo = "Кирилл Соловицкий"


class ByMaster(StatesGroup):
    START = State()
    SERVICE_CHOICE = State()


async def button1_clicked(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    """Add data to `dialog_data` and switch to the next window of current dialog"""
    manager.dialog_data.update(manager.start_data)
    manager.dialog_data["master_name"] = callback.data
    await manager.next()


master = Dialog(
    Window(
        Const("🧑🏻‍🎨 Педагог (Мастер)"),
        Button(
            Const(NameMasters.nazar_az),
            id="nazar",
            on_click=button1_clicked,
        ),
        Button(
            Const(NameMasters.kirill_solo),
            id="kirill",
            on_click=button1_clicked,
        ),
        Cancel(text=Const("Назад")),
        state=ByMaster.START,
    ),
    Window(
        Format("User input: {dialog_data}"),
        Back(text=Const("Назад")),
        state=ByMaster.SERVICE_CHOICE,
    ),
)


async def start_by_master(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    if manager.start_data:
        manager.dialog_data.update(manager.start_data)
    await manager.start(ByMaster.START, data=manager.dialog_data)


async def send_contact(cq: CallbackQuery, _, dialog_manager: DialogManager):
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Поделиться контактом", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    message = await cq.message.answer("Нажмите на кнопку ниже:", reply_markup=markup)
    dialog_manager.dialog_data["message_id"] = message.message_id


async def get_contact(msg: Message, _, dialog_manager: DialogManager):
    await msg.bot.delete_messages(
        msg.chat.id, [dialog_manager.dialog_data["message_id"], msg.message_id]
    )
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
        await dialog_manager.next()
    else:
        dialog_manager.dialog_data["user"].last_name = msg.from_user.last_name
    gspread_worker.update_data_user(dialog_manager.dialog_data["user"])


registration = Dialog(
    Window(
        StaticMedia(
            path="src/data/welcome_photo.jpg",
            type=ContentType.PHOTO,
        ),
        Format(
            "{event.from_user.full_name} привет, \n\n--- текст ---\n\nчтобы продолжить понадобится ваш номер телефона"
        ),
        Next(Const("Дальше"), on_click=send_contact, show_mode=ShowMode.SEND),
        state=Registration.START,
    ),
    Window(
        Const("Чтобы продолжить пользоваться ботом, вам нужно подтвердить свой номер."),
        MessageInput(get_contact, content_types=ContentType.CONTACT),
        state=Registration.CONTACT,
    ),
    Window(
        Format(
            "Вас зовут {event.from_user.first_name}?\n\nЕсли нет, введите Ваше имя ниже"
        ),
        MessageInput(get_name),
        Next(Const("Да"), on_click=get_name),
        state=Registration.NAME,
    ),
    Window(
        Format(
            "Ваша фамилия {event.from_user.last_name}?\n\nЕсли нет, введите Вашу фамилию ниже"
        ),
        MessageInput(get_lastname),
        Next(Const("Да"), on_click=get_lastname),
        state=Registration.LASTNAME,
    ),
    Window(
        Const("✍️ Записаться \n"),
        Row(
            Button(
                Const("🧑🏻‍🎨 Педагог (Мастер)"),
                id="bymaster",
                on_click=start_by_master,
            ),
        ),
        state=Registration.SIGN_UP,
    ),
)


@router.message(Command("sign_up"))
async def sign_up_handler(
    message: Message, dialog_manager: DialogManager, user: UserDTO
):
    if user:
        await dialog_manager.start(
            Registration.SIGN_UP, data=user.model_dump(exclude_none=True)
        )
    else:
        await dialog_manager.start(Registration.START)
