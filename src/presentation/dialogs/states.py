from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


class FirstSeen(StatesGroup):
    START = State()


class Registration(StatesGroup):
    GET_CONTACT = State()
    EDIT_CONTACT = State()
    NAME = State()
    LASTNAME = State()
    END = State()


class BaseMenu(StatesGroup):
    START = State()
    SIGN_UP = State()
    ABOUT_US = State()
    HOW_TO = State()
    END = State()


class SignUp(StatesGroup):
    START = State()
    STAY_FORM = State()


class AcitivityPages(StatesGroup):
    START = State()
    TICKETS = State()


class AdminReply(StatesGroup):
    START = State()
    CANCEL = State()
    SEND = State()


class AdminPayments(StatesGroup):
    CANCEL_PAYMENT = State()
    CONFIRM_PAYMENT = State()


class Administration(StatesGroup):
    START = State()


class AdminActivity(StatesGroup):
    PAGE = State()
    CHANGE = State()
    REMOVE = State()

    NAME = State()
    DESCRIPTION = State()
    PHOTO = State()
    SEND = State()
