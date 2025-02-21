from typing import Any

from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Back, Button, Cancel
from aiogram_dialog.widgets.text import Const

from src.cache.user_collector import user_collector
from src.dialogs.states import BaseMenu, SignUp
from src.dialogs.utils import get_cached_user

signup_dialog = Dialog(
    Window(
        Const("Выберите занятие, которое хотите посетить"),
        Button(Const("Мастер-классы"), id="mass_class"),
        Button(Const("Уроки"), id="less"),
        Button(Const("Детская студия"), id="child_less"),
        Button(Const("Вечерние наброски"), id="evening_sketch"),
        Cancel(Const("Назад")),
        state=SignUp.START,
        getter=get_cached_user,
    ),
)
