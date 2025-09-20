import logging
import re
from typing import Any

from aiogram.enums.parse_mode import ParseMode
from aiogram.types import CallbackQuery, ContentType, Message, ReplyKeyboardRemove
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities.modes import ShowMode
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Row, SwitchTo
from aiogram_dialog.widgets.text import Const, Format, Jinja

from src.application.domen.text import RU
from src.application.models import UserDTO
from src.infrastracture.adapters.repositories.repo import UsersRepository
from src.presentation.dialogs.states import Registration
from src.presentation.keyboards.keyboard import keyboard_phone
from src.presentation.notifier import Notifier

_FINISHED = 'finished'
_REPOSITORY = 'repository'

logger = logging.getLogger(__name__)


def normalize_phone_number(phone: str) -> str:
    pattern = r'^(\+7|8)(\d{10})$'
    match = re.match(pattern, phone)
    if match:
        prefix, number = match.groups()
        if prefix == '8':
            return f'+7{number}'
        else:
            return f'+7{number}'
    raise ValueError


async def send_contact(cq: CallbackQuery, _, manager: DialogManager) -> None:
    manager.dialog_data[_FINISHED] = False
    await cq.message.answer(
        'Для регистрации потребуется ваш номер телефона',
        reply_markup=keyboard_phone,
    )


async def get_contact(msg: Message, _, manager: DialogManager) -> None:
    try:
        if msg.contact:
            phone = normalize_phone_number('+' + msg.contact.phone_number.lstrip('+'))
        else:
            phone = normalize_phone_number(msg.text)
    except ValueError:
        await msg.answer('✅ Номер должен состоять из 11 цифр и начинаться с +7 или 8')
        return None

    await msg.answer('Спасибо!', reply_markup=ReplyKeyboardRemove())

    username = '@' + str(msg.from_user.username) if msg.from_user.username else None
    new_user = UserDTO(id=msg.from_user.id, nickname=username, phone=phone)
    manager.dialog_data['user'] = new_user
    manager.current_context().widget_data['phone'] = phone
    repository: UsersRepository = manager.middleware_data[_REPOSITORY]
    await repository.user.update_user(new_user)
    await manager.switch_to(Registration.NAME)


async def result_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    dialog_manager.dialog_data[_FINISHED] = True
    user_dict: dict = dialog_manager.dialog_data['user']

    user_dict['name'] = dialog_manager.find('name').get_value()
    user_dict['phone'] = '+' + dialog_manager.find('phone').get_value().lstrip('+')
    user_dict['last_name'] = dialog_manager.find('last_name').get_value()
    return user_dict


async def registration_complete(
    callback: CallbackQuery, button: Button, manager: DialogManager, *_
) -> None:
    repository: UsersRepository = manager.middleware_data[_REPOSITORY]
    notifier: Notifier = manager.middleware_data['notifier']

    user = UserDTO(**manager.dialog_data['user'])

    mess_to_remove = await callback.message.answer(RU.random_wait)
    if await repository.user.get_user(user.id):
        await repository.user.update_user(user)
        message = 'Данные были обновлены'
        show_mode = ShowMode.DELETE_AND_SEND
    else:
        is_success = await repository.user.add_user(user)
        if is_success:
            message = (
                'Ура! Регистрация завершена, теперь Вы можете творить вместе с нами!'
            )
            show_mode = ShowMode.DELETE_AND_SEND
            await notifier.registration_notify(manager, user)
        else:
            message = (
                'Что-то пошло не так, попробуйте ещё раз. '
                'Если ошибка повторяется, '
                'то попробуйте через пару часов. '
                'Мы уже разбираемся.'
            )
            show_mode = ShowMode.NO_UPDATE
    await callback.message.answer(message, reply_markup=ReplyKeyboardRemove())
    await mess_to_remove.delete()
    await manager.done(show_mode=show_mode)


async def next_or_end(event, widget, dialog_manager: DialogManager, *_) -> None:
    if dialog_manager.dialog_data.get(_FINISHED):
        await dialog_manager.switch_to(Registration.END)
    else:
        await dialog_manager.next()


