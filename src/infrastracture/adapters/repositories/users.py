import logging
from functools import partial, wraps
from queue import Queue
from threading import Thread

from gspread.cell import Cell
from gspread.worksheet import Worksheet

from src.application.models import UserDTO, UserTgId
from src.infrastracture.adapters.interfaces.repositories import UsersAbstractRepository

logger = logging.getLogger(__name__)


class RepositoryUser(UsersAbstractRepository):
    def __init__(self, wsheet_user: Worksheet):
        self.__tasks_queue: Queue = Queue(maxsize=1000)
        self._user_worksheet = wsheet_user

    def __add_to_queue(f):
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            self.__tasks_queue.put(partial(f, self, *args, **kwargs))

        return wrapper

    def run_background_update(self):
        Thread(target=self.__background_update_sheets, daemon=True).start()

    def __background_update_sheets(self):
        while True:
            task = self.__tasks_queue.get()
            task()

    def load_users_from_gsheet(self) -> dict[UserTgId, UserDTO]:
        list_of_dicts = self._user_worksheet.get_all_records()
        return {
            int(user_data["id"]): UserDTO(**user_data)
            for user_data in list_of_dicts
            if user_data["id"]
        }

    def __get_user_cell(
        self,
        user: UserDTO | None = None,
        id: int | None = None,
    ) -> Cell | None:
        user_id = user.id if user else id
        return self._user_worksheet.find(str(user_id), in_column=1)

    def get_user(self, id: int) -> UserDTO | None:
        cell = self.__get_user_cell(id=id)
        if cell:
            values = self._user_worksheet.row_values(cell.row)
            return UserDTO.parse_from_row(values)

    @__add_to_queue
    def add_user(self, user: UserDTO) -> None:
        cell = self.__get_user_cell(user=user)
        if cell:
            self.update_user(user)
        else:
            values = list(user.to_dict(exclude_none=True).values())
            self._user_worksheet.append_row(values)

    def update_user(self, user: UserDTO) -> None | str:
        cell = self.__get_user_cell(user=user)
        if cell:
            return self._user_worksheet.batch_update(user.compile_batch(cell.row))
