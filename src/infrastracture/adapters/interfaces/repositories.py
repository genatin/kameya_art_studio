import logging
import re
from abc import ABC, abstractmethod
from typing import Any

from gspread.cell import Cell
from gspread.worksheet import Worksheet

from src.application.domen.models import LessonActivity
from src.application.models import UserDTO, UserTgId

logger = logging.getLogger(__name__)


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

    def _find_component(self, component_name: str, row: int) -> Cell | None:
        return self._wsheet.find(component_name, in_row=row)

    def find_desctiption(self) -> Cell:
        cell = self._find_component("description", 1)
        if cell:
            return self._wsheet.col_values(cell.col)[1]

    def change_value_in_row(self, num_row: int, column_name: str, value: Any):
        cell = self._find_component(column_name, 1)
        self._wsheet.update_cell(num_row, cell.col, value)

    def _sign_up_user(self, user: UserDTO, lesson_activity: LessonActivity) -> str:
        values = user.to_dict(sign_up=True)
        values.update(lesson_activity.model_dump_for_store())
        response = self._wsheet.append_row(list(values.values()), table_range="A1")
        range_str = response["updates"]["updatedRange"]
        m_obj = re.search(r"\d+", range_str)
        return range_str[m_obj.start() : m_obj.end()]
