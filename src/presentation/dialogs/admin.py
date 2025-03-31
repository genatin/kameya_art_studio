import logging

from aiogram import F
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import CallbackQuery, ContentType, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities import LaunchMode, MediaAttachment, MediaId, ShowMode
from aiogram_dialog.widgets.common import ManagedScroll
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    Next,
    NextPage,
    PrevPage,
    Row,
    Start,
    StubScroll,
    SwitchTo,
)
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from src.application.domen.models.activity_type import (
    child_studio_act,
    evening_sketch_act,
    lesson_act,
    mclass_act,
)
from src.application.domen.text import ru
from src.infrastracture.adapters.repositories.activities import ActivityRepository
from src.infrastracture.adapters.repositories.repo import GspreadRepository
from src.presentation.dialogs.states import (
    AdminActivity,
    Administration,
    AdminReply,
    BaseMenu,
)
from src.presentation.dialogs.utils import (
    FILE_ID,
    get_activity_page,
    safe_text_with_link,
    store_activities_by_type,
)

logger = logging.getLogger(__name__)
_PARSE_MODE_TO_USER = ParseMode.HTML
_CANCEL = Row(
    Start(Const("Назад"), "empty", BaseMenu.START), Button(Const(" "), id="ss")
)
_IS_EDIT = "is_edit"
_DESCRIPTION_MC = "description_mc"
_BACK = Back(Const("Назад"))


def _get_activity_repo(dialog_manager: DialogManager) -> ActivityRepository:
    return dialog_manager.middleware_data["activity_repository"]


async def message_admin_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    safe_text = safe_text_with_link(message)
    manager.dialog_data["admin_message"] = f"Ответ от Камея Арт Студии:\n\n{safe_text}"
    if message.photo or message.document:
        manager.dialog_data["admin_message"] += "\n\nНиже прикрепляем документ"
        if message.photo:
            manager.dialog_data[FILE_ID] = message.photo[0].file_id
        if message.document:
            manager.dialog_data["document"] = message.document.file_id

    await manager.next()


async def send_to_user(
    callback: CallbackQuery, button: Button, manager: DialogManager, *_
):
    if manager.dialog_data["admin_message"]:
        await manager.event.bot.send_message(
            chat_id=manager.start_data["user_id"],
            text=manager.dialog_data["admin_message"],
            parse_mode=ParseMode.HTML,
        )
    if manager.dialog_data.get(FILE_ID):
        await manager.event.bot.send_photo(
            chat_id=manager.start_data["user_id"], photo=manager.dialog_data[FILE_ID]
        )
    if manager.dialog_data.get("document"):
        await manager.event.bot.send_document(
            chat_id=manager.start_data["user_id"],
            document=manager.dialog_data["document"],
        )
    await manager.next()


async def get_image(dialog_manager: DialogManager, **kwargs):
    image = None
    if image_id := dialog_manager.dialog_data.get(FILE_ID):
        image = MediaAttachment(ContentType.PHOTO, file_id=MediaId(image_id))
    elif document_id := dialog_manager.dialog_data.get("document"):
        image = MediaAttachment(ContentType.DOCUMENT, file_id=MediaId(document_id))
    return {
        FILE_ID: image,
        "description": dialog_manager.dialog_data.get("description", ""),
    }


async def approve_payment(
    callback: CallbackQuery, button: Button, manager: DialogManager, *_
):
    repository: GspreadRepository = manager.middleware_data["repository"]
    repository.change_value_in_signup_user(
        manager.start_data["activity_type"],
        int(manager.start_data["num_row"]),
        column_name="status",
        value="оплачено",
    )

    manager.dialog_data["approve_message"] = (
        'Оплату получили, благодарим вас.\n\n<b>В случае отмены необходимо за 48 часов связаться с <a href="https://t.me/+79963673783">нами</a>!</b>'
    )
    await manager.event.bot.send_message(
        chat_id=manager.start_data["user_id"],
        text=manager.dialog_data["approve_message"],
        parse_mode=_PARSE_MODE_TO_USER,
    )
    await callback.message.answer("Сообщение отправлено пользователю")
    await manager.done()


