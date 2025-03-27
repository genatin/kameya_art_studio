import logging
from typing import Any

from src.application.domen.models import LessonActivity
from src.application.domen.models.activity_type import ActivityEnum
from src.application.models import UserDTO
from src.infrastracture.adapters.interfaces.repositories import BaseRepository
from src.infrastracture.adapters.repositories.lessons import (
    ChildLessonsRepository,
    EveningSketchRepository,
    LessonsRepository,
    MCLassesRepository,
)
from src.infrastracture.repository.users import UsersService

logger = logging.getLogger(__name__)


class GspreadRepository:
    def __init__(
        self,
        user_repo,
        lessons_repo,
        child_lessons_repo,
        mclasses_repo,
        evening_sketch_repo,
    ):
        self.user: UsersService = user_repo
        self.lessons_repo: LessonsRepository = lessons_repo
        self.child_lessons_repo: ChildLessonsRepository = child_lessons_repo
        self.mclasses_repo: MCLassesRepository = mclasses_repo
        self.evening_sketch_repo: EveningSketchRepository = evening_sketch_repo

    def __get_repo(
        self,
        lesson_activity: str,
    ) -> BaseRepository:
        match lesson_activity:
            case ActivityEnum.LESSON.value:
                return self.lessons_repo
            case ActivityEnum.CHILD_STUDIO.value:
                return self.child_lessons_repo
            case ActivityEnum.MASS_CLASS.value:
                return self.mclasses_repo
            case ActivityEnum.EVENING_SKETCH.value:
                return self.evening_sketch_repo
            case _:
                raise NotImplementedError

    def signup_user(self, lesson_activity: LessonActivity, user: UserDTO) -> int:
        repo = self.__get_repo(lesson_activity.activity_type.name)
        return repo._sign_up_user(user, lesson_activity)

    def change_value_in_signup_user(
        self, activity_type: str, num_row: int, column_name: str, value: Any
    ):
        repo = self.__get_repo(activity_type)
        repo.change_value_in_row(num_row, column_name, value)
