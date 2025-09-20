from enum import Enum

from pydantic import BaseModel

from src.application.domen.text import RU


class ActivityEnum(Enum):
    LESSON = 'lesson'
    CHILD_STUDIO = 'child_studio'
    EVENING_SKETCH = 'evening_sketch'
    MASS_CLASS = 'mclasses'


class ActivityType(BaseModel):
    name: str
    human_name: str


class ActivityTypeFactory:
    activity_human_readable = {
        ActivityEnum.MASS_CLASS: RU.mass_class,
        ActivityEnum.LESSON: RU.lesson,
        ActivityEnum.CHILD_STUDIO: RU.child_studio,
        ActivityEnum.EVENING_SKETCH: RU.evening_sketch,
    }

    @classmethod
    def generate(cls, name: ActivityEnum | str) -> ActivityType:
        if isinstance(name, str):
            name = ActivityEnum(name)
        return ActivityType(name=name.value, human_name=cls.activity_human_readable[name])


mclass_act = ActivityTypeFactory.generate(ActivityEnum.MASS_CLASS)
lesson_act = ActivityTypeFactory.generate(ActivityEnum.LESSON)
child_studio_act = ActivityTypeFactory.generate(ActivityEnum.CHILD_STUDIO)
evening_sketch_act = ActivityTypeFactory.generate(ActivityEnum.EVENING_SKETCH)
