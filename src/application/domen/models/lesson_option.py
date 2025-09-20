from pydantic import BaseModel

from src.application.domen.text import RU

TRIAL_LESS = 'trial_less'
ONE_LESS = 'one_less'
SUBSCRIPTION_4 = 'subscrition_4'
SUBSCRIPTION_8 = 'subscrition_8'
CLASSIC_LESS = 'classic_less'
PRO_LESS = 'pro_less'


class LessonOption(BaseModel):
    name: str
    human_name: str


class LessonOptionFactory:
    lesson_human_readable = {
        TRIAL_LESS: RU.trial_lesson,
        ONE_LESS: RU.one_lesson,
        SUBSCRIPTION_4: RU.subscription_4,
        SUBSCRIPTION_8: RU.subscription_8,
        CLASSIC_LESS: RU.classic_less,
        PRO_LESS: RU.pro_less,
    }

    @classmethod
    def generate(cls, name: str) -> LessonOption:
        return LessonOption(name=name, human_name=cls.lesson_human_readable.get(name, ''))


trial_l_option = LessonOptionFactory.generate(TRIAL_LESS)
one_l_option = LessonOptionFactory.generate(ONE_LESS)
sub4_l_option = LessonOptionFactory.generate(SUBSCRIPTION_4)
sub8_l_option = LessonOptionFactory.generate(SUBSCRIPTION_8)
classic_option = LessonOptionFactory.generate(CLASSIC_LESS)
pro_option = LessonOptionFactory.generate(PRO_LESS)
