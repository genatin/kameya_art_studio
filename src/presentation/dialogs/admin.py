import logging

from aiogram import F
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import CallbackQuery, ContentType, Message
from aiogram_dialog import Dialog, DialogManager, SubManager, Window
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, ListGroup, Next, SwitchTo
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from src.application.domen.text import ru
from src.infrastracture.adapters.repositories.repo import GspreadRepository
from src.infrastracture.database.sqlite import (
    add_mclass,
    get_all_mclasses,
    remove_mclasses_by_name,
)
from src.presentation.dialogs.states import Administration, AdminReply

logger = logging.getLogger(__name__)
_PARSE_MODE_TO_USER = ParseMode.MARKDOWN


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
    return {"image": image, "description": dialog_manager.dialog_data["description"]}


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


async def next_or_end(event, widget, dialog_manager: DialogManager, *_):
    await dialog_manager.next()


async def name_mc_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    manager.dialog_data["name_mc"] = message.text
    await manager.next()


async def photo_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    manager.dialog_data["description"] = message.text or message.caption
    manager.dialog_data["image"] = message.photo[0].file_id if message.photo else ""

    await manager.next()


async def add_mc_to_db(
    callback: CallbackQuery, button: Button, manager: DialogManager, *_
):
    name_mc = manager.dialog_data["name_mc"]
    image = manager.dialog_data["image"]
    description = manager.dialog_data["description"]
    add_mclass(name=name_mc, image=image, description=description)
    await manager.event.answer("Мастер-класс добавлен.")
    await manager.done()


async def get_mclasses(**kwargs):
    mclasses = [{"id": mclass[0], "name": mclass[1]} for mclass in get_all_mclasses()]
    return {"mclasses": mclasses}


async def remove_mc_from_db(
    callback: CallbackQuery, button: Button, sub_manager: SubManager, *_
):
    remove_mclasses_by_name(sub_manager.item_id)
    await callback.answer("Мастер-класс удалён")
    await sub_manager.done()


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
            when="{dialog_data[payment_confirm]}",
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
        SwitchTo(Const(ru.mass_class), id="change_ms", state=Administration.CHANGE_MC),
        state=Administration.START,
    ),
    Window(
        Const(ru.mass_class),
        Next(Const(ru.admin_add)),
        SwitchTo(
            Const(ru.admin_remove), id="remove_mc", state=Administration.REMOVE_MC
        ),
        state=Administration.CHANGE_MC,
    ),
    Window(
        Format(
            "*Введите название мастер-класса*\n_Например: Трансформеры в стиле Рембрандта_"
        ),
        MessageInput(name_mc_handler),
        state=Administration.NAME_MC,
        parse_mode=ParseMode.MARKDOWN,
    ),
    Window(
        Format(
            "*Введите описания для мастер-класса и не забудьте приложить фото (НЕ ДОКУМЕНТ), если требуется* \n\n_Например: Погрузитесь в удивительное сочетание современной поп-культуры и классической живописи! \nНа мастер-классе вы научитесь изображать легендарных Трансформеров, вдохновляясь техникой светотени и драматизмом Рембрандта. Узнаете, как сочетать динамику футуристических персонажей с глубокими, насыщенными тонами старинной живописи. Идеально для тех, кто хочет расширить свои художественные горизонты и создать нечто уникальное!_"
        ),
        MessageInput(photo_handler),
        state=Administration.DESCRIPTION_MC,
        parse_mode=ParseMode.MARKDOWN,
    ),
    Window(
        DynamicMedia("image", when="image"),
        Format("__*ВНИМАНИЕ! ОПИСАНИЕ ОТСУТСТВУЕТ*__", when=~F["description"]),
        Format(
            "Мастер класс будет выглядеть так: \n\n{dialog_data[name_mc]}\n\n{dialog_data[description]}"
        ),
        Back(Const("Исправить")),
        Button(Const("Добавить"), id="good", on_click=add_mc_to_db),
        state=Administration.SEND,
        getter=get_image,
        parse_mode=_PARSE_MODE_TO_USER,
    ),
    Window(
        Const("Выберите мастер-класс, который хотите удалить", when=F["mclasses"]),
        Const("Мастер-классы отсутствуют", when=~F["mclasses"]),
        ListGroup(
            Button(
                Format("{item[name]}"), id="remove_mclass", on_click=remove_mc_from_db
            ),
            id="select_search",
            item_id_getter=lambda item: item["name"],
            items="mclasses",
        ),
        SwitchTo(Const("Назад"), id="__back__", state=Administration.CHANGE_MC),
        getter=get_mclasses,
        state=Administration.REMOVE_MC,
    ),
)