async def description_handler(
    event: Message, widget, dialog_manager: DialogManager, *_
):
    new_description = (
        d.get_value() if (d := dialog_manager.find(_DESCRIPTION_MC)) else ""
    )
    if dialog_manager.dialog_data.get(_IS_EDIT):
        activity_theme = dialog_manager.dialog_data["activity"]["theme"]
        activ_repository = _get_activity_repo(dialog_manager)
        activity = await activ_repository.update_activity_description_by_name(
            type_name=dialog_manager.dialog_data["act_type"],
            theme=activity_theme,
            new_description=new_description,
        )
        dialog_manager.dialog_data[_IS_EDIT] = False
        if activity:
            scroll: ManagedScroll = dialog_manager.find("scroll")
            media_number = await scroll.get_page()
            dialog_manager.dialog_data["activities"][media_number][
                "description"
            ] = new_description
            await event.answer("Описание мастер-класса успешно изменено")
        else:
            await event.answer(ru.sth_error)
        await dialog_manager.switch_to(AdminActivity.PAGE)
    else:
        dialog_manager.dialog_data["description"] = new_description
        await dialog_manager.next()


async def name_activity_handler(
    message: Message,
    message_input: MessageInput,
    dialog_manager: DialogManager,
):
    if dialog_manager.dialog_data.get(_IS_EDIT):
        activ_repository = _get_activity_repo(dialog_manager)
        activity = await activ_repository.update_activity_name_by_name(
            activity_type=dialog_manager.dialog_data["act_type"],
            old_theme=dialog_manager.dialog_data["activity"]["theme"],
            new_theme=message.text,
        )
        if activity:
            scroll: ManagedScroll = dialog_manager.find("scroll")
            media_number = await scroll.get_page()
            dialog_manager.dialog_data["activities"][media_number][
                "theme"
            ] = message.text
            await message.answer("Имя мастер-класса успешно изменено")
        else:
            await message.answer(ru.sth_error)
        await dialog_manager.switch_to(AdminActivity.PAGE)
    else:
        dialog_manager.dialog_data["theme_activity"] = message.text
        await dialog_manager.next()


async def change_photo(
    message: Message, dialog_manager: DialogManager, file_id: str = ""
):
    mclass_name = dialog_manager.dialog_data["activity"]["theme"]
    activ_repository = _get_activity_repo(dialog_manager)

    activity = await activ_repository.update_activity_fileid_by_name(
        type_name=dialog_manager.dialog_data["act_type"],
        theme=mclass_name,
        file_id=file_id,
    )
    if activity:
        scroll: ManagedScroll | None = dialog_manager.find("scroll")
        media_number = await scroll.get_page() if scroll else 0
        dialog_manager.dialog_data["activities"][media_number][FILE_ID] = file_id
        dialog_manager.dialog_data[FILE_ID] = file_id
        await message.answer(
            f"Картинка мастер-класса успешно {'изменена' if file_id else 'удалена'}"
        )
    else:
        await message.answer(ru.sth_error)


async def photo_handler(
    message: Message,
    message_input: MessageInput,
    dialog_manager: DialogManager,
):
    file_id = message.photo[0].file_id if message.photo else ""
    if not file_id:
        await message.answer(
            "Нужно приложить картинку, НЕ ДОКУМЕНТ или нажмите кнопку ниже"
        )
        return
    if dialog_manager.dialog_data.get(_IS_EDIT):
        dialog_manager.dialog_data[_IS_EDIT] = False
        await change_photo(message, dialog_manager, file_id)
        await dialog_manager.switch_to(AdminActivity.PAGE)

    else:
        dialog_manager.dialog_data[FILE_ID] = file_id
        await dialog_manager.next()


