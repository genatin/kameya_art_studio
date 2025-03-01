from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, Row, SwitchTo
from aiogram_dialog.widgets.text import Const

from src.presentation.dialogs.states import SignUp
from src.presentation.dialogs.utils import get_cached_user
from src.presentation.keyboards.text import ru

signup_dialog = Dialog(
    Window(
        Const("Выберите занятие, которое хотите посетить"),
        Button(Const("Мастер-классы"), id="mass_class"),
        SwitchTo(Const("Уроки"), id="less", state=SignUp.LESSONS),
        Button(Const("Детская студия"), id="child_less"),
        Button(Const("Вечерние наброски"), id="evening_sketch"),
        Row(Cancel(Const(ru.back_step)), Button(Const(""), id="ss")),
        state=SignUp.START,
        getter=get_cached_user,
    ),
    Window(
        Const(
            "Уроки 🧑🏼‍🏫\n\n На этих уроках вы научитесь бла-бла-бла\n\nбла-бла-бла"
        ),
        state=SignUp.LESSONS,
    ),
)
