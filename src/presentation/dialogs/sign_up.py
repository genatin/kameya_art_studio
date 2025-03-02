import logging

from aiogram.enums.parse_mode import ParseMode
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, Row, SwitchTo
from aiogram_dialog.widgets.text import Const, Format, Jinja

from src.application.domen.models import LessonActivity
from src.application.domen.models.activity_type import (
    ActivityEnum,
    ActivityFactory,
    child_studio_act,
    evening_sketch_act,
    lesson_act,
    master_class_act,
)
from src.application.domen.models.lesson_option import (
    LessonOption,
    LessonOptionFactory,
    one_l_option,
    sub4_l_option,
    sub8_l_option,
    trial_l_option,
)
from src.application.domen.text import ru
from src.application.models import UserDTO
from src.infrastracture import users_repository
from src.infrastracture.adapters.repositories.gspread_users import gspread_repository
from src.infrastracture.in_memory.storage import DataCache
from src.presentation.dialogs.states import SignUp
from src.presentation.dialogs.utils import notify_admins

logger = logging.getLogger(__name__)


_LESSON_ACTIVITY = "lesson_activity"

_BACK_TO_SIGN_UP = Row(
    SwitchTo(Const(ru.back_step), id="sign_up", state=SignUp.START),
    Button(Const(" "), id="empty"),
)


async def lesson_option(cq: CallbackQuery, _, manager: DialogManager):
    lesson_activity = manager.dialog_data[_LESSON_ACTIVITY]
    lesson_activity["lesson_option"] = LessonOptionFactory.generate(cq.data)
    await manager.switch_to(SignUp.STAY_FORM)


def generate_button(less_option: LessonOption) -> Button:
    return Button(
        Const(less_option.human_name), id=less_option.name, on_click=lesson_option
    )


_TRIALLESSON_BUT = generate_button(trial_l_option)
_ONELESSON_BUT = generate_button(one_l_option)
_SUBSCRIPTION_4_BUT = generate_button(sub4_l_option)
_SUBSCRIPTION_8_BUT = generate_button(sub8_l_option)


async def stay_form(
    callback: CallbackQuery, button: Button, manager: DialogManager, *_
):
    lesson_activity: LessonActivity = LessonActivity(
        **manager.dialog_data[_LESSON_ACTIVITY]
    )
    # users_repository.get_cached_user(ca)
    user: UserDTO = users_repository.collector.get_user(manager.event.from_user.id)
    gspread_repository.sign_up_user(user, lesson_activity)
    await notify_admins(manager.event.bot, user, lesson_activity)
    await callback.message.answer(ru.application_form)
    await manager.done()


async def _activity_option(cq: CallbackQuery, _, manager: DialogManager):
    activity_type = ActivityFactory.generate(cq.data)
    if less_act := manager.dialog_data.get(_LESSON_ACTIVITY):
        less_act["activity_type"] = activity_type
    else:
        manager.dialog_data[_LESSON_ACTIVITY] = LessonActivity(
            activity_type=activity_type
        )


async def _form_presentation(dialog_manager: DialogManager, **kwargs):
    lesson_activity: LessonActivity = LessonActivity(
        **dialog_manager.dialog_data[_LESSON_ACTIVITY]
    )
    return {
        "activity_type": lesson_activity.activity_type.human_name,
        "lesson_option": lesson_activity.lesson_option.human_name,
    }


async def back_on_previos_state(
    callback: CallbackQuery, button: Button, manager: DialogManager, *_
):
    lesson_activity: LessonActivity = LessonActivity(
        **manager.dialog_data[_LESSON_ACTIVITY]
    )
    match lesson_activity.activity_type.name:
        case ActivityEnum.MASS_CLASS.value:
            state = SignUp.MASS_CLASSES
        case ActivityEnum.LESSON.value:
            state = SignUp.LESSONS
        case ActivityEnum.CHILD_STUDIO.value:
            state = SignUp.CHILD_LESSONS
        case ActivityEnum.EVENING_SKETCH.value:
            state = SignUp.EVENING_LESSONS
    await manager.switch_to(state=state)


async def getter_lessons(**kwargs):
    return DataCache.lessons()


signup_dialog = Dialog(
    Window(
        Const("Выберите занятие, которое хотите посетить"),
        Button(Const(master_class_act.human_name), id=master_class_act.name),
        SwitchTo(
            Const(lesson_act.human_name),
            id=lesson_act.name,
            state=SignUp.LESSONS,
            on_click=_activity_option,
        ),
        SwitchTo(
            Const(child_studio_act.human_name),
            id=child_studio_act.name,
            state=SignUp.CHILD_LESSONS,
            on_click=_activity_option,
        ),
        Button(Const(evening_sketch_act.human_name), id=evening_sketch_act.name),
        Row(Cancel(Const(ru.back_step)), Button(Const(" "), id="ss")),
        state=SignUp.START,
    ),
    Window(
        Format("{description}"),
        _TRIALLESSON_BUT,
        _ONELESSON_BUT,
        _SUBSCRIPTION_4_BUT,
        _SUBSCRIPTION_8_BUT,
        _BACK_TO_SIGN_UP,
        state=SignUp.LESSONS,
        getter=getter_lessons,
    ),
    Window(
        Const(
            "Детские уроки🧑🏼‍🏫\n\n На этих уроках вы научитесь бла-бла-бла\n\nбла-бла-бла"
        ),
        _ONELESSON_BUT,
        _SUBSCRIPTION_4_BUT,
        _SUBSCRIPTION_8_BUT,
        _BACK_TO_SIGN_UP,
        state=SignUp.CHILD_LESSONS,
    ),
    Window(
        Jinja(
            "<b>Ваша заявка:</b>\n\n"
            "<b>Выбранное занятие:</b> {{activity_type}}\n"
            "<b>Вариант посещения:</b> {{lesson_option}}\n\n"
            "Убедитесь, что заявка корректно сформирована, с помощью кнопок ниже можно изменить данные.\n\n"
            "Если всё правильно, оставьте заявку<i></i>"
        ),
        Row(
            SwitchTo(
                Const("Выбрать другое занятие"),
                state=SignUp.START,
                id="to_lesson",
            ),
            Button(
                Const("Изменить вариант посещения"),
                id="to_lastname",
                on_click=back_on_previos_state,
            ),
        ),
        Button(Const(ru.stay_form), id="done", on_click=stay_form),
        state=SignUp.STAY_FORM,
        getter=_form_presentation,
        parse_mode=ParseMode.HTML,
    ),
)
