import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.filters import CommandObject
from aiogram.types import ContentType, TelegramObject
from aiogram.utils.deep_linking import decode_payload
from aiogram_dialog import DialogManager

from src.infrastracture.adapters.repositories.repo import UsersRepository
from src.infrastracture.database.redis.repository import RedisRepository
from src.presentation.dialogs.registration import start_reg
from src.presentation.dialogs.states import FirstSeen

logger = logging.getLogger(__name__)


class RegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Проверяем, зарегистрирован ли пользователь
        dialog_manager: DialogManager = data['dialog_manager']
        repository: UsersRepository = data['repository']
        user_id = event.from_user.id
        user = await repository.user.get_user(user_id)
        if not user or user.reg_is_complete():
            start_data = None
            command: CommandObject = data.get('command')
            if command and command.args is not None:
                payload = decode_payload(command.args)
                start_data = {'jump_to_page': payload}
            if not user:
                await event.answer('🌠 Звёзды ждут, чтобы их нарисовали… ')
                await dialog_manager.event.bot.send_chat_action(user_id, 'typing')
                await asyncio.sleep(1.5)
                if start_data:
                    redis_repository: RedisRepository = data['redis_repository']
                    base_menu_image = await redis_repository.hgetall('menu_image')
                    try:
                        file_id, content_type = next(iter(base_menu_image.items()))
                    except StopIteration:
                        file_id = None
                    welcome_message = (
                        '🎨✨ Приветствуем в творческом пространстве'
                        '\nРады видеть вас в нашей арт-студии Камея! '
                        '\nЗдесь вы найдете мастер-классы, '
                        'уроки и вдохновение для любого уровня.'
                    )
                    if file_id is not None and content_type == ContentType.PHOTO.value:
                        await dialog_manager.event.bot.send_photo(
                            user_id,
                            file_id,
                            caption=welcome_message,
                        )
                    else:
                        await event.answer(welcome_message)
                    await dialog_manager.event.bot.send_chat_action(user_id, 'typing')
                    await asyncio.sleep(3)
                    await event.answer(
                        'Чтобы занятие было удобно смотреть прямо здесь, а нам — '
                        'знать, кого приветствовать, давайте быстренько познакомимся.'
                        '\nЭто займёт полминуты!'
                    )
                    await dialog_manager.event.bot.send_chat_action(user_id, 'typing')
                    await asyncio.sleep(3)
                    return await start_reg(event, None, dialog_manager, start_data)
                return await dialog_manager.start(FirstSeen.START, data=start_data)
            await event.answer('Ой, кажется регистрация не была завершена')
            await repository.user.remove_user(user_id)
            return await dialog_manager.start(FirstSeen.START, data=start_data)
        return await handler(event, data)
