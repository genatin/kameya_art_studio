from aiogram.fsm.state import State, StatesGroup


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
    EDIT_ACTS = State()
    IMAGE = State()


class AdminActivity(StatesGroup):
    PAGE = State()
    CHANGE = State()
    REMOVE = State()

    NAME = State()
    DATE = State()
    TIME = State()
    DESCRIPTION = State()
    PHOTO = State()
    SEND = State()


class Developer(StatesGroup):
    START = State()
    TO_ADMIN = State()


class PaymentsApprove(StatesGroup):
    START = State()
    CONFIRM_PAYMENT = State()
