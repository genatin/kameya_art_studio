import logging

from aiogram import F
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import CallbackQuery, ContentType, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities import LaunchMode, MediaAttachment, MediaId, StartMode
from aiogram_dialog.widgets.common import ManagedScroll
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    CurrentPage,
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
    get_mclasses_page,
    store_mclasses,
)
from src.presentation.dialogs.states import Administration, AdminMC, AdminReply

logger = logging.getLogger(__name__)
_PARSE_MODE_TO_USER = ParseMode.MARKDOWN
_CANCEL = Row(Cancel(Const("Назад")), Button(Const(" "), id="ss"))
_IS_EDIT = "is_edit"
_DESCRIPTION_MC = "description_mc"


async def message_admin_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    manager.dialog_data["admin_message"] = (
        f"Ответ от Камея Арт Студии:\n\n_{message.text or message.caption}_"
    )

    if message.photo or message.document:
        manager.dialog_data["admin_message"] += "\n\n_(Ниже прикрепляем документ)_"
        if message.photo:
            manager.dialog_data["image"] = message.photo[0].file_id
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
            parse_mode=_PARSE_MODE_TO_USER,
        )
    if manager.dialog_data.get("image"):
        await manager.event.bot.send_photo(
            chat_id=manager.start_data["user_id"], photo=manager.dialog_data["image"]
        )
    if manager.dialog_data.get("document"):
        await manager.event.bot.send_document(
            chat_id=manager.start_data["user_id"],
            document=manager.dialog_data["document"],
        )
    await manager.next()


async def get_image(dialog_manager: DialogManager, **kwargs):
    image = None
    if image_id := dialog_manager.dialog_data.get("image"):
        image = MediaAttachment(ContentType.PHOTO, file_id=MediaId(image_id))
    elif document_id := dialog_manager.dialog_data.get("document"):
        image = MediaAttachment(ContentType.DOCUMENT, file_id=MediaId(document_id))
    return {
        "image": image,
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
        "Оплату получили, благодарим вас.\nВ случае отмены необходимо за 48 часов уведомить в этом чате о переносе, иначе сертификат сгорит!\n"
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
            await event.answer("Описание мастер-класса успешно изменено")
            await dialog_manager.start(Administration.START)
        else:
            await event.answer(ru.sth_error)
            await dialog_manager.start(Administration.START)
    else:
        dialog_manager.dialog_data["description"] = new_description
        await dialog_manager.next()


async def name_mc_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    logger.info(f"---> {manager.dialog_data.get(_IS_EDIT)}")
    if manager.dialog_data.get(_IS_EDIT):
        mclass = await update_mclass_name_by_name(
            old_name=manager.dialog_data["mclass"]["name"], new_name=message.text
        )
        if mclass:
            await message.answer("Имя мастер-класса успешно изменено")
        await manager.start(Administration.START)
    else:
        manager.dialog_data["name_mc"] = message.text
        await manager.next()


async def photo_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    file_id = message.photo[0].file_id if message.photo else ""
    logger.info(f"--->photo {manager.dialog_data.get(_IS_EDIT)}")
    if not file_id:
        await message.answer(
            "Нужно приложить картинку, НЕ ДОКУМЕНТ или нажмите кнопку ниже"
        )
        return
    if manager.dialog_data.get(_IS_EDIT):
        manager.dialog_data[_IS_EDIT] = False
        mclass_name = manager.dialog_data["mclass"]["name"]
        if file_id:
            mc = await update_mclass_photo_by_name(name=mclass_name, file_id=file_id)
            if mc:
                await message.answer("Картинка мастер-класса успешно изменена")
        await manager.start(Administration.START)

    else:
        manager.dialog_data["image"] = file_id
        await manager.next()


async def add_mc_to_db(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    *_,
):
    name_mc = manager.dialog_data["name_mc"]
    image = manager.dialog_data.get("image", "")
    description = manager.dialog_data.get("description", "")
    await add_mclass(name=name_mc, image_id=image, description=description)
    await manager.event.answer("Мастер-класс добавлен.")
    await manager.start(Administration.START)


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


async def edit_mc(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    *_,
):
    manager.dialog_data[_IS_EDIT] = True
    logger.info(f"-- edit > {manager.dialog_data[_IS_EDIT]}")


admin_reply_dialog = Dialog(
    Window(
        Const(
            "Введите сообщение, которое хотите отправить пользователю \n\n*(можно прикрепить файл ИЛИ фото)*"
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
        DynamicMedia("image", when="image"),
        Back(Const("Исправить")),
        Button(Const("Отправить"), id="good", on_click=send_to_user),
        state=AdminReply.SEND,
        getter=get_image,
        parse_mode=_PARSE_MODE_TO_USER,
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
)


admin_dialog = Dialog(
    Window(
        Const("Вы вошли в режим администрирования, что вы хотите изменить"),
        Start(
            Const(ru.mass_class),
            id="change_ms",
            state=AdminMC.START,
        ),
        _CANCEL,
        state=Administration.START,
    ),
)

change_mclass = Dialog(
    Window(
        Const(f"{ru.mass_class}ы"),
        Next(Const(ru.admin_add)),
        SwitchTo(
            Const(ru.admin_current),
            id="remove_mc",
            state=AdminMC.PAGE,
            when=F["dialog_data"]["mclasses"],
        ),
        _CANCEL,
        state=AdminMC.START,
    ),
    Window(
        Format(
            "*Введите название мастер-класса*\n_Например: Трансформеры в стиле Рембрандта_"
        ),
        MessageInput(name_mc_handler),
        state=AdminMC.NAME,
        parse_mode=ParseMode.MARKDOWN,
    ),
    Window(
        Format(
            "*Введите описание для мастер-класса, если требуется* \n\n_Например: Погрузитесь в удивительное сочетание современной поп-культуры и классической живописи! \nНа мастер-классе вы научитесь изображать легендарных Трансформеров, вдохновляясь техникой светотени и драматизмом Рембрандта. Узнаете, как сочетать динамику футуристических персонажей с глубокими, насыщенными тонами старинной живописи. Идеально для тех, кто хочет расширить свои художественные горизонты и создать нечто уникальное!_"
        ),
        Next(Const("Без описания")),
        TextInput(id=_DESCRIPTION_MC, on_success=description_handler),
        state=AdminMC.DESCRIPTION,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Format("Приложите фото, если требуется"),
        Next(Const("Без фото")),
        MessageInput(photo_handler),
        state=AdminMC.PHOTO,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        DynamicMedia("image", when="image"),
        Format("__*ВНИМАНИЕ! ОПИСАНИЕ ОТСУТСТВУЕТ*__", when=~F["description"]),
        Format(
            "Мастер класс будет выглядеть так: \n\n*Название мастер-класса: {dialog_data[name_mc]}"
        ),
        Format("\nОписание: {description}*", when="description"),
        Back(Const("Исправить")),
        Button(Const("Добавить"), id="good", on_click=add_mc_to_db),
        state=AdminMC.SEND,
        getter=get_image,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Format("*Тема: {mclass[name]}*\nОписание: {mclass[description]}"),
        DynamicMedia(selector="image", when="image"),
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
        SwitchTo(Const("Назад"), id="__back__", state=AdminMC.START),
        getter=get_mclasses_page,
        state=AdminMC.PAGE,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Format("*Мастер-класс: {dialog_data[mclass][name]}*\n\nЧто поменять?"),
        SwitchTo(Const("Название"), id="edit_name_mc", state=AdminMC.NAME),
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
