import logging
import time

from src.infrastracture.adapters.repositories.lessons import (
    ChildLessonsRepository,
    LessonsRepository,
)
from src.infrastracture.repository.users import UsersRepository

logger = logging.getLogger(__name__)


class GspreadRepository:
    def __init__(self, user_repo, lessons_repo, child_lessons_repo):
        self.user: UsersRepository = user_repo
        self.lessons_repo: LessonsRepository = lessons_repo
        self.child_lessons_repo: ChildLessonsRepository = child_lessons_repo

    def update_cache(self):
        self.lessons_repo.find_desctiption.cache_clear()
        self.lessons_repo.find_desctiption()
