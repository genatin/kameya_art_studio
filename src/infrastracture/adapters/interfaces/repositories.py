import logging
import re
from abc import ABC, abstractmethod
from collections.abc import Sequence
from contextlib import suppress
from typing import Any

from gspread.cell import Cell
from gspread.utils import rowcol_to_a1
from gspread.worksheet import Worksheet

from src.application.domen.models import LessonActivity
from src.application.models import UserDTO
from src.infrastracture.database.sqlite.models import Activity

logger = logging.getLogger(__name__)


class UsersAbstractRepository(ABC):
    @abstractmethod
    async def add_user(self, user: UserDTO) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_user(self, user: UserDTO) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_user(self, id: int) -> UserDTO | None:
        raise NotImplementedError

    @abstractmethod
    async def get_users(self) -> list[UserDTO] | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_user(self, id: int) -> UserDTO | None:
        raise NotImplementedError


class BaseRepository:
    def __init__(self, wsheet: Worksheet) -> None:
        self._wsheet = wsheet

    def _find_component(self, component_name: str, row: int) -> Cell | None:
        return self._wsheet.find(component_name, in_row=row)

    def change_value_in_row(self, num_row: int, column_name: str, value: Any) -> None:
        cell = self._find_component(column_name, 1)
        self._wsheet.update_cell(num_row, cell.col, value)

    def update_cells_by_headers(self, num_row: int, updates: dict) -> None:
        """Обновляет ячейки в указанной строке по названиям столбцов.

        :param row_num: Номер строки (начинается с 1)
        :param updates: Словарь {название_столбца: новое_значение}
        """
        # Получаем все заголовки
        headers = self._wsheet.row_values(1)

        requests = []
        for col_name, value in updates.items():
            with suppress(ValueError):
                col_idx = headers.index(col_name) + 1
                cell = rowcol_to_a1(num_row, col_idx)
                requests.append({'range': cell, 'values': [[value]]})

        if requests:
            self._wsheet.batch_update(requests)

    def change_values_in_row(self, num_row: int, values: dict) -> None:
        self.update_cells_by_headers(num_row, values)

    def _sign_up_user(self, user: UserDTO, lesson_activity: LessonActivity) -> str:
        values = user.to_dict(sign_up=True)
        values.update(lesson_activity.model_dump_for_store())
        response = self._wsheet.append_row(list(values.values()), table_range='A1')
        range_str = response['updates']['updatedRange']
        m_obj = re.search(r'\d+', range_str)
        return range_str[m_obj.start() : m_obj.end()]


class ActivityAbstractRepository(ABC):
    @abstractmethod
    async def add_activity(
        self,
        activity_type: str,
        theme: str,
        image_id: str,
        content_type: str,
        description: str | None = None,
    ) -> Activity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_all_activity_by_type(self, activity_type: str) -> Sequence[Activity]:
        raise NotImplementedError

    @abstractmethod
    async def update_activity_name_by_name(
        self, activity_type: str, old_theme: str, new_theme: str
    ) -> Activity | None:
        raise NotImplementedError

    @abstractmethod
    async def update_activity_description_by_name(
        self, activity_type: str, theme: str, new_description: str
    ) -> Activity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_activity_by_theme_and_type(
        self,
        activity_type: str,
        theme: str,
    ) -> Activity:
        raise NotImplementedError

    @abstractmethod
    async def update_activity_fileid_by_name(
        self, activity_type: str, theme: str, file_id: str, content_type: str
    ) -> Activity | None:
        raise NotImplementedError

    @abstractmethod
    async def remove_activity_by_theme_and_type(
        self, activity_type: str, theme: str
    ) -> None:
        raise NotImplementedError
