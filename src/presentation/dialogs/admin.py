import asyncio
import logging

from aiogram import F
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import CallbackQuery, ContentType, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities import LaunchMode, MediaAttachment, MediaId, ShowMode
from aiogram_dialog.widgets.common import ManagedScroll
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    CurrentPage,
    FirstPage,
    LastPage,
    Next,
    NextPage,
    PrevPage,
    Row,
    Start,
    StubScroll,
    SwitchTo,
)
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, List

from src.application.domen.models.activity_type import (
    ActivityEnum,
    child_studio_act,
    evening_sketch_act,
    lesson_act,
    mclass_act,
)
from src.application.domen.text import RU
from src.infrastracture.adapters.interfaces.repositories import (
    ActivityAbstractRepository,
)
from src.infrastracture.adapters.repositories.repo import UsersRepository
from src.infrastracture.database.redis.keys import BaseMenuImage
from src.infrastracture.database.redis.repository import RedisRepository
from src.presentation.callbacks import PaymentCallback, SignUpCallback
from src.presentation.dialogs.states import (
    AdminActivity,
    Administration,
    AdminPayments,
    AdminReply,
    BaseMenu,
)
from src.presentation.dialogs.utils import (
    FILE_ID,
    approve_form_for_other_admins,
    close_app_form_for_other_admins,
    get_activity_page,
    message_is_sended,
    safe_text_with_link,
    store_activities_by_type,
)
from src.presentation.reminders.payment_reminder import PaymentReminder

logger = logging.getLogger(__name__)
_PARSE_MODE_TO_USER = ParseMode.HTML
_CANCEL = Row(Start(Const('Назад'), 'empty', BaseMenu.START), Button(Const(' '), id='ss'))
_IS_EDIT = 'is_edit'
_DESCRIPTION_MC = 'description_mc'
_BACK_TO_PAGE_ACTIVITY = SwitchTo(Const('Назад'), id='back', state=AdminActivity.PAGE)


def _get_activity_repo(dialog_manager: DialogManager) -> ActivityAbstractRepository:
    return dialog_manager.middleware_data['activity_repository']


async def send_signup_message(
    manager: DialogManager, messages: list[str], callback: CallbackQuery
) -> None:
    user_id = manager.start_data['user_id']
    for m in messages:
        await manager.event.bot.send_message(
            chat_id=user_id,
            text=m,
            parse_mode=ParseMode.HTML,
        )
        await manager.event.bot.send_chat_action(user_id, 'typing')
        await asyncio.sleep(2)
    # if manager.dialog_data.get(FILE_ID):
    #     await manager.event.bot.send_photo(
    #         chat_id=user_id, photo=manager.dialog_data[FILE_ID]
    #     )
    # if manager.dialog_data.get('document'):
    #     await manager.event.bot.send_document(
    #         chat_id=user_id,
    #         document=manager.dialog_data['document'],
    #     )


async def message_admin_handler(
    message: Message,
    message_input: MessageInput,
    dialog_manager: DialogManager,
) -> None:
    cost = safe_text_with_link(message)
    dialog_manager.dialog_data['cost'] = cost
    if message.from_user.id == 697602910:
        bank_name = 'Т-банк'
        phone = '+79131721538'
        repecepient_name = 'Соловицкий Кирилл Валерьевич'
    else:
        bank_name = 'Альфа-банк'
        phone = '+79095266566'
        repecepient_name = 'Азаматов Назар Бахтиерович'

    repository: UsersRepository = dialog_manager.middleware_data['repository']
    user = await repository.user.get_user(dialog_manager.start_data['user_id'])
    admin_message_1 = [
        (
            f'{user.name}, здравствуйте! Благодарим Вас за заявку, '
            'мы зарезервировали для Вас место'
        )
    ]
    admin_messag_2 = [
        (
            f'Для бронирония места переведите деньги по номеру телефона:'
            f'\n\n💵 Стоимость участия {cost}₽'
            f'\n📞 {phone}'
            f'\n🏦 {bank_name}'
            f'\n🧑‍🎨 {repecepient_name}'
        )
    ]
    if dialog_manager.start_data['activity_type'] == ActivityEnum.CHILD_STUDIO.value:
        admin_message_3 = []
    else:
        admin_message_3 = [
            (
                'Как только платёж поступит, мы сразу же пришлём сообщение '
                'о подтверждении а также адрес и инструкцию, как до нас добраться'
            )
        ]
    admin_message_4 = [
        (
            'Если возникнут вопросы с переводом — просто напишите'
            f' нам {RU.kameya_tg_contact}, поможем!'
        )
    ]
    dialog_manager.dialog_data['admin_messages'] = (
        admin_message_1 + admin_messag_2 + admin_message_3 + admin_message_4
    )

    if message.photo or message.document:
        dialog_manager.dialog_data['admin_messages'].append(
            '<i>\n\nНиже прикрепляем документ</i>'
        )
        if message.photo:
            dialog_manager.dialog_data[FILE_ID] = message.photo[0].file_id
        if message.document:
            dialog_manager.dialog_data['document'] = message.document.file_id

    redis_repository: RedisRepository = dialog_manager.middleware_data['redis_repository']
    await redis_repository.hset(dialog_manager.start_data['message_id'], 'cost', cost)
    await dialog_manager.next()


