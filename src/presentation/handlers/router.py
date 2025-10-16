import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import StartMode

from src.application.domen.text import RU
from src.infrastracture.adapters.repositories.repo import UsersRepository
from src.infrastracture.database.redis.repository import RedisRepository
from src.presentation.callbacks import PaymentCallback, SignUpCallback
from src.presentation.dialogs.states import AdminPayments, AdminReply, BaseMenu, SignUp
from src.presentation.middlewares.middleware import RegistrationMiddleware

logger = logging.getLogger(__name__)

main_router = Router()
main_router.message.middleware(RegistrationMiddleware())


@main_router.message(Command('start'))
async def cmd_hello(
    message: Message,
    dialog_manager: DialogManager,
    repository: UsersRepository,
) -> None:
    try:
        await dialog_manager.start(BaseMenu.START)
    except ValueError:
        await message.answer(RU.cancel)


@main_router.message(Command('sign_up'))
@main_router.message(F.text == RU.sign_up)
async def sign_up_handler(
    message: Message,
    dialog_manager: DialogManager,
    repository: UsersRepository,
) -> None:
    try:
        await dialog_manager.start(SignUp.START)
    except ValueError:
        await message.answer(RU.cancel)


@main_router.message(Command('registration'))
async def registration_handler(
    message: Message,
    dialog_manager: DialogManager,
    repository: UsersRepository,
) -> None:
    await repository.user.remove_user(message.from_user.id, only_cache=True)
    try:
        await dialog_manager.start(BaseMenu.START, data='update_reg')
    except ValueError:
        await message.answer(RU.cancel)


@main_router.message(Command('about'))
async def about_handler(
    message: Message,
    dialog_manager: DialogManager,
) -> None:
    try:
        await dialog_manager.start(BaseMenu.ABOUT_US)
    except ValueError:
        await message.answer(RU.cancel)


@main_router.message(Command('how_to'))
async def how_to_handler(message: Message, dialog_manager: DialogManager) -> None:
    try:
        await dialog_manager.start(BaseMenu.HOW_TO)
    except ValueError:
        await message.answer(RU.cancel)


@main_router.callback_query(SignUpCallback.filter())
async def sign_up_callback_handler(
    cq: CallbackQuery,
    callback_data: SignUpCallback,
    dialog_manager: DialogManager,
    redis_repository: RedisRepository,
) -> None:
    user_data = await redis_repository.hgetall(callback_data.message_id)
    user_data['message_id'] = callback_data.message_id
    try:
        if callback_data.action == 'sign_up':
            state = AdminReply.START
        else:
            state = AdminReply.CANCEL
        await dialog_manager.start(state=state, data=user_data, show_mode=ShowMode.SEND)
    except ValueError:
        await cq.message.answer(RU.cancel)


@main_router.callback_query(PaymentCallback.filter())
async def sign_up_payment_handler(
    cq: CallbackQuery,
    callback_data: PaymentCallback,
    dialog_manager: DialogManager,
    redis_repository: RedisRepository,
) -> None:
    user_data = await redis_repository.hgetall(callback_data.message_id)
    user_data['message_id'] = callback_data.message_id
    try:
        if callback_data.action == 'yes':
            await dialog_manager.start(AdminPayments.CONFIRM_PAYMENT, data=user_data)
        else:
            await dialog_manager.start(AdminPayments.CANCEL_PAYMENT, data=user_data)
    except ValueError:
        await cq.message.answer(RU.cancel)


@main_router.message(F.text == 'delete_me[admin]')
async def delete_me_handler(
    message: Message,
    dialog_manager: DialogManager,
    repository: UsersRepository,
) -> None:
    success = await repository.user.remove_user(message.from_user.id)
    await message.answer(f'delete is {success}')


not_handled_router = Router()


@not_handled_router.message(~F.text.startswith('/'))
async def message_handler(
    message: Message,
    dialog_manager: DialogManager,
) -> None:
    try:
        await dialog_manager.start(BaseMenu.START)
    except ValueError:
        await message.answer(RU.cancel)


@main_router.message(Command('cancel'))
async def cmd_hello(
    message: Message,
    dialog_manager: DialogManager,
    repository: UsersRepository,
) -> None:
    await dialog_manager.start(BaseMenu.START, mode=StartMode.RESET_STACK)
