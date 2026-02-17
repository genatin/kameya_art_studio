import logging
from collections.abc import Callable
from typing import Any

from aiogram import F
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import CallbackQuery
from aiogram_dialog import (
    Dialog,
    DialogManager,
    LaunchMode,
    ShowMode,
    StartMode,
    Window,
)
from aiogram_dialog.widgets.common import ManagedScroll
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    Counter,
    CurrentPage,
    FirstPage,
    LastPage,
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
    ActivityTypeFactory,
    child_studio_act,
    evening_sketch_act,
    lesson_act,
    mclass_act,
)
from src.application.domen.models.lesson_option import LessonOption, LessonOptionFactory
from src.application.domen.text import RU
from src.application.models import UserDTO
from src.infrastracture.adapters.repositories.repo import UsersRepository
from src.presentation.dialogs.states import AcitivityPages, BaseMenu, SignUp
from src.presentation.dialogs.utils import (
    FILE_ID,
    format_date_russian,
    get_activity_page,
    store_activities_by_type,
    validate_activities_inplace,
)
from src.presentation.notifier import Notifier

logger = logging.getLogger(__name__)


_LESSON_ACTIVITY = 'lesson_activity'
_IS_FILE_ID = F[FILE_ID] | F['dialog_data'][FILE_ID]
_ACTIVITY_EXISTS = F['dialog_data']['activities']
_THEME_AND_DESCRIPTION_HTML = Format(
    ('<b>{activity[theme]}</b>\n\n<i>{activity[description]}</i>'),
    when='activity',
)

_BACK_TO_MENU_ROW_IF_NO_ACTIVITIES = Row(
    Start(
        Const('Назад'),
        id='bact_to_signup',
        state=SignUp.START,
    ),
    Button(Const(' '), id='ss'),
    when=~_ACTIVITY_EXISTS,
)


async def on_value_changed(
    _, widget: ManagedCounter, dialog_manager: DialogManager
) -> None:
    dialog_manager.dialog_data[_LESSON_ACTIVITY]['num_tickets'] = widget.get_value()


_COUNTER = Counter(
    id='someid',
    default=1,
    min_value=1,
    max_value=8,
    on_value_changed=on_value_changed,
)