async def on_error_name(
    message: Message, dialog_: Any, manager: DialogManager, error_: ValueError
) -> None:
    str_error = str(error_)
    error_to_send = 'Ой-ой! Что-то пошло не так!\n\n'
    match str_error:
        case 'pattern':
            detail = (
                '✅ Допустимы только русские буквы '
                '\n(латиница, цифры, пробелы и символы — не прокатят)\n\n'
            )
        case 'len':
            detail = '✅ Допустимая длина от 2 до 50 символов (не Гэндальф и не Йо)\n\n'
        case 'same':
            detail = '✅ Нельзя 4 одинаковые буквы подряд (это не имя, а заклинание!)\n'
    await message.answer(f'<i>{error_to_send}{detail}</i>', parse_mode=ParseMode.HTML)


async def on_error_phone(
    message: Message, dialog_: Any, manager: DialogManager, error_: ValueError
) -> None:
    error_to_send = 'Ой-ой! Что-то пошло не так!\n\n'
    detail = '✅ Номер должен состоять из 11 цифр и начинаться с +7 или 8\n'
    await message.answer(f'<i>{error_to_send}{detail}</i>', parse_mode=ParseMode.HTML)


def validate_name_factory(name: str) -> bool:
    name = name.strip()
    valid_pattern = re.compile(r'^[а-яё]+$', re.I)
    if not 2 <= len(name) <= 50:
        raise ValueError('len')
    if not re.fullmatch(valid_pattern, name):
        raise ValueError('pattern')
    if re.search(r'(.)\1{3,}', name):
        raise ValueError('same')
    return name


registration_dialog = Dialog(
    Window(
        Const('Нажмите кнопку ниже ⬇️ или введите номер вручную'),
        MessageInput(get_contact, content_types=(ContentType.CONTACT, ContentType.TEXT)),
        state=Registration.GET_CONTACT,
    ),
    Window(
        Const('*Введите номер телефона*\n_Например: +78005553535_'),
        TextInput(
            id='phone',
            on_success=next_or_end,
            type_factory=normalize_phone_number,
            on_error=on_error_phone,
        ),
        SwitchTo(Const(RU.back_step), id='reg_end', state=Registration.END),
        state=Registration.EDIT_CONTACT,
        parse_mode=ParseMode.MARKDOWN,
    ),
    Window(
        Format('*Введите Ваше полное имя*\n_Например: Илья_'),
        TextInput(
            id='name',
            on_success=next_or_end,
            type_factory=validate_name_factory,
            on_error=on_error_name,
        ),
        state=Registration.NAME,
        parse_mode=ParseMode.MARKDOWN,
    ),
    Window(
        Const('*Введите Вашу фамилию*\n_Например: Репин_'),
        TextInput(
            id='last_name',
            on_success=next_or_end,
            type_factory=validate_name_factory,
            on_error=on_error_name,
        ),
        state=Registration.LASTNAME,
        parse_mode=ParseMode.MARKDOWN,
    ),
    Window(
        Jinja(
            '<b>Телефон</b>: {{phone}}\n'
            '<b>Имя</b>: {{name}}\n'
            '<b>Фамилия</b>: {{last_name}}\n\n'
            'Убедитесь, что данные введены корректно, '
            'с помощью кнопок ниже можно изменить данные.\n\n'
            'Если всё правильно, нажмите <i>Дальше</i>'
        ),
        Row(
            SwitchTo(
                Const('Изменить имя'),
                state=Registration.NAME,
                id='to_name',
            ),
            SwitchTo(
                Const('Изменить фамилию'),
                state=Registration.LASTNAME,
                id='to_lastname',
            ),
        ),
        SwitchTo(
            Const('Изменить телефон'),
            state=Registration.EDIT_CONTACT,
            id='to_phone',
        ),
        Button(Const('Дальше ➡️'), id='good', on_click=registration_complete),
        parse_mode=ParseMode.HTML,
        getter=result_getter,
        state=Registration.END,
    ),
)
