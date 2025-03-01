from pydantic import BaseModel

from src.presentation.dialogs.models.activity_type import ActivityType
from src.presentation.dialogs.models.lesson_option import LessonOption


class LessonActivity(BaseModel):
    activity_type: ActivityType
    lesson_option: LessonOption | None = None