async def send_user_payment(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Отменить запись',
        callback_data=PaymentCallback(
            action='no', message_id=manager.start_data['message_id']
        ),
    )
    builder.button(
        text='Да',
        callback_data=PaymentCallback(
            action='yes', message_id=manager.start_data['message_id']
        ),
    )
    await callback.message.answer(
        f'<b>Подтвердить оплату для заявки?</b>\n\n{manager.start_data["message"]}',
        parse_mode=_PARSE_MODE_TO_USER,
        reply_markup=builder.as_markup(),
    )
    await manager.done()
    await manager.reset_stack()
    await asyncio.sleep(0.3)


async def send_to_user(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    user_id = manager.start_data['user_id']
    if await message_is_sended(
        manager,
        user_id=user_id,
    ):
        await callback.message.answer(
            'Сообщение уже было отправлено другим администратором'
        )
        return await manager.done()

    async with asyncio.TaskGroup() as tg:
        task_close = tg.create_task(
            close_app_form_for_other_admins(
                manager,
                user_id=user_id,
                responding_admin_id=callback.from_user.id,
            )
        )
        if a_m := manager.dialog_data['admin_messages']:
            task_send = tg.create_task(send_signup_message(manager, a_m, callback))
        if manager.dialog_data.get('cost', manager.start_data['cost']) == 0:
            task_approve = tg.create_task(approve_payment(callback, None, manager))
        else:
            payment_notifier: PaymentReminder = manager.middleware_data[
                'payment_notifier'
            ]
            task_remind = tg.create_task(payment_notifier.add_reminder(user_id))
            task_payment = tg.create_task(send_user_payment(callback, button, manager))
            repository: UsersRepository = manager.middleware_data['repository']
            repository.change_values_in_signup_user(
                manager.start_data['activity_type'],
                int(manager.start_data['num_row']),
                {'cost': manager.dialog_data['cost'], 'status': 'не оплачено'},
            )


async def get_image(
    dialog_manager: DialogManager, **kwargs
) -> dict[str, MediaAttachment | str]:
    image = None
    if image_id := dialog_manager.dialog_data.get(FILE_ID):
        image = MediaAttachment(ContentType.PHOTO, file_id=MediaId(image_id))
    elif document_id := dialog_manager.dialog_data.get('document'):
        image = MediaAttachment(ContentType.DOCUMENT, file_id=MediaId(document_id))
    return {
        FILE_ID: image,
        'description': dialog_manager.dialog_data.get('description', ''),
    }


async def cancel_payment(
    callback: CallbackQuery, button: Button, manager: DialogManager, *_
) -> None:
    repository: UsersRepository = manager.middleware_data['repository']
    repository.change_value_in_signup_user(
        manager.start_data['activity_type'],
        int(manager.start_data['num_row']),
        column_name='status',
        value='Отменено',
    )
    await manager.event.bot.send_message(
        chat_id=manager.start_data['user_id'],
        text=(
            '<i>Привет! 💔'
            '\nК сожалению нам пришлось отменить занятие — '
            'загадочные обстоятельства!</i>'
            '\n\nКамея | Арт-Студия 🎨✨'
            '<b>\n\nВ случае возникших вопросов свяжитесь с нами '
            f'{RU.kameya_tg_contact}</b>'
        ),
        parse_mode=_PARSE_MODE_TO_USER,
    )
    user_phone = manager.start_data['user_phone']
    await callback.message.answer(
        (
            'Сообщение об отмене записи отправлено'
            f' <a href="https://t.me/{user_phone}">пользователю</a> '
            f'с номером телефона: {user_phone}'
        ),
        parse_mode=ParseMode.HTML,
    )
    payment_notifier: PaymentReminder = manager.middleware_data['payment_notifier']
    await payment_notifier.delete_payment(manager.start_data['user_id'])
    await approve_form_for_other_admins(
        manager,
        user_id=manager.start_data['user_id'],
        responding_admin_id=callback.from_user.id,
        message_text='Занятие отменено ❌',
    )
    await manager.done(show_mode=ShowMode.NO_UPDATE)


async def approve_payment(
    callback: CallbackQuery, button: Button, manager: DialogManager, *_
) -> None:
    repository: UsersRepository = manager.middleware_data['repository']
    repository.change_value_in_signup_user(
        manager.start_data['activity_type'],
        int(manager.start_data['num_row']),
        column_name='status',
        value='оплачено',
    )
    cost = manager.dialog_data.get('cost', manager.start_data['cost'])
    user_name = (await repository.user.get_user(manager.start_data['user_id'])).name
    if cost != 0:
        manager.dialog_data['approve_message'] = (
            f'🎉\n{user_name}, оплату получили, благодарим Вас, запись подтверждена!\n\n'
            '<b>В случае отмены необходимо свяжитесь с '
            f'нами \n{RU.kameya_tg_contact}</b>'
        )
    else:
        manager.dialog_data['approve_message'] = (
            f'🎉\n{user_name}, благодарим Вас за регистрацию, запись подтверждена!\n\n'
            '<b>В случае отмены необходимо свяжитесь с '
            f'нами \n{RU.kameya_tg_contact}</b>'
        )
    await manager.event.bot.send_message(
        chat_id=manager.start_data['user_id'],
        text=manager.dialog_data['approve_message'],
        parse_mode=_PARSE_MODE_TO_USER,
    )
    if manager.start_data['activity_type'] != ActivityEnum.CHILD_STUDIO.value:
        await manager.event.bot.send_message(
            chat_id=manager.start_data['user_id'],
            text=('Чтобы узнать как до нас добраться, используйте команду 👉 /how_to'),
            parse_mode=_PARSE_MODE_TO_USER,
        )
    payment_notifier: PaymentReminder = manager.middleware_data['payment_notifier']
    await approve_form_for_other_admins(
        manager,
        user_id=manager.start_data['user_id'],
        responding_admin_id=callback.from_user.id,
        message_text='Занятие оплачено ✅',
    )
    await payment_notifier.delete_payment(manager.start_data['user_id'])

    user_phone = manager.start_data['user_phone']
    await callback.message.answer(
        f'Сообщение отправлено <a href="https://t.me/{user_phone}">пользователю</a>'
        f' с номером телефона: {user_phone}',
        parse_mode=ParseMode.HTML,
    )
    await manager.done()


async def description_handler(
    event: Message, widget, dialog_manager: DialogManager, *_
) -> None:
    new_description = d.get_value() if (d := dialog_manager.find(_DESCRIPTION_MC)) else ''
    if dialog_manager.dialog_data.get(_IS_EDIT):
        activity_theme = dialog_manager.dialog_data['activity']['theme']
        activ_repository = _get_activity_repo(dialog_manager)
        activity = await activ_repository.update_activity_description_by_name(
            activity_type=dialog_manager.dialog_data['act_type'],
            theme=activity_theme,
            new_description=new_description,
        )
        dialog_manager.dialog_data[_IS_EDIT] = False
        if activity:
            scroll: ManagedScroll = dialog_manager.find('scroll')
            media_number = await scroll.get_page()
            dialog_manager.dialog_data['activities'][media_number]['description'] = (
                new_description
            )
            await event.answer('Описание мастер-класса успешно изменено')
        else:
            await event.answer(RU.sth_error)
        await dialog_manager.switch_to(AdminActivity.PAGE)
    else:
        dialog_manager.dialog_data['description'] = new_description
        await dialog_manager.next()


async def name_activity_handler(
    message: Message,
    message_input: MessageInput,
    dialog_manager: DialogManager,
) -> None:
    if dialog_manager.dialog_data.get(_IS_EDIT):
        activ_repository = _get_activity_repo(dialog_manager)
        activity = await activ_repository.update_activity_name_by_name(
            activity_type=dialog_manager.dialog_data['act_type'],
            old_theme=dialog_manager.dialog_data['activity']['theme'],
            new_theme=message.text,
        )
        if activity:
            scroll: ManagedScroll = dialog_manager.find('scroll')
            media_number = await scroll.get_page()
            dialog_manager.dialog_data['activities'][media_number]['theme'] = message.text
            await message.answer('Имя мастер-класса успешно изменено')
        else:
            await message.answer(RU.sth_error)
        await dialog_manager.switch_to(AdminActivity.PAGE)
    else:
        dialog_manager.dialog_data['theme_activity'] = message.text
        await dialog_manager.next()


async def change_photo(
    message: Message, dialog_manager: DialogManager, file_id: str = ''
) -> None:
    mclass_name = dialog_manager.dialog_data['activity']['theme']
    activ_repository = _get_activity_repo(dialog_manager)

    activity = await activ_repository.update_activity_fileid_by_name(
        activity_type=dialog_manager.dialog_data['act_type'],
        theme=mclass_name,
        file_id=file_id,
    )
    if activity:
        scroll: ManagedScroll | None = dialog_manager.find('scroll')
        media_number = await scroll.get_page() if scroll else 0
        dialog_manager.dialog_data['activities'][media_number][FILE_ID] = file_id
        dialog_manager.dialog_data[FILE_ID] = file_id
        await message.answer(
            f'Картинка мастер-класса успешно {"изменена" if file_id else "удалена"}'
        )
    else:
        await message.answer(RU.sth_error)


async def photo_handler(
    message: Message,
    message_input: MessageInput,
    dialog_manager: DialogManager,
) -> None:
    file_id = message.photo[0].file_id if message.photo else ''
    if not file_id:
        await message.answer(
            'Нужно приложить картинку, НЕ ДОКУМЕНТ или нажмите кнопку ниже'
        )
        return
    if dialog_manager.dialog_data.get(_IS_EDIT):
        dialog_manager.dialog_data[_IS_EDIT] = False
        await change_photo(message, dialog_manager, file_id)
        await dialog_manager.switch_to(AdminActivity.PAGE)

    else:
        dialog_manager.dialog_data[FILE_ID] = file_id
        await dialog_manager.next()


async def menu_image_handler(
    message: Message,
    message_input: MessageInput,
    dialog_manager: DialogManager,
) -> None:
    file_id = message.photo[0].file_id if message.photo else ''
    if not file_id:
        await message.answer(
            'Нужно приложить картинку, НЕ ДОКУМЕНТ или нажмите кнопку ниже'
        )
        return
    redis_repository: RedisRepository = dialog_manager.middleware_data['redis_repository']
    await redis_repository.set(BaseMenuImage(key='menu_image'), file_id, ex=None)
    await message.answer('Картинка главного меню успешно изменена.')
    await dialog_manager.start(BaseMenu.START)


async def add_activities_to_db(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    *_,
) -> None:
    act_type = dialog_manager.dialog_data['act_type']
    activities = dialog_manager.dialog_data['activities']
    theme_activity = dialog_manager.dialog_data['theme_activity']
    file_id = dialog_manager.dialog_data.get(FILE_ID, '')
    description = dialog_manager.dialog_data.get('description', '')
    activ_repository: ActivityAbstractRepository = _get_activity_repo(dialog_manager)
    act = await activ_repository.add_activity(
        activity_type=act_type,
        theme=theme_activity,
        image_id=file_id,
        description=description,
    )
    if not act:
        await callback.message.answer(f'Не удалось добавить {act_type}, попробуйте позже')
        return await dialog_manager.start(BaseMenu.START)

    await callback.message.answer(f'{act_type} добавлен.')
    activities.append(
        {
            'id': len(activities),
            'theme': theme_activity,
            'description': description,
            FILE_ID: file_id,
        }
    )

    scroll: ManagedScroll | None = dialog_manager.find('scroll')
    if scroll:
        await scroll.set_page(len(activities) - 1)
        return await dialog_manager.switch_to(AdminActivity.PAGE)
    await dialog_manager.start(Administration.REDACTOR)


async def remove_activity_from_db(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager, *_
) -> None:
    scroll: ManagedScroll = dialog_manager.find('scroll')
    media_number = await scroll.get_page()
    activities = dialog_manager.dialog_data.get('activities', [])
    activ_repository = _get_activity_repo(dialog_manager)

    await activ_repository.remove_activity_by_theme_and_type(
        activity_type=dialog_manager.dialog_data['act_type'],
        theme=activities[media_number]['theme'],
    )
    del activities[media_number]
    l_activities = len(activities)
    if l_activities > 0:
        await scroll.set_page(max(0, media_number - 1))
        await dialog_manager.switch_to(AdminActivity.PAGE)
    else:
        await dialog_manager.start(Administration.REDACTOR)


async def no_photo(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    *_,
) -> None:
    if dialog_manager.dialog_data.get(_IS_EDIT):
        await change_photo(callback.message, dialog_manager, '')
        await dialog_manager.switch_to(AdminActivity.PAGE, show_mode=ShowMode.SEND)
    else:
        dialog_manager.dialog_data[FILE_ID] = ''
        await dialog_manager.next()


async def edit_mc(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    *_,
) -> None:
    manager.dialog_data[_IS_EDIT] = True


async def get_admin_message(dialog_manager: DialogManager, **kwargs) -> dict:
    return {'message_from_user': dialog_manager.start_data['message']}


async def act_is_free(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    manager.dialog_data['admin_messages'] = None
    manager.dialog_data['cost'] = 0
    redis_repository: RedisRepository = manager.middleware_data['redis_repository']
    await redis_repository.client.hset(manager.start_data['message_id'], 'cost', 0)


async def redo_user_message(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Отменить заявку',
        callback_data=SignUpCallback(
            message_id=manager.start_data['message_id'], action='reject'
        ),
    )
    builder.button(
        text=RU.send_bank_details,
        callback_data=SignUpCallback(
            message_id=manager.start_data['message_id'], action='sign_up'
        ),
    )
    await callback.message.answer(
        manager.start_data['message'],
        parse_mode=_PARSE_MODE_TO_USER,
        reply_markup=builder.as_markup(),
    )
    await manager.done()


async def get_users(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    repository: UsersRepository = manager.middleware_data['repository']
    users = await repository.user.get_users()
    column_name = 'tg_id | last_name.name | phone\n–––––––––––––––––––––––––––––––––\n'
    users_str = '\n'.join(
        (
            f'{user.id} | {user.last_name if user.last_name else None}'
            f' {user.name if user.name else None} | {user.phone}'
        )
        for user in users
    )
    manager.dialog_data['all_users_mess'] = (
        f'Количество пользователей: {len(users)}\n\n{column_name}{users_str}'
    )


admin_reply_dialog = Dialog(
    Window(
        Const('Вы уверены, что хотите отменить запись?'),
        Row(
            Button(Const('Назад'), id='redo', on_click=redo_user_message),
            Button(Const('Да'), id='payment_approve', on_click=cancel_payment),
        ),
        state=AdminReply.CANCEL,
    ),
    Window(
        Const(
            'Введите сумму числом, например: 5000 \n\n'
            '<b>(можно прикрепить файл ИЛИ фото)</b>'
        ),
        Button(Const('Назад'), id='redo', on_click=redo_user_message),
        Next(Const('Бесплатно'), on_click=act_is_free),
        MessageInput(message_admin_handler),
        state=AdminReply.START,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Const(
            'Сообщения будут выглядеть так:',
            when=F['dialog_data']['admin_messages'],
        ),
        List(
            Format('{item}'),
            when=F['dialog_data']['admin_messages'],
            items=F['dialog_data']['admin_messages'],
        ),
        Format(
            (
                'Сообщение будет выглядеть так: \n\n'
                '🎉(имя_пользователя), благодарим Вас за регистрацию, '
                'запись подтверждена!\n\n'
                '<b>В случае отмены необходимо за 48 часов связаться с '
                f'нами \n{RU.kameya_tg_contact}</b>'
            ),
            when=~F['dialog_data']['admin_messages'],
        ),
        DynamicMedia(FILE_ID, when=FILE_ID),
        Back(Const('Исправить')),
        Button(Const('Отправить'), id='good', on_click=send_to_user),
        state=AdminReply.SEND,
        getter=get_image,
        parse_mode=ParseMode.HTML,
    ),
    launch_mode=LaunchMode.EXCLUSIVE,
)

admin_payments_dialog = Dialog(
    Window(
        Const('Вы уверены, что хотите подтвердить оплату'),
        Row(
            Button(Const('Нет'), id='redo_pay', on_click=send_user_payment),
            Button(Const('Да'), id='payment_approve', on_click=approve_payment),
        ),
        state=AdminPayments.CONFIRM_PAYMENT,
    ),
    Window(
        Const('Вы уверены, что хотите отменить запись?'),
        Row(
            Button(Const('Нет'), id='redo_pay', on_click=send_user_payment),
            Button(Const('Да'), id='payment_approve', on_click=cancel_payment),
        ),
        state=AdminPayments.CANCEL_PAYMENT,
    ),
    launch_mode=LaunchMode.EXCLUSIVE,
)


admin_dialog = Dialog(
    Window(
        Const('Режим администрирования'),
        SwitchTo(
            Const('🐑 Список зарегистрированных'),
            id='get_users',
            state=Administration.USERS,
            on_click=get_users,
        ),
        SwitchTo(
            Const('🖼 Изменить картинку в меню'),
            id='change_image',
            state=Administration.IMAGE,
        ),
        Next(Const('🎰 Редактор активностей')),
        _CANCEL,
        state=Administration.START,
    ),
    Window(
        Const('🎰 Редактор активностей'),
        Start(
            Const(RU.child_studio),
            id='child_studio',
            state=AdminActivity.PAGE,
            data={'act_type': child_studio_act},
        ),
        Start(
            Const(RU.mass_class),
            id='change_ms',
            state=AdminActivity.PAGE,
            data={'act_type': mclass_act},
        ),
        Start(
            Const(RU.lesson),
            id='change_lesson',
            state=AdminActivity.PAGE,
            data={'act_type': lesson_act},
        ),
        Start(
            Const(RU.evening_sketch),
            id='even_sketch',
            state=AdminActivity.PAGE,
            data={'act_type': evening_sketch_act},
        ),
        Row(Back(Const('Назад')), Button(Const(' '), id='ss')),
        state=Administration.REDACTOR,
    ),
    Window(
        Format('{dialog_data[all_users_mess]}'),
        Row(
            SwitchTo(Const('Назад'), id='back', state=Administration.START),
            Button(Const(' '), id='ss'),
        ),
        state=Administration.USERS,
    ),
    Window(
        Const('🖼 Изменить картинку в меню'),
        Format('Приложите фото и отправьте сообщением'),
        SwitchTo(Const('Назад'), id='back', state=Administration.START),
        MessageInput(menu_image_handler),
        state=Administration.IMAGE,
    ),
    launch_mode=LaunchMode.ROOT,
)

change_activity_dialog = Dialog(
    Window(
        Format('Меню настройки {dialog_data[act_type]}\n\n'),
        Format(
            '<b>{activity[theme]}</b>\n\n{activity[description]}',
            when='activity',
        ),
        DynamicMedia(selector=FILE_ID, when=FILE_ID),
        StubScroll(id='scroll', pages='len_activities'),
        SwitchTo(
            Const(RU.admin_change),
            id='admin_change',
            state=AdminActivity.CHANGE,
            when='len_activities',
            on_click=edit_mc,
        ),
        SwitchTo(
            Const(RU.admin_remove),
            id='remove',
            state=AdminActivity.REMOVE,
            when='len_activities',
        ),
        Row(
            LastPage(scroll='scroll', text=Const('<')),
            CurrentPage(scroll='scroll', text=Format('{current_page1}/{pages}')),
            NextPage(scroll='scroll', text=Const('>')),
            when=(F['media_number'] == 0) & F['next_p'],
        ),
        Row(
            PrevPage(scroll='scroll', text=Const('<')),
            CurrentPage(scroll='scroll', text=Format('{current_page1}/{pages}')),
            NextPage(scroll='scroll', text=Const('>')),
            when=(F['media_number'] > 0) & F['next_p'],
        ),
        Row(
            PrevPage(scroll='scroll', text=Const('<')),
            CurrentPage(scroll='scroll', text=Format('{current_page1}/{pages}')),
            FirstPage(scroll='scroll', text=Const('>')),
            when=(~F['next_p']) & (F['media_number'] > 0),
        ),
        Row(
            Cancel(Const('Назад')),
            Next(
                Format('Создать {dialog_data[act_type]}'),
            ),
        ),
        getter=get_activity_page,
        state=AdminActivity.PAGE,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Format('*Введите тему активности*\n_Например: Трансформеры в стиле Рембрандта_'),
        MessageInput(name_activity_handler, content_types=[ContentType.TEXT]),
        _BACK_TO_PAGE_ACTIVITY,
        state=AdminActivity.NAME,
        parse_mode=ParseMode.MARKDOWN,
    ),
    Window(
        Format(
            '<b>Введите описание для {dialog_data[act_type]} и '
            'отправьте сообщением</b> \n\n'
            'Например:\n<i>Погрузитесь в удивительное сочетание '
            'современной поп-культуры и '
            'классической живописи! \nНа мастер-классе вы '
            'научитесь изображать легендарных '
            'Трансформеров, вдохновляясь техникой светотени '
            'и драматизмом Рембрандта. '
            'Узнаете, как сочетать динамику футуристических '
            'персонажей с глубокими, насыщенными '
            'тонами старинной живописи. Идеально для тех, '
            'кто хочет расширить свои художественные '
            'горизонты и создать нечто уникальное!</i>'
        ),
        Row(_BACK_TO_PAGE_ACTIVITY, Next(Const('Без описания'))),
        TextInput(id=_DESCRIPTION_MC, on_success=description_handler),
        state=AdminActivity.DESCRIPTION,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Format('Приложите фото и отправьте сообщением'),
        Row(
            _BACK_TO_PAGE_ACTIVITY,
            Button(Const('Без фото'), id='next_or_edit', on_click=no_photo),
        ),
        MessageInput(photo_handler),
        state=AdminActivity.PHOTO,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        DynamicMedia(FILE_ID, when=FILE_ID),
        Format('<b><i>ВНИМАНИЕ! ОПИСАНИЕ ОТСУТСТВУЕТ</i></b>', when=~F['description']),
        Format(
            '{dialog_data[act_type]} будет выглядеть так: \n\n'
            '<b>Тема: {dialog_data[theme_activity]}</b>',
            when=F['dialog_data']['theme_activity'],
        ),
        Format('\n<b>Описание:</b> {description}', when='description'),
        Row(
            _BACK_TO_PAGE_ACTIVITY,
            Button(Const('Добавить'), id='add_mc', on_click=add_activities_to_db),
        ),
        state=AdminActivity.SEND,
        getter=get_image,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Format(
            '<b>{dialog_data[act_type]}:'
            '\n\nТема: {dialog_data[activity][theme]}'
            '\nОписание: {dialog_data[activity][description]}</b>'
            '\n\nЧто поменять?'
        ),
        DynamicMedia(FILE_ID, when=FILE_ID),
        SwitchTo(Const('Тема'), id='edit_name_mc', state=AdminActivity.NAME),
        SwitchTo(
            Const('Описание'),
            id='edit_des_mc',
            state=AdminActivity.DESCRIPTION,
        ),
        SwitchTo(
            Const('Изображение'),
            id='edit_image_mc',
            state=AdminActivity.PHOTO,
        ),
        SwitchTo(Const('Назад'), id='back', state=AdminActivity.PAGE),
        state=AdminActivity.CHANGE,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Const('Вы уверены, что хотите удалить?'),
        Button(Const('Да'), id='yes_remove', on_click=remove_activity_from_db),
        _BACK_TO_PAGE_ACTIVITY,
        state=AdminActivity.REMOVE,
    ),
    on_start=store_activities_by_type,
)
