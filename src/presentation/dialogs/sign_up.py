import logging
from typing import Callable

from aiogram import F
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, LaunchMode, StartMode, Window
from aiogram_dialog.widgets.common import ManagedScroll
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Column,
    Counter,
    ManagedCounter,
    NextPage,
    PrevPage,
    Row,
    Start,
    StubScroll,
)
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Jinja

from src.application.domen.models import LessonActivity
from src.application.domen.models.activity_type import (
    ActivityEnum,
    ActivityTypeFactory,
    child_studio_act,
    evening_sketch_act,
    lesson_act,
    mclass_act,
)
from src.application.domen.models.lesson_option import (
    LessonOption,
    LessonOptionFactory,
    classic_option,
    one_l_option,
    pro_option,
    sub4_l_option,
    sub8_l_option,
    trial_l_option,
)
from src.application.domen.text import ru
from src.application.models import UserDTO
from src.infrastracture.adapters.repositories.repo import GspreadRepository
from src.presentation.dialogs.mass_classes.mclasses import (
    FILE_ID,
    get_activity_page,
    store_activities_by_type,
)
from src.presentation.dialogs.states import (
    BaseMenu,
    ChildLessons,
    EveningSketch,
    Lessons,
    MassClasses,
    SignUp,
)
from src.presentation.dialogs.utils import notify_admins

logger = logging.getLogger(__name__)


_LESSON_ACTIVITY = "lesson_activity"
_IS_DESCRIPTION = F["activity"]["description"]
_IS_FILE_ID = F["dialog_data"][FILE_ID]
_ACTIVITY_EXISTS = F["dialog_data"]["activities"]


async def store_lesson_activity(manager: DialogManager, data):
    if isinstance(manager.start_data, dict):
        manager.dialog_data.update(manager.start_data)
    lesson_activity = manager.dialog_data.get(_LESSON_ACTIVITY)
    lesson_activity["lesson_option"] = LessonOptionFactory.generate(data).model_dump()
    await on_page_change(manager)


async def done_with_lessons(cq: CallbackQuery, _, manager: DialogManager):
    await store_lesson_activity(manager, cq.data)
    await manager.start(SignUp.STAY_FORM, data=manager.dialog_data)


async def next_with_lessons(cq: CallbackQuery, _, manager: DialogManager):
    await store_lesson_activity(manager, cq.data)
    manager.dialog_data[_LESSON_ACTIVITY]["num_tickets"] = 1
    await manager.next()


def generate_button(less_option: LessonOption) -> Callable[..., Button]:
    def button(on_click: Callable = done_with_lessons) -> Button:
        return Button(
            Const(less_option.human_name), id=less_option.name, on_click=on_click
        )

    return button


_TRIALLESSON_BUT = generate_button(trial_l_option)
_ONELESSON_BUT = generate_button(one_l_option)
_SUBSCRIPTION_4_BUT = generate_button(sub4_l_option)
_SUBSCRIPTION_8_BUT = generate_button(sub8_l_option)
_CLASSIC_LESS_BUT = generate_button(classic_option)
_PRO_LESS_BUT = generate_button(pro_option)


_BACK_TO_MENU = Row(
    Start(
        Const("Назад"),
        id="bact_to_signup",
        state=SignUp.START,
    ),
    Button(Const(" "), id="ss"),
)


async def on_value_changed(
    _, widget: ManagedCounter, dialog_manager: DialogManager
) -> None:
    dialog_manager.dialog_data[_LESSON_ACTIVITY]["num_tickets"] = widget.get_value()


_COUNTER = Counter(
    id="someid",
    default=1,
    max_value=8,
    on_value_changed=on_value_changed,
)


async def stay_form(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
):
    repository: GspreadRepository = manager.middleware_data["repository"]
    lesson_activity: LessonActivity = LessonActivity(
        **manager.start_data[_LESSON_ACTIVITY]
    )
    user: UserDTO = await repository.user.get_user(manager.event.from_user.id)

    num_row = repository.signup_user(lesson_activity=lesson_activity, user=user)
    await notify_admins(manager, user, lesson_activity, num_row)
    await callback.message.answer(ru.application_form, parse_mode=ParseMode.HTML)
    await manager.done()


