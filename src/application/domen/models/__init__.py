import datetime as dt
import re
import zoneinfo
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

from src.application.domen.models.activity_type import ActivityType
from src.application.domen.models.lesson_option import LessonOption


def auto_parse_date(value: str | dt.date) -> dt.datetime:
    if isinstance(value, dt.date):
        return value
    if re.match(r'\d{2}-\d{2}-\d{4}', value):  # DD-MM-YYYY
        return dt.datetime.strptime(value, '%d-%m-%Y').date()  # noqa: DTZ007
    elif re.match(r'\d{4}-\d{2}-\d{2}', value):  # YYYY-MM-DD
        return dt.datetime.strptime(value, '%Y-%m-%d').date()  # noqa: DTZ007
    else:
        # Пробуем стандартный парсинг
        return dt.datetime.fromisoformat(value).date()


def _moscow_time_factory() -> str:
    return dt.datetime.now(zoneinfo.ZoneInfo('Europe/Moscow')).strftime('%d.%m.%Y %H:%M')


DateField = Annotated[dt.date, BeforeValidator(auto_parse_date)]


class LessonActivity(BaseModel):
    activity_type: ActivityType
    id: int | None = None
    lesson_option: LessonOption | None = None
    topic: str = Field(default='undefined')
    num_tickets: int = Field(default=1)
    status: str = Field(default='не обработано')
    datetime: str = Field(default_factory=_moscow_time_factory)
    date: DateField | None = None
    time: dt.time | None = None

    def model_dump_for_store(self) -> dict:
        return {
            'topic': self.topic,
            'option': self.lesson_option.human_name,
            'datetime': self.datetime,
            'num_tickets': self.num_tickets,
            'status': self.status,
        }
