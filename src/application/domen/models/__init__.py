from pydantic import BaseModel

from src.application.domen.models.activity_type import ActivityType
from src.application.domen.models.lesson_option import LessonOption


class LessonActivity(BaseModel):
    activity_type: ActivityType
    lesson_option: LessonOption | None = None