async def _activity_option(cq: CallbackQuery, _, manager: DialogManager):
    activity_type = ActivityTypeFactory.generate(cq.data)
    if less_act := manager.dialog_data.get(_LESSON_ACTIVITY):
        less_act["act_type"] = activity_type
    else:
        manager.dialog_data[_LESSON_ACTIVITY] = LessonActivity(
            activity_type=activity_type
        )
    match activity_type.name:
        case ActivityEnum.LESSON.value:
            state = Lessons.START
        case ActivityEnum.CHILD_STUDIO.value:
            state = ChildLessons.START
        case ActivityEnum.MASS_CLASS.value:
            state = MassClasses.START
        case ActivityEnum.EVENING_SKETCH.value:
            state = EveningSketch.START
    await manager.start(state, data=manager.dialog_data)


async def _form_presentation(dialog_manager: DialogManager, **kwargs):
    lesson_activity: LessonActivity = LessonActivity(
        **dialog_manager.start_data.get(_LESSON_ACTIVITY)
    )
    return {
        "activity_type": lesson_activity.activity_type.human_name,
        "lesson_option": lesson_activity.lesson_option.human_name,
        "num_tickets": lesson_activity.num_tickets,
        "topic": lesson_activity.topic,
    }


async def complete(result, _, dialog_manager: DialogManager, **kwargs):
    dialog_manager.dialog_data.update(result)
    await dialog_manager.next()


async def result_after_ticket(
    _: CallbackQuery,
    button: Button,
    manager: DialogManager,
):
    await manager.start(SignUp.STAY_FORM, data=manager.dialog_data)


async def on_page_change(dialog_manager: DialogManager, *args):
    scroll: ManagedScroll | None = dialog_manager.find("scroll")
    if scroll is None:
        return
    media_number = await scroll.get_page()
    activity = dialog_manager.dialog_data.get("activities", [])
    dialog_manager.dialog_data[_LESSON_ACTIVITY]["topic"] = activity[media_number][
        "theme"
    ]


signup_dialog = Dialog(
    Window(
        Const("Выберите занятие, которое хотите посетить"),
        Button(
            Const(mclass_act.human_name),
            id=mclass_act.name,
            on_click=_activity_option,
        ),
        Button(
            Const(lesson_act.human_name),
            id=lesson_act.name,
            on_click=_activity_option,
        ),
        Button(
            Const(child_studio_act.human_name),
            id=child_studio_act.name,
            on_click=_activity_option,
        ),
        Button(
            Const(evening_sketch_act.human_name),
            id=evening_sketch_act.name,
            on_click=_activity_option,
        ),
        Row(
            Start(
                Const(ru.back_step),
                id="back_to_menu",
                state=BaseMenu.START,
                mode=StartMode.RESET_STACK,
            ),
            Button(Const(" "), id="ss"),
        ),
        state=SignUp.START,
    ),
    Window(
        Jinja(
            "<b>Ваша заявка:</b>\n\n"
            "<b>Выбранное занятие:</b> {{activity_type}}\n"
            "{% if topic != 'undefined' %}"
            "<b>Тема:</b> {{topic}}\n"
            "{% endif %}"
            "{% if lesson_option != '' %}"
            "<b>Вариант посещения:</b> {{lesson_option}}\n"
            "{% endif %}"
            "{% if num_tickets is not none %}"
            "<b>Количество билетов:</b> {{num_tickets}}\n"
            "{% endif %}"
            "<i>\nУбедитесь, что заявка корректно сформирована. \n\n"
            "Если всё правильно, оставьте заявку</i>"
        ),
        Back(
            Const("Назад"),
        ),
        Button(Const(ru.stay_form), id="done", on_click=stay_form),
        state=SignUp.STAY_FORM,
        getter=_form_presentation,
        parse_mode=ParseMode.HTML,
    ),
    launch_mode=LaunchMode.ROOT,
)


