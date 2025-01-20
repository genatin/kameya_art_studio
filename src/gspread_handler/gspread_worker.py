from contextlib import contextmanager
from functools import partial
from queue import Queue
from threading import RLock, Thread
from typing import Iterator

import gspread

from src.config import Config, config
from src.database.dto import UserDTO
from src.database.user_collector import UserTgId


class GspreadWorker:
    def __init__(self, config: Config):
        self.__gp = gspread.service_account(filename=config.SERVICE_ACCOUNT_FILE_NAME)
        self.__tasks_queue: Queue = Queue(maxsize=10000)
        self.__lock = RLock()

    def __add_to_queue(f):
        def wrapper(self, *args, **kwargs):
            self.__tasks_queue.put(partial(f, self, *args, **kwargs))

        return wrapper

    @contextmanager
    def open_gsheet(self, file_name: str) -> Iterator[gspread.Spreadsheet]:
        self.__gsheet = self.__gp.open(file_name)
        try:
            yield self.__gsheet
        finally:
            self.__gsheet = None

    def run_background_update(self):
        Thread(target=self.__background_update_sheets, daemon=True).start()

    def __background_update_sheets(self):
        while True:
            task = self.__tasks_queue.get()
            with self.__lock:
                task()

    def load_users_from_gsheet(self) -> dict[UserTgId, UserDTO]:
        with self.open_gsheet(config.GSHEET_NAME) as gsheet:
            users_sheet = gsheet.worksheet(config.users_page)
            list_of_dicts = users_sheet.get_all_records()[1:]
            return {tg_id: UserDTO(id=tg_id) for tg_id, phone, *_ in list_of_dicts}

    @__add_to_queue
    def add_user(self, user: UserDTO) -> None:
        with self.open_gsheet(config.GSHEET_NAME) as gsheet:
            users = gsheet.worksheet(config.users_page)
            values = list(user.model_dump(exclude_none=True).values())
            users.append_row(values)

    @__add_to_queue
    def update_data_user(self, user: UserDTO) -> None:
        with self.open_gsheet(config.GSHEET_NAME) as gsheet:
            wsheet_users = gsheet.worksheet(config.users_page)
            row_num = wsheet_users.find(user.id, in_column=1).row
            wsheet_users.batch_update(user.compile_batch(row_num))


gspread_worker = GspreadWorker(config)
