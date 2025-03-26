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

from src.application.domen.text import ru
from src.infrastracture.adapters.repositories.repo import GspreadRepository
from src.infrastracture.database.sqlite import (
    add_mclass,
    remove_mclasses_by_name,
    update_mclass_description_by_name,
    update_mclass_name_by_name,
    update_mclass_photo_by_name,
)
from src.presentation.dialogs.mass_classes.mclasses import (
    FILE_ID,
    get_mclasses_page,
    store_mclasses,
)
from src.presentation.dialogs.states import Administration, AdminMC, AdminReply
from src.presentation.dialogs.utils import safe_text_with_link

logger = logging.getLogger(__name__)
_PARSE_MODE_TO_USER = ParseMode.HTML
_CANCEL = Row(Cancel(Const("Назад")), Button(Const(" "), id="ss"))
_IS_EDIT = "is_edit"
_DESCRIPTION_MC = "description_mc"


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
        'Оплату получили, благодарим вас.\n\n<b>В случае отмены необходимо за 48 часов связаться с <a href="https://t.me/+79095266566">нами</a>!</b>'
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
        mclass_name = dialog_manager.dialog_data["mclass"]["name"]
        mc = await update_mclass_description_by_name(
            name=mclass_name, new_description=new_description
        )
        dialog_manager.dialog_data[_IS_EDIT] = False
        if mc:
            scroll: ManagedScroll = dialog_manager.find("scroll")
            media_number = await scroll.get_page()
            dialog_manager.dialog_data["mclasses"][media_number][
                "description"
            ] = new_description
            await event.answer("Описание мастер-класса успешно изменено")
        else:
            await event.answer(ru.sth_error)
        await dialog_manager.switch_to(AdminMC.PAGE)
    else:
        dialog_manager.dialog_data["description"] = new_description
        await dialog_manager.next()


async def name_mc_handler(
    message: Message,
    message_input: MessageInput,
    dialog_manager: DialogManager,
):
    if dialog_manager.dialog_data.get(_IS_EDIT):
        mclass = await update_mclass_name_by_name(
            old_name=dialog_manager.dialog_data["mclass"]["name"], new_name=message.text
        )
        if mclass:
            scroll: ManagedScroll = dialog_manager.find("scroll")
            media_number = await scroll.get_page()
            dialog_manager.dialog_data["mclasses"][media_number]["name"] = message.text
            await message.answer("Имя мастер-класса успешно изменено")
        else:
            await message.answer(ru.sth_error)
        await dialog_manager.switch_to(AdminMC.PAGE)
    else:
        dialog_manager.dialog_data["name_mc"] = message.text
        await dialog_manager.next()


async def change_photo(
    message: Message, dialog_manager: DialogManager, file_id: str = ""
):
    mclass_name = dialog_manager.dialog_data["mclass"]["name"]
    mc = await update_mclass_photo_by_name(name=mclass_name, file_id=file_id)
    if mc:
        scroll: ManagedScroll = dialog_manager.find("scroll")
        media_number = await scroll.get_page()
        dialog_manager.dialog_data["mclasses"][media_number][FILE_ID] = file_id
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
        await dialog_manager.switch_to(AdminMC.PAGE)

    else:
        dialog_manager.dialog_data[FILE_ID] = file_id
        await dialog_manager.next()


async def add_mc_to_db(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    *_,
):
    mclasses = dialog_manager.dialog_data["mclasses"]
    name_mc = dialog_manager.dialog_data["name_mc"]
    file_id = dialog_manager.dialog_data.get(FILE_ID, "")
    description = dialog_manager.dialog_data.get("description", "")
    await add_mclass(name=name_mc, image_id=file_id, description=description)
    await dialog_manager.event.answer("Мастер-класс добавлен.")
    mclasses.append(
        {
            "id": len(mclasses),
            "name": name_mc,
            "description": description,
            FILE_ID: file_id,
        }
    )
    scroll: ManagedScroll = dialog_manager.find("scroll")
    await scroll.set_page(len(mclasses) - 1)
    await dialog_manager.switch_to(AdminMC.PAGE)


