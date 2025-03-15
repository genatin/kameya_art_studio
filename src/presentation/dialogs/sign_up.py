import logging
from typing import Callable

from aiogram.enums.parse_mode import ParseMode
from aiogram.types import CallbackQuery, ContentType
from aiogram_dialog import Dialog, DialogManager, LaunchMode, StartMode, Window
from aiogram_dialog.widgets.kbd import Back, Button, Counter, ManagedCounter, Row, Start
from aiogram_dialog.widgets.media import StaticMedia
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
from src.config import get_config
from src.infrastracture.adapters.repositories.repo import GspreadRepository
from src.presentation.dialogs.states import BaseMenu, ChildLessons, Lessons, SignUp
from src.presentation.dialogs.utils import notify_admins

logger = logging.getLogger(__name__)


_LESSON_ACTIVITY = "lesson_activity"


def store_lesson_activity(manager: DialogManager, data):
    manager.dialog_data.update(manager.start_data)
    lesson_activity = manager.dialog_data.get(_LESSON_ACTIVITY)
    lesson_activity["lesson_option"] = LessonOptionFactory.generate(data).model_dump()


async def done_with_lessons(cq: CallbackQuery, _, manager: DialogManager):
    store_lesson_activity(manager, cq.data)
    await manager.start(SignUp.STAY_FORM, data=manager.dialog_data)


async def next_with_lessons(cq: CallbackQuery, _, manager: DialogManager):
    store_lesson_activity(manager, cq.data)
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
    match lesson_activity.activity_type.name:
        case ActivityEnum.LESSON.value:
            repo = repository.lessons_repo
        case ActivityEnum.CHILD_STUDIO.value:
            repo = repository.child_lessons_repo

    repo.sign_up_user(user, lesson_activity)
    await notify_admins(manager.event, user, lesson_activity)
    await callback.message.answer(ru.application_form, parse_mode=ParseMode.HTML)
    await manager.done()


async def _activity_option(cq: CallbackQuery, _, manager: DialogManager):
    activity_type = ActivityFactory.generate(cq.data)
    if less_act := manager.dialog_data.get(_LESSON_ACTIVITY):
        less_act["activity_type"] = activity_type
    else:
        manager.dialog_data[_LESSON_ACTIVITY] = LessonActivity(
            activity_type=activity_type
        )
    match activity_type.name:
        case ActivityEnum.LESSON.value:
            state = Lessons.START
        case ActivityEnum.CHILD_STUDIO.value:
            state = ChildLessons.START
    await manager.start(state, data=manager.dialog_data)


async def _form_presentation(dialog_manager: DialogManager, **kwargs):
    lesson_activity: LessonActivity = LessonActivity(
        **dialog_manager.start_data.get(_LESSON_ACTIVITY)
    )
    return {
        "activity_type": lesson_activity.activity_type.human_name,
        "lesson_option": lesson_activity.lesson_option.human_name,
        "num_tickets": lesson_activity.num_tickets,
    }


async def getter_lessons(repository: GspreadRepository, **kwargs):
    return {"description": repository.lessons_repo.find_desctiption()}


async def getter_child(repository: GspreadRepository, **kwargs):
    return {"description": repository.child_lessons_repo.find_desctiption()}


async def complete(result, _, dialog_manager: DialogManager, **kwargs):
    dialog_manager.dialog_data.update(result)
    await dialog_manager.next()


signup_dialog = Dialog(
    Window(
        Const("Выберите занятие, которое хотите посетить"),
        Button(Const(master_class_act.human_name), id=master_class_act.name),
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
        Button(Const(evening_sketch_act.human_name), id=evening_sketch_act.name),
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
            "<b>Вариант посещения:</b> {{lesson_option}}\n"
            "{% if num_tickets is not none %}"
            "<b>Количество билетов:</b> {{num_tickets}}"
            "{% endif %}"
            "<i>\n\nУбедитесь, что заявка корректно сформирована. \n\n"
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


async def result_on_child(
    _: CallbackQuery,
    button: Button,
    manager: DialogManager,
):
    await manager.start(SignUp.STAY_FORM, data=manager.dialog_data)


lessons_dialog = Dialog(
    Window(
        StaticMedia(
            path=get_config().LESSONS_IMAGE_PATH,
            type=ContentType.PHOTO,
        ),
        Format("{description}"),
        _TRIALLESSON_BUT(),
        _ONELESSON_BUT(),
        _SUBSCRIPTION_4_BUT(),
        _SUBSCRIPTION_8_BUT(),
        _BACK_TO_MENU,
        state=Lessons.START,
        getter=getter_lessons,
    ),
)


child_lessons_dialog = Dialog(
    Window(
        StaticMedia(
            path=get_config().CHILD_LESS_IMAGE_PATH,
            type=ContentType.PHOTO,
        ),
        Format("{description}"),
        _ONELESSON_BUT(next_with_lessons),
        _SUBSCRIPTION_4_BUT(next_with_lessons),
        _SUBSCRIPTION_8_BUT(next_with_lessons),
        _BACK_TO_MENU,
        state=ChildLessons.START,
        getter=getter_child,
    ),
    Window(
        StaticMedia(
            path=get_config().CHILD_LESS_IMAGE_PATH,
            type=ContentType.PHOTO,
        ),
        Format(
            "Тип посещения: {dialog_data[lesson_activity][lesson_option][human_name]}"
        ),
        _COUNTER,
        Row(
            Back(Const("Назад")),
            Button(Const("Дальше"), id="done", on_click=result_on_child),
        ),
        state=ChildLessons.TICKETS,
    ),
)
