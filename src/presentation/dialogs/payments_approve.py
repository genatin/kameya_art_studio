import asyncio
import logging

from aiogram.enums.parse_mode import ParseMode
from aiogram.types import CallbackQuery, ContentType, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities import ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const

from src.infrastracture.database.redis.keys import AdminKey
from src.infrastracture.database.redis.repository import RedisRepository
from src.presentation.callbacks import PaymentCallback, PaymentScreenCallback
from src.presentation.dialogs.states import PaymentsApprove

logger = logging.getLogger(__name__)


async def send_user_payment(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    builder = InlineKeyboardBuilder()
    admin_id = str(manager.start_data['admin_id'])

    builder.button(
        text='Прикрепить',
        callback_data=PaymentScreenCallback(
            message_id=manager.start_data['message_id'], admin_id=admin_id
        ),
    )
    await callback.message.answer(
        'Здесь можно прикрепить чек об оплате',
        parse_mode=ParseMode.HTML,
        reply_markup=builder.as_markup(),
    )
    await manager.done()
    await manager.reset_stack()
    await asyncio.sleep(0.2)


async def photo_handler(
    message: Message,
    message_input: MessageInput,
    dialog_manager: DialogManager,
) -> None:
    file_id = None
    if message.photo:
        file_id = message.photo[0].file_id
        content_type = ContentType.PHOTO
        caption_from_user = message.caption or ''
    if message.document:
        file_id = message.document.file_id
        content_type = ContentType.DOCUMENT
        caption_from_user = message.caption or ''
    if not file_id:
        await message.answer(
            'Нужно приложить картинку или документ или нажмите кнопку ниже'
        )
        return
    admin_id = str(dialog_manager.start_data['admin_id'])
    redis_repository: RedisRepository = dialog_manager.middleware_data['redis_repository']
    reply_to_mess = await redis_repository.get(AdminKey(key=admin_id), dict)
    caption = 'Поступил чек об оплате'
    if caption_from_user:
        caption += (
            '\n\n<b>Сообщение пользователя:</b>\n'
            + '<blockquote>'
            + caption_from_user
            + '</blockquote>'
        )
    if content_type is ContentType.PHOTO:
        await dialog_manager.event.bot.send_photo(
            admin_id,
            file_id,
            caption=caption,
            parse_mode=ParseMode.HTML,
            disable_notification=False,
            reply_to_message_id=reply_to_mess[admin_id],
        )
    if content_type is ContentType.DOCUMENT:
        await dialog_manager.event.bot.send_document(
            admin_id,
            file_id,
            caption=caption,
            parse_mode=ParseMode.HTML,
            disable_notification=False,
            reply_to_message_id=reply_to_mess[admin_id],
        )
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Отменить запись',
        callback_data=PaymentCallback(
            action='no', message_id=dialog_manager.start_data['message_id']
        ),
    )
    builder.button(
        text='Да',
        callback_data=PaymentCallback(
            action='yes', message_id=dialog_manager.start_data['message_id']
        ),
    )
    await message.answer('Чек об оплате отправлен, благодарим!')
    await dialog_manager.done()


payments_approve_dialog = Dialog(
    Window(
        Const('Прикрепите документ или фото и отправьте'),
        MessageInput(photo_handler),
        Button(Const('Назад'), id='back_or_menu', on_click=send_user_payment),
        state=PaymentsApprove.START,
    ),
)
