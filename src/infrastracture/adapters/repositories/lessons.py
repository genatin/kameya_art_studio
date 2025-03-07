import logging

from src.infrastracture.adapters.interfaces.repositories import BaseRepository

logger = logging.getLogger(__name__)


class LessonsRepository(BaseRepository):
    pass


class ChildLessonsRepository(BaseRepository):
    pass
