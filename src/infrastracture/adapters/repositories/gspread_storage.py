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
from src.infrastracture.adapters.interfaces.repositories import UsersAbstractRepository

logger = logging.getLogger(__name__)

config = get_config()


class GspreadStorage:
    sheet: Spreadsheet = gspread.service_account(
        filename=config.SERVICE_FILE_NAME
    ).open(config.GSHEET_NAME)

    def lessons(cls):
        logger.info(f"lpppppp")
        ws = cls.sheet.worksheet(config.lessons_page)
        cell = ws.find("description", in_row=1)
        return ws.col_values(cell.col)[1]


gspread_storage = GspreadStorage()
