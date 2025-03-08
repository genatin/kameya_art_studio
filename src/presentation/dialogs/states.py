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
    END = State()


class SignUp(StatesGroup):
    START = State()
    STAY_FORM = State()


class Lessons(StatesGroup):
    START = State()


class ChildLessons(StatesGroup):
    START = State()
    TICKETS = State()
