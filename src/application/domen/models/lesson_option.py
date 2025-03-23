from pydantic import BaseModel

from src.application.domen.text import ru

TRIAL_LESS = "trial_less"
ONE_LESS = "one_less"
SUBSCRIPTION_4 = "subscrition_4"
SUBSCRIPTION_8 = "subscrition_8"


class LessonOption(BaseModel):
    name: str
    human_name: str


class LessonOptionFactory:
    lesson_human_readable = {
        TRIAL_LESS: ru.trial_lesson,
        ONE_LESS: ru.one_lesson,
        SUBSCRIPTION_4: ru.subscription_4,
        SUBSCRIPTION_8: ru.subscription_8,
    }

    @classmethod
    def generate(cls, name: str) -> LessonOption:
        return LessonOption(
            name=name, human_name=cls.lesson_human_readable.get(name, "")
        )


trial_l_option = LessonOptionFactory.generate(TRIAL_LESS)
one_l_option = LessonOptionFactory.generate(ONE_LESS)
sub4_l_option = LessonOptionFactory.generate(SUBSCRIPTION_4)
sub8_l_option = LessonOptionFactory.generate(SUBSCRIPTION_8)
