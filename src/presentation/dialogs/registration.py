import logging

from aiogram.enums.parse_mode import ParseMode
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
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Row, SwitchTo
from aiogram_dialog.widgets.text import Const, Format, Jinja

from src.application.domen.text import ru
from src.application.models import UserDTO
from src.infrastracture.adapters.repositories.repo import GspreadRepository
from src.presentation.dialogs.states import Registration
from src.presentation.keyboards.keyboard import keyboard_phone, keyboard_signup

_FINISHED = "finished"
_REPOSITORY = "repository"

logger = logging.getLogger(__name__)


async def send_contact(cq: CallbackQuery, _, manager: DialogManager):
    manager.dialog_data[_FINISHED] = False
    await cq.message.answer(
        "Ой, Вы ещё не зарегистрированы, для регистрации потребуется ваш номер телефона",
        reply_markup=keyboard_phone,
    )


async def get_contact(msg: Message, _, manager: DialogManager):
    phone = "+" + msg.contact.phone_number.lstrip("+")

    new_user = UserDTO(
        id=msg.from_user.id, nickname="@" + msg.from_user.username, phone=phone
    )
    manager.dialog_data["user"] = new_user
    manager.current_context().widget_data["phone"] = phone
    repository: GspreadRepository = manager.middleware_data[_REPOSITORY]
    await repository.user.add_user(new_user)
    await manager.switch_to(Registration.NAME)


async def result_getter(dialog_manager: DialogManager, **kwargs):
    dialog_manager.dialog_data[_FINISHED] = True
    user_dict: dict = dialog_manager.dialog_data["user"]

    user_dict["name"] = dialog_manager.find("name").get_value()
    user_dict["phone"] = "+" + dialog_manager.find("phone").get_value().lstrip("+")
    user_dict["last_name"] = dialog_manager.find("last_name").get_value()
    return user_dict


async def registration_complete(
    callback: CallbackQuery, button: Button, manager: DialogManager, *_
):
    repository: GspreadRepository = manager.middleware_data[_REPOSITORY]

    user = UserDTO(**manager.dialog_data["user"])

    await callback.message.answer("Ещё совсем чуть-чуть...")
    is_success = await repository.user.update_user(user)
    # TODO сделать отправку админу
    if is_success:
        message = "Ура! Регистрация завершена, теперь Вы можете творить вместе с нами!"
        show_mode = ShowMode.DELETE_AND_SEND

    else:
        message = "Что-то пошло не так, попробуйте ещё раз. Если ошибка повторяется, то попробуйте через пару часов. Мы уже разбираемся."
        show_mode = ShowMode.NO_UPDATE

    await callback.message.answer(message, reply_markup=keyboard_signup)
    await manager.done(show_mode=show_mode)


async def next_or_end(event, widget, dialog_manager: DialogManager, *_):
    if dialog_manager.dialog_data.get(_FINISHED):
        await dialog_manager.switch_to(Registration.END)
    else:
        await dialog_manager.next()


registration_dialog = Dialog(
    Window(
        Const("Нажмите кнопку ниже"),
        MessageInput(get_contact, content_types=ContentType.CONTACT),
        state=Registration.GET_CONTACT,
    ),
    Window(
        Const("*Введите номер телефона*\n_Например: +78005553535_"),
        TextInput(id="phone", on_success=next_or_end),
        SwitchTo(Const(ru.back_step), id="reg_end", state=Registration.END),
        state=Registration.EDIT_CONTACT,
        parse_mode=ParseMode.MARKDOWN,
    ),
    Window(
        Format("*Введите ваше имя*\n_Например: Илья_"),
        TextInput(id="name", on_success=next_or_end),
        state=Registration.NAME,
        parse_mode=ParseMode.MARKDOWN,
    ),
    Window(
        Const("*Введите вашу фамилию*\n_Например: Репин_"),
        TextInput("last_name", on_success=next_or_end),
        state=Registration.LASTNAME,
        parse_mode=ParseMode.MARKDOWN,
    ),
    Window(
        Jinja(
            "<b>Телефон</b>: {{phone}}\n"
            "<b>Имя</b>: {{name}}\n"
            "<b>Фамилия</b>: {{last_name}}\n\n"
            "Убедитесь, что данные введены корректно, с помощью кнопок ниже можно изменить данные.\n\n"
            "Если всё правильно, нажмите <i>Дальше</i>"
        ),
        Row(
            SwitchTo(
                Const("Изменить имя"),
                state=Registration.NAME,
                id="to_name",
            ),
            SwitchTo(
                Const("Изменить фамилию"),
                state=Registration.LASTNAME,
                id="to_lastname",
            ),
        ),
        SwitchTo(
            Const("Изменить телефон"),
            state=Registration.EDIT_CONTACT,
            id="to_phone",
        ),
        Button(Const("Дальше ➡️"), id="good", on_click=registration_complete),
        parse_mode=ParseMode.HTML,
        getter=result_getter,
        state=Registration.END,
    ),
)
