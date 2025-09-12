from aiogram.enums.parse_mode import ParseMode
from aiogram.types import Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Cancel
from aiogram_dialog.widgets.text import Const, Format

from src.config import get_config
from src.presentation.dialogs.states import BaseMenu, Developer

_DEV_REPORT = 'dev_report'


async def send_to_developer(
    event: Message, widget, dialog_manager: DialogManager, *_
) -> None:
    report = d.get_value() if (d := dialog_manager.find(_DEV_REPORT)) else ''
    await dialog_manager.event.bot.send_message(
        chat_id=get_config().DEVELOPER_ID,
        text='Сообщение об ошибке/пожелание от пользователя: \n\n'
        + '<i>'
        + report
        + '</i>',
        parse_mode=ParseMode.HTML,
    )
    await event.answer('Сообщение отправлено. Благодарим Вас!')
    await dialog_manager.start(BaseMenu.START)


developer_dialog = Dialog(
    Window(
        Format(
            'Мы очень хотим, чтобы Вам было удобно пользоваться нашим ботом, '
            'поэтому здесь можно оставить свои пожелания или сообщить об ошибках. '
            'Чем подробнее получится описать ошибку, тем быстрее мы её исправим. '
            '\n\n<i>Опишите проблему и отправьте обычным сообщением прямо тут</i>'
        ),
        TextInput(id=_DEV_REPORT, on_success=send_to_developer),
        Cancel(Const('Назад')),
        state=Developer.START,
        parse_mode=ParseMode.HTML,
    ),
)
