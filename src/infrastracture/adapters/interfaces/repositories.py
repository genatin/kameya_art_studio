import zoneinfo
from abc import ABC, abstractmethod
from datetime import datetime
from functools import cache

from gspread.cell import Cell
from gspread.worksheet import Worksheet

from src.application.domen.models import LessonActivity
from src.application.models import UserDTO, UserTgId


class UsersAbstractRepository(ABC):

    @abstractmethod
    def add_user(self, user: UserDTO) -> None:
        raise NotImplementedError

    @abstractmethod
    def update_user(self, user: UserDTO) -> None | str:
        raise NotImplementedError

    @abstractmethod
    def get_user(self, id: int) -> UserDTO | None:
        raise NotImplementedError

    @abstractmethod
    def load_users_from_gsheet(self) -> dict[UserTgId, UserDTO]:
        raise NotImplementedError


class BaseRepository(ABC):
    def __init__(self, wsheet: Worksheet):
        self._wsheet = wsheet

    def _find_component(self, component_name: str, row: int) -> Cell:
        cell = self._wsheet.find(component_name, in_row=row)
        return self._wsheet.col_values(cell.col)[1]

    def find_desctiption(self) -> Cell:
        return self._find_component("description", 1)

    def sign_up_user(self, user: UserDTO, lesson_activity: LessonActivity) -> None:
        values = user.to_dict(sign_up=True)
        values.update(
            {
                "topic": "undifined",
                "option": lesson_activity.lesson_option.human_name,
                "date": datetime.now(zoneinfo.ZoneInfo("Europe/Moscow")).strftime(
                    "%d.%m.%Y %H:%M"
                ),
            }
        )
        if lesson_activity.num_tickets:
            values["num_tickets"] = lesson_activity.num_tickets
        self._wsheet.append_row(list(values.values()), table_range="A1")