async def add_activities_to_db(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    *_,
):
    act_type = dialog_manager.dialog_data["act_type"]
    activities = dialog_manager.dialog_data["activities"]
    theme_activity = dialog_manager.dialog_data["theme_activity"]
    file_id = dialog_manager.dialog_data.get(FILE_ID, "")
    description = dialog_manager.dialog_data.get("description", "")
    activ_repository = _get_activity_repo(dialog_manager)
    act = await activ_repository.add_activity(
        activity_type=act_type,
        theme=theme_activity,
        image_id=file_id,
        description=description,
    )
    if not act:
        await callback.message.answer(
            f"Не удалось добавить {act_type}, попробуйте позже"
        )
        return await dialog_manager.start(BaseMenu.START)

    await callback.message.answer(f"{act_type} добавлен.")
    activities.append(
        {
            "id": len(activities),
            "theme": theme_activity,
            "description": description,
            FILE_ID: file_id,
        }
    )

    scroll: ManagedScroll | None = dialog_manager.find("scroll")
    if scroll:
        await scroll.set_page(len(activities) - 1)
        return await dialog_manager.switch_to(AdminActivity.PAGE)
    await dialog_manager.start(Administration.START)


async def remove_activity_from_db(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager, *_
):
    scroll: ManagedScroll = dialog_manager.find("scroll")
    media_number = await scroll.get_page()
    activities = dialog_manager.dialog_data.get("activities", [])
    activ_repository = _get_activity_repo(dialog_manager)

    await activ_repository.remove_activity_by_theme_and_type(
        type_name=dialog_manager.dialog_data["act_type"],
        theme=activities[media_number]["theme"],
    )
    del activities[media_number]
    l_activities = len(activities)
    if l_activities > 0:
        await scroll.set_page(max(0, media_number - 1))
    else:
        await dialog_manager.start(Administration.START)


async def no_photo(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    *_,
):
    if dialog_manager.dialog_data.get(_IS_EDIT):
        await change_photo(callback.message, dialog_manager, "")
        await dialog_manager.switch_to(AdminActivity.PAGE, show_mode=ShowMode.SEND)
    else:
        dialog_manager.dialog_data[FILE_ID] = ""
        await dialog_manager.next()


async def edit_mc(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    *_,
):
    manager.dialog_data[_IS_EDIT] = True


admin_reply_dialog = Dialog(
    Window(
        Const(
            "Введите сообщение, которое хотите отправить пользователю \n\n<b>(можно прикрепить файл ИЛИ фото)</b>"
        ),
        MessageInput(message_admin_handler),
        state=AdminReply.REPLY,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Format("Сообщение будет выглядеть так: \n\n{dialog_data[admin_message]}"),
        Const(
            "Пользователю отправится подтверждение об оплате",
            when=F["dialog_data"]["payment_confirm"],
        ),
        DynamicMedia(FILE_ID, when=FILE_ID),
        Back(Const("Исправить")),
        Button(Const("Отправить"), id="good", on_click=send_to_user),
        state=AdminReply.SEND,
        getter=get_image,
        parse_mode=ParseMode.HTML,
    ),
    Window(
        Const("Сообщение отправлено\n\nПодтвердить оплату?"),
        Next(Const("Да")),
        Cancel(Const("Отменить")),
    ),
    Window(
        Const("Вы уверены, что хотите подтвердить оплату"),
        Row(
            Button(Const("Да"), id="payment_approve", on_click=approve_payment),
            Back(Const("Нет")),
        ),
        state=AdminReply.PAYMENT,
    ),
)


admin_dialog = Dialog(
    Window(
        Const("Вы вошли в режим администрирования, что вы хотите изменить"),
        Start(
            Const(ru.mass_class),
            id="change_ms",
            state=AdminActivity.PAGE,
            data={"act_type": mclass_act},
        ),
        Start(
            Const(ru.lesson),
            id="change_lesson",
            state=AdminActivity.PAGE,
            data={"act_type": lesson_act},
        ),
        Start(
            Const(ru.child_studio),
            id="child_studio",
            state=AdminActivity.PAGE,
            data={"act_type": child_studio_act},
        ),
        Start(
            Const(ru.evening_sketch),
            id="even_sketch",
            state=AdminActivity.PAGE,
            data={"act_type": evening_sketch_act},
        ),
        _CANCEL,
        state=Administration.START,
    ),
    launch_mode=LaunchMode.ROOT,
)

