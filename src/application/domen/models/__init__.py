import zoneinfo
from datetime import datetime

from pydantic import BaseModel, Field

from src.application.domen.models.activity_type import ActivityType
from src.application.domen.models.lesson_option import LessonOption


def _moscow_time_factory() -> str:
    return datetime.now(zoneinfo.ZoneInfo('Europe/Moscow')).strftime('%d.%m.%Y %H:%M')


class LessonActivity(BaseModel):
    activity_type: ActivityType
    lesson_option: LessonOption | None = None
    topic: str = Field(default='undefined')
    num_tickets: int = Field(default=1)
    status: str = Field(default='не обработано')
    datetime: str = Field(default_factory=_moscow_time_factory)

    def model_dump_for_store(self) -> dict:
        return {
            'topic': self.topic,
            'option': self.lesson_option.human_name,
            'datetime': self.datetime,
            'num_tickets': self.num_tickets,
            'status': self.status,
        }
