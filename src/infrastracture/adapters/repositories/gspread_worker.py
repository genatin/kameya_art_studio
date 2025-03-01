import logging
import zoneinfo
from datetime import datetime
from functools import partial, wraps
from queue import Queue
from threading import Thread

import gspread
from gspread.cell import Cell
from gspread.spreadsheet import Spreadsheet

from src.application.domen.models import LessonActivity
from src.application.domen.models.activity_type import ActivityEnum
from src.application.models import UserDTO, UserTgId
from src.config import Config, get_config
from src.infrastracture.database.interfaces.repositories import UsersAbstractRepository

logger = logging.getLogger(__name__)


class GspreadRepository(UsersAbstractRepository):
    def __init__(self, config: Config):
        self.__tasks_queue: Queue = Queue(maxsize=1000)
        self.config = config
        self.__sheet: Spreadsheet = gspread.service_account(
            filename=config.SERVICE_FILE_NAME
        ).open(config.GSHEET_NAME)

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
        users_sheet = self.__sheet.worksheet(self.config.users_page)
        list_of_dicts = users_sheet.get_all_records()
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
        ws = self.__sheet.worksheet(self.config.users_page)
        user_id = user.id if user else id
        return ws.find(str(user_id), in_column=1)

    def get_user(self, id: int) -> UserDTO | None:
        ws = self.__sheet.worksheet(self.config.users_page)
        cell = self.__get_user_cell(id=id)
        if cell:
            values = ws.row_values(cell.row)
            return UserDTO.parse_from_row(values)

    @__add_to_queue
    def add_user(self, user: UserDTO) -> None:
        ws = self.__sheet.worksheet(self.config.users_page)
        cell = self.__get_user_cell(user=user)
        if cell:
            self.update_user(user)
        else:
            values = list(user.to_dict(exclude_none=True).values())
            ws.append_row(values)

    @__add_to_queue
    def sign_up_user(self, user: UserDTO, lesson_activity: LessonActivity) -> None:
        match lesson_activity.activity_type.name:
            case ActivityEnum.LESSON.value:
                page = self.config.lessons_page
            case ActivityEnum.CHILD_STUDIO.value:
                page = self.config.child_page
            case ActivityEnum.MASS_CLASS.value:
                page = self.config.master_class_page
            case ActivityEnum.EVENING_SKETCH.value:
                page = self.config.evening_page

        ws = self.__sheet.worksheet(page)
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
        ws.append_row(list(values.values()))

    def update_user(self, user: UserDTO) -> None | str:
        ws = self.__sheet.worksheet(self.config.users_page)
        cell = self.__get_user_cell(user=user)
        if cell:
            return ws.batch_update(user.compile_batch(cell.row))


gspread_repository = GspreadRepository(get_config())