change_activity_dialog = Dialog(
    Window(
        Format("Меню настройки {dialog_data[act_type]}\n\n"),
        Format(
            "<b>Тема: {activity[theme]}</b>\nОписание: {activity[description]}",
            when="activity",
        ),
        DynamicMedia(selector=FILE_ID, when=FILE_ID),
        StubScroll(id="scroll", pages="len_activities"),
        SwitchTo(
            Const(ru.admin_change),
            id="admin_change_mc",
            state=AdminActivity.CHANGE,
            when="len_activities",
            on_click=edit_mc,
        ),
        Button(
            Const(ru.admin_remove),
            id="remove_mc",
            on_click=remove_activity_from_db,
            when="len_activities",
        ),
        Row(
            Button(Const(" "), id="but"),
            NextPage(scroll="scroll"),
            when=(F["media_number"] == 0) & F["next_p"],
        ),
        Row(
            PrevPage(scroll="scroll"),
            NextPage(scroll="scroll"),
            when=(F["media_number"] > 0) & F["next_p"],
        ),
        Row(
            PrevPage(scroll="scroll"),
            Button(Const(" "), id="but1"),
            when=(~F["next_p"]) & (F["media_number"] > 0),
        ),
        Row(
            Cancel(Const("Назад")),
            Next(
                Format("Создать {dialog_data[act_type]}"),
                # кнопка активна всегда для мастер-классов, в остальных случаях
                # только если активностей нет совсем
                when=(
                    (F["dialog_data"]["act_type"] == ru.mass_class)
                    | (
                        (~(F["dialog_data"]["act_type"] == ru.mass_class))
                        & (F["len_activities"] == 0)
                    )
                ),
            ),
        ),
        getter=get_activity_page,
        state=AdminActivity.PAGE,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Format(
            "*Введите тему активности*\n_Например: Трансформеры в стиле Рембрандта_"
        ),
        MessageInput(name_activity_handler, content_types=[ContentType.TEXT]),
        state=AdminActivity.NAME,
        parse_mode=ParseMode.MARKDOWN,
    ),
    Window(
        Format(
            "<b>Введите описание для {dialog_data[act_type]} и отправьте сообщением</b> \n\nНапример:\n<i>Погрузитесь в удивительное сочетание современной поп-культуры и классической живописи! \nНа мастер-классе вы научитесь изображать легендарных Трансформеров, вдохновляясь техникой светотени и драматизмом Рембрандта. Узнаете, как сочетать динамику футуристических персонажей с глубокими, насыщенными тонами старинной живописи. Идеально для тех, кто хочет расширить свои художественные горизонты и создать нечто уникальное!</i>"
        ),
        Row(_BACK, Next(Const("Без описания"))),
        TextInput(id=_DESCRIPTION_MC, on_success=description_handler),
        state=AdminActivity.DESCRIPTION,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Format("Приложите фото и отправьте сообщением"),
        Row(_BACK, Button(Const("Без фото"), id="next_or_edit", on_click=no_photo)),
        MessageInput(photo_handler),
        state=AdminActivity.PHOTO,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        DynamicMedia(FILE_ID, when=FILE_ID),
        Format("<b><i>ВНИМАНИЕ! ОПИСАНИЕ ОТСУТСТВУЕТ</i></b>", when=~F["description"]),
        Format(
            "{dialog_data[act_type]} будет выглядеть так: \n\n<b>Тема: {dialog_data[theme_activity]}</b>",
            when=F["dialog_data"]["theme_activity"],
        ),
        Format("\n<b>Описание:</b> {description}", when="description"),
        Row(
            _BACK, Button(Const("Добавить"), id="add_mc", on_click=add_activities_to_db)
        ),
        state=AdminActivity.SEND,
        getter=get_image,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Format(
            "<b>{dialog_data[act_type]}: {dialog_data[activity][theme]}</b>\n\nЧто поменять?\n\n<b>Обратите внимание, для обновления некоторых изменений требуется время (~1 мин)</b>"
        ),
        SwitchTo(Const("Тема"), id="edit_name_mc", state=AdminActivity.NAME),
        SwitchTo(
            Const("Описание"),
            id="edit_des_mc",
            state=AdminActivity.DESCRIPTION,
        ),
        SwitchTo(
            Const("Изображение"),
            id="edit_image_mc",
            state=AdminActivity.PHOTO,
        ),
        state=AdminActivity.CHANGE,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    on_start=store_activities_by_type,
)