lessons_dialog = Dialog(
    Window(
        Const("Уроки скоро появятся", when=~_ACTIVITY_EXISTS),
        Format(
            "<b>Тема: {activity[theme]}</b>\nОписание: {activity[description]}",
            when="activity",
        ),
        DynamicMedia(selector=FILE_ID, when=_IS_FILE_ID),
        Column(
            _TRIALLESSON_BUT(),
            _ONELESSON_BUT(),
            _SUBSCRIPTION_4_BUT(),
            _SUBSCRIPTION_8_BUT(),
            when=_ACTIVITY_EXISTS,
        ),
        _BACK_TO_MENU,
        state=Lessons.START,
        getter=get_activity_page,
        parse_mode=ParseMode.HTML,
    ),
    on_start=store_activities_by_type,
)


child_lessons_dialog = Dialog(
    Window(
        Const("Детская студия скоро появятся", when=~_ACTIVITY_EXISTS),
        Format(
            "<b>Тема: {activity[theme]}</b>\nОписание: {activity[description]}",
            when="activity",
        ),
        DynamicMedia(selector=FILE_ID, when=_IS_FILE_ID),
        Column(
            _ONELESSON_BUT(next_with_lessons),
            _SUBSCRIPTION_4_BUT(next_with_lessons),
            _SUBSCRIPTION_8_BUT(next_with_lessons),
            when=_ACTIVITY_EXISTS,
        ),
        _BACK_TO_MENU,
        getter=get_activity_page,
        state=ChildLessons.START,
        parse_mode=ParseMode.HTML,
    ),
    Window(
        DynamicMedia(selector=FILE_ID, when=_IS_FILE_ID),
        Const("Выберите необходимое количество билетов"),
        _COUNTER,
        Row(
            Back(Const("Назад")),
            Button(Const("Дальше"), id="done", on_click=result_after_ticket),
        ),
        state=ChildLessons.TICKETS,
    ),
    on_start=store_activities_by_type,
)


mass_classes_dialog = Dialog(
    Window(
        Const("Мастер классы скоро появятся", when=~_ACTIVITY_EXISTS),
        Const("Выберите мастер-класс, который хотите выбрать", when=_ACTIVITY_EXISTS),
        Format(
            "<b>Тема: {activity[theme]}</b>\nОписание: {activity[description]}",
            when="activity",
        ),
        DynamicMedia(selector=FILE_ID, when=FILE_ID),
        StubScroll(id="scroll", pages="len_activities"),
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
            Start(
                Const("Назад"),
                id="bact_to_signup",
                state=SignUp.START,
            ),
            Button(Const("Записаться"), id="next", on_click=next_with_lessons),
        ),
        getter=get_activity_page,
        state=MassClasses.START,
        parse_mode=ParseMode.HTML,
    ),
    Window(
        Const("Выберите необходимое количество билетов"),
        _COUNTER,
        Row(
            Back(Const("Назад")),
            Button(Const("Дальше"), id="done", on_click=result_after_ticket),
        ),
        state=MassClasses.TICKETS,
    ),
    on_start=store_activities_by_type,
)


evening_sketch_dialog = Dialog(
    Window(
        Const("Вечерние наброски появятся", when=~_ACTIVITY_EXISTS),
        Format(
            "<b>Тема: {activity[theme]}</b>\nОписание: {activity[description]}",
            when="activity",
        ),
        DynamicMedia(selector=FILE_ID, when=_IS_FILE_ID),
        Column(
            _CLASSIC_LESS_BUT(next_with_lessons),
            _PRO_LESS_BUT(next_with_lessons),
            when=_ACTIVITY_EXISTS,
        ),
        _BACK_TO_MENU,
        state=EveningSketch.START,
        getter=get_activity_page,
        parse_mode=ParseMode.HTML,
    ),
    Window(
        DynamicMedia(selector=FILE_ID, when=_IS_FILE_ID),
        Const("Выберите необходимое количество билетов"),
        _COUNTER,
        Row(
            Back(Const("Назад")),
            Button(Const("Дальше"), id="done", on_click=result_after_ticket),
        ),
        state=EveningSketch.TICKETS,
    ),
    on_start=store_activities_by_type,
)