async def remove_mc_from_db(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager, *_
):
    scroll: ManagedScroll = dialog_manager.find("scroll")
    media_number = await scroll.get_page()
    mclasses = dialog_manager.dialog_data.get("mclasses", [])
    await remove_mclasses_by_name(mclasses[media_number]["name"])
    del mclasses[media_number]
    l_mclasses = len(mclasses)
    if l_mclasses > 0:
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
        await dialog_manager.switch_to(AdminMC.PAGE, show_mode=ShowMode.SEND)
    else:
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
        state=AdminReply.CONFIRM_PAYMENT,
    ),
    Window(
        Const("Вы уверены, что хотите подтвердить оплату"),
        Button(Const("Да"), id="payment_approve", on_click=approve_payment),
        Back(Const("Нет")),
        state=AdminReply.PAYMENT,
    ),
    launch_mode=LaunchMode.ROOT,
    # on_start=
)


admin_dialog = Dialog(
    Window(
        Const("Вы вошли в режим администрирования, что вы хотите изменить"),
        Start(
            Const(ru.mass_class),
            id="change_ms",
            state=AdminMC.PAGE,
        ),
        _CANCEL,
        state=Administration.START,
    ),
)

change_mclass = Dialog(
    Window(
        Format(
            "<b>Тема: {mclass[name]}</b>\nОписание: {mclass[description]}",
            when="mclass",
        ),
        DynamicMedia(selector=FILE_ID, when=FILE_ID),
        StubScroll(id="scroll", pages="mc_count"),
        SwitchTo(
            Const(ru.admin_change),
            id="admin_change_mc",
            state=AdminMC.CHANGE,
            when="mc_count",
            on_click=edit_mc,
        ),
        Button(
            Const(ru.admin_remove),
            id="remove_mc",
            on_click=remove_mc_from_db,
            when="mc_count",
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
            Next(Const(f"{ru.admin_create} мастер-класс")),
        ),
        getter=get_mclasses_page,
        state=AdminMC.PAGE,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Format(
            "*Введите название мастер-класса*\n_Например: Трансформеры в стиле Рембрандта_"
        ),
        MessageInput(name_mc_handler, content_types=[ContentType.TEXT]),
        state=AdminMC.NAME,
        parse_mode=ParseMode.MARKDOWN,
    ),
    Window(
        Format(
            "<b>Введите описание для мастер-класса, если требуется</b> \n\n<i>Например: Погрузитесь в удивительное сочетание современной поп-культуры и классической живописи! \nНа мастер-классе вы научитесь изображать легендарных Трансформеров, вдохновляясь техникой светотени и драматизмом Рембрандта. Узнаете, как сочетать динамику футуристических персонажей с глубокими, насыщенными тонами старинной живописи. Идеально для тех, кто хочет расширить свои художественные горизонты и создать нечто уникальное!</i>"
        ),
        Next(Const("Без описания")),
        TextInput(id=_DESCRIPTION_MC, on_success=description_handler),
        state=AdminMC.DESCRIPTION,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Format("Приложите фото, если требуется"),
        Button(Const("Без фото"), id="next_or_edit", on_click=no_photo),
        MessageInput(photo_handler),
        state=AdminMC.PHOTO,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        DynamicMedia(FILE_ID, when=FILE_ID),
        Format("<b><i>ВНИМАНИЕ! ОПИСАНИЕ ОТСУТСТВУЕТ</i></b>", when=~F["description"]),
        Format(
            "Мастер класс будет выглядеть так: \n\n<b>Название мастер-класса: {dialog_data[name_mc]}</b>",
            when=F["dialog_data"]["name_mc"],
        ),
        Format("\nОписание: {description}", when="description"),
        Back(Const("Исправить")),
        Button(Const("Добавить"), id="add_mc", on_click=add_mc_to_db),
        state=AdminMC.SEND,
        getter=get_image,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Format("<b>Мастер-класс: {dialog_data[mclass][name]}</b>\n\nЧто поменять?"),
        SwitchTo(Const("Тема"), id="edit_name_mc", state=AdminMC.NAME),
        SwitchTo(
            Const("Описание"),
            id="edit_des_mc",
            state=AdminMC.DESCRIPTION,
        ),
        SwitchTo(
            Const("Изображение"),
            id="edit_image_mc",
            state=AdminMC.PHOTO,
        ),
        state=AdminMC.CHANGE,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    on_start=store_mclasses,
)