async def result_after_ticket(
    _: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.start(SignUp.STAY_FORM, data=manager.dialog_data)


_TICKET_WIDGETS = (
    DynamicMedia(selector=FILE_ID, when=_IS_FILE_ID),
    Const(
        'Выберите необходимое количество билетов\n\n<i>Количество билетов ограничено</i>'
    ),
    _COUNTER,
    Row(
        Back(Const('Назад')),
        Button(Const('Дальше'), id='done', on_click=result_after_ticket),
    ),
)


async def store_lesson_activity(manager: DialogManager, data) -> None:
    if isinstance(manager.start_data, dict):
        manager.dialog_data.update(manager.start_data)
    lesson_activity = manager.dialog_data.get(_LESSON_ACTIVITY)
    lesson_activity['lesson_option'] = LessonOptionFactory.generate(data).model_dump()
    await on_page_change(manager)


async def done_with_lessons(cq: CallbackQuery, _, manager: DialogManager) -> None:
    await store_lesson_activity(manager, cq.data)
    await manager.start(SignUp.STAY_FORM, data=manager.dialog_data)


async def next_with_lessons(cq: CallbackQuery, _, manager: DialogManager) -> None:
    await store_lesson_activity(manager, cq.data)
    manager.dialog_data[_LESSON_ACTIVITY]['num_tickets'] = 1
    await manager.next()


def generate_button(less_option: LessonOption) -> Callable[..., Button]:
    def button(on_click: Callable = done_with_lessons) -> Button:
        return Button(
            Const(less_option.human_name), id=less_option.name, on_click=on_click
        )

    return button


async def stay_form(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    repository: UsersRepository = manager.middleware_data['repository']
    notifier: Notifier = manager.middleware_data['notifier']
    lesson_activity: LessonActivity = LessonActivity(
        **manager.start_data[_LESSON_ACTIVITY]
    )
    message = await callback.message.answer(RU.random_wait)
    user: UserDTO = await repository.user.get_user(manager.event.from_user.id)
    num_row = repository.signup_user(lesson_activity=lesson_activity, user=user)
    await notifier.sign_up_notify(user, lesson_activity, num_row, manager)
    await message.delete()
    await callback.message.answer(RU.application_form, parse_mode=ParseMode.HTML)
    await manager.done()


async def jump_to_activity_pages(
    manager: DialogManager,
    act_name: str | None,
    act_id: int | None = None,
    show_mode: ShowMode | None = None,
) -> None:
    activity_type = ActivityTypeFactory.generate(act_name)
    start_data = manager.dialog_data if manager.has_context() else {}
    mode = StartMode.NORMAL
    if act_id is not None:
        mode = StartMode.RESET_STACK
        start_data['act_id'] = act_id
    start_data[_LESSON_ACTIVITY] = LessonActivity(activity_type=activity_type)
    await manager.start(
        AcitivityPages.START,
        data=start_data,
        show_mode=show_mode,
        mode=mode,
    )


async def _activity_option(cq: CallbackQuery, _, manager: DialogManager) -> None:
    await jump_to_activity_pages(manager, cq.data)


async def _form_presentation(
    dialog_manager: DialogManager, **kwargs
) -> dict[str, str | int]:
    lesson_activity: LessonActivity = LessonActivity(
        **dialog_manager.start_data.get(_LESSON_ACTIVITY)
    )
    date_ = format_date_russian(lesson_activity.date) if lesson_activity.date else None
    time_ = lesson_activity.time.strftime('%H:%M') if lesson_activity.time else None
    return {
        'activity_type': lesson_activity.activity_type.human_name,
        'lesson_option': lesson_activity.lesson_option.human_name,
        'num_tickets': lesson_activity.num_tickets,
        'topic': lesson_activity.topic,
        'date': lesson_activity.date,
        'time': lesson_activity.time,
        'date_repr': date_,
        'time_repr': time_,
    }


async def complete(result, _, dialog_manager: DialogManager, **kwargs) -> None:
    dialog_manager.dialog_data.update(result)
    await dialog_manager.next()


async def on_page_change(dialog_manager: DialogManager, *args) -> None:
    scroll: ManagedScroll | None = dialog_manager.find('scroll')
    if scroll is None:
        return
    media_number = await scroll.get_page()
    activity = dialog_manager.dialog_data.get('activities', [])
    dialog_manager.dialog_data[_LESSON_ACTIVITY]['topic'] = activity[media_number][
        'theme'
    ]
    dialog_manager.dialog_data[_LESSON_ACTIVITY]['date'] = activity[media_number].get(
        'date'
    )
    if t := activity[media_number].get('time'):
        dialog_manager.dialog_data[_LESSON_ACTIVITY]['time'] = t


async def get_random_message(dialog_manager: DialogManager, **kwargs) -> dict[str, str]:
    return {'random_signup_message': RU.random_signup}


async def _store_activities_by_type_sign_up(
    start_data: Any, manager: DialogManager
) -> None:
    activities = await store_activities_by_type(start_data, manager)
    validate_activities_inplace(activities)
    manager.dialog_data['activities'] = activities


signup_dialog = Dialog(
    Window(
        Format('{random_signup_message}'),
        Button(
            Const(child_studio_act.human_name),
            id=child_studio_act.name,
            on_click=_activity_option,
        ),
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
            Const(evening_sketch_act.human_name),
            id=evening_sketch_act.name,
            on_click=_activity_option,
        ),
        Row(
            Start(
                Const(RU.back_step),
                id='back_to_menu',
                state=BaseMenu.START,
                mode=StartMode.RESET_STACK,
            ),
            Button(Const(' '), id='ss'),
        ),
        getter=get_random_message,
        state=SignUp.START,
    ),
    Window(
        Jinja(
            '<b>Ваша заявка:</b>\n\n'
            '<b>Выбранное занятие:</b> {{activity_type}}\n'
            "{% if topic != 'undefined' %}"
            '<b>Тема:</b> {{topic}}\n'
            '{% endif %}'
            "{% if lesson_option != '' %}"
            '<b>Вариант посещения:</b> {{lesson_option}}\n'
            '{% endif %}'
            '{% if num_tickets is not none %}'
            '<b>Количество билетов:</b> {{num_tickets}}\n'
            '{% endif %}'
            '{% if date_repr is not none %}'
            '<b>Дата занятия:</b> {{date_repr}}\n'
            '{% endif %}'
            '{% if time_repr is not none %}'
            '<b>Время:</b> {{time_repr}}\n'
            '{% endif %}'
            '<i>\nУбедитесь, что заявка корректно сформирована. \n\n'
            'Если всё правильно, оставьте заявку.</i>'
        ),
        Row(
            Back(
                Const('Назад'),
            ),
            Button(Const(RU.stay_form), id='done', on_click=stay_form),
        ),
        state=SignUp.STAY_FORM,
        getter=_form_presentation,
        parse_mode=ParseMode.HTML,
    ),
    launch_mode=LaunchMode.ROOT,
)


activity_pages_dialog = Dialog(
    Window(
        Format('🙈 Ой, активность не найдена', when=F['not_found']),
        Format('{dialog_data[act_type]} скоро будут доступны', when=~_ACTIVITY_EXISTS),
        _THEME_AND_DESCRIPTION_HTML,
        Format(
            '<i><b>Дата: {activity[date_repr]} </b></i>',
            when=F['activity']['date_repr'],
        ),
        Format(
            '<i><b>Время: {activity[time_repr]} </b></i>',
            when=F['activity']['time_repr'],
        ),
        DynamicMedia(selector=FILE_ID, when=FILE_ID),
        StubScroll(id='scroll', pages='len_activities'),
        # Button(Const('😉 Ссылка для друга'), id='gen_link', on_click=generate_deep_link),
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
            Start(
                Const('Назад'),
                id='bact_to_signup',
                state=SignUp.START,
            ),
            Button(Const('Записаться'), id='next', on_click=next_with_lessons),
            when=_ACTIVITY_EXISTS & ~F['not_found'],
        ),
        Cancel(
            Const(RU.menu),
            id='bact_to_signup',
            when=F['not_found'],
        ),
        _BACK_TO_MENU_ROW_IF_NO_ACTIVITIES,
        getter=get_activity_page,
        state=AcitivityPages.START,
        parse_mode=ParseMode.HTML,
    ),
    Window(*_TICKET_WIDGETS, state=AcitivityPages.TICKETS, parse_mode=ParseMode.HTML),
    on_start=_store_activities_by_type_sign_up,
)
