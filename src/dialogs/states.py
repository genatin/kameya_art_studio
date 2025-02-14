from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    SEND_CONTACT = State()
    GET_CONTACT = State()
    NAME = State()
    NAME_IS = State()
    LASTNAME = State()
    LASTNAME_IS = State()


class BaseMenu(StatesGroup):
    START = State()
    SIGN_UP = State()
    ABOUT_US = State()
    END = State()
