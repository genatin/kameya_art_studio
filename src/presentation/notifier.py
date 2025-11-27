import logging
from uuid import uuid4

from aiogram.enums.parse_mode import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog import DialogManager

from src.application.domen.models import LessonActivity
from src.application.domen.text import RU
from src.application.models import UserDTO
from src.config import get_config
from src.infrastracture.database.redis.keys import AdminKey
from src.infrastracture.database.redis.repository import RedisRepository
from src.presentation.callbacks import SignUpCallback
from src.presentation.dialogs.models import SignUpCallbackFactory

logger = logging.getLogger(__name__)

_MINUTE = 60
_HOUR = _MINUTE * 60
_DAY = _HOUR * 24
_MONTH = _DAY * 30


class Notifier:
    async def admin_notify(self, manager: DialogManager, message_str: str) -> None:
        for admin_id in get_config().admins:
            try:
                await manager.event.bot.send_message(
                    admin_id,
                    message_str,
                    parse_mode=ParseMode.HTML,
                    disable_notification=False,
                )
            except Exception as exc:
                logger.error('Failed while notify admins', exc_info=exc)

    async def sign_up_notify(
        self,
        user: UserDTO,
        lesson_activity: LessonActivity,
        num_row: int,
        manager: DialogManager,
    ) -> None:
        message_to_admin = (
            '<u>Пользователь создал заявку:</u>\n\n'
            f'Имя: <b>{user.name}</b>\n'
            f'Фамилия: <b>{user.last_name}</b>\n'
            f'Телефон: <b>{user.phone}</b>\n'
            f'Количество билетов: {lesson_activity.num_tickets or 1}\n'
            f'Занятие: {lesson_activity.activity_type.human_name}\n'
            f'Тема: {lesson_activity.topic}\n'
            '\n'
            f'Дата: {lesson_activity.date}\n'
            f'Время: {lesson_activity.time}\n'
            f'<b><u>{lesson_activity.lesson_option.human_name}</u></b>'
            f'\n\n<a href="https://t.me/{user.phone}">Связаться с пользователем</a>'
        )
        builder = InlineKeyboardBuilder()
        message_id = str(uuid4())

        builder.button(
            text='Отменить заявку',
            callback_data=SignUpCallback(message_id=message_id, action='reject'),
        )
        builder.button(
            text=RU.send_bank_details,
            callback_data=SignUpCallback(message_id=message_id, action='sign_up'),
        )

        redis_repository: RedisRepository = manager.middleware_data['redis_repository']
        send_mes_ids = {'sended': False}
        for admin_id in get_config().admins:
            try:
                mess = await manager.event.bot.send_message(
                    admin_id,
                    message_to_admin,
                    parse_mode=ParseMode.HTML,
                    reply_markup=builder.as_markup(),
                )
                send_mes_ids[admin_id] = mess.message_id
            except Exception as exc:
                logger.error('Failed while notify admins', exc_info=exc)
        # при ответе одним из администраторов у других уведомление (сообщение)
        # о заявке редактируется (удаляется кнопка). актуально 14 дней
        await redis_repository.set(AdminKey(key=user.id), send_mes_ids, ex=_MONTH)

        # admin message id
        signup_data = SignUpCallbackFactory(
            message_id=message_id,
            user_id=user.id,
            user_phone=user.phone,
            activity_type=lesson_activity.activity_type.name,
            num_row=num_row,
            message=message_to_admin,
        )
        await redis_repository.hset(
            message_id, mapping=signup_data.model_dump(), ex=_MONTH
        )
