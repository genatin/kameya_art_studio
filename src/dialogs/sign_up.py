from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, Row
from aiogram_dialog.widgets.text import Const

from src.dialogs.states import SignUp
from src.dialogs.utils import get_cached_user

signup_dialog = Dialog(
    Window(
        Const("Выберите занятие, которое хотите посетить"),
        Button(Const("Мастер-классы"), id="mass_class"),
        Button(Const("Уроки"), id="less"),
        Button(Const("Детская студия"), id="child_less"),
        Button(Const("Вечерние наброски"), id="evening_sketch"),
        Row(Cancel(Const("Назад")), Button(Const(""), id="ss")),
        state=SignUp.START,
        getter=get_cached_user,
    ),
)
