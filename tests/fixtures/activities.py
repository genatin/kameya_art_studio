"""Тестовые фикстуры для активностей."""
from datetime import datetime, time
from unittest.mock import MagicMock

from src.application.domen.models.activity_type import ActivityEnum
from src.application.domen.models.lesson_option import LessonOption
from src.application.models import UserDTO


# Валидные данные для тестирования активностей
VALID_ACTIVITY_DATA = {
    'activity_type': ActivityEnum.LESSON,
    'topic': 'Тестовая активность',
    'description': 'Описание тестовой активности',
    'date': datetime(2024, 12, 1),
    'time': time(14, 0),
    'num_tickets': 1,
    'lesson_option': LessonOption.SIGN_UP,
}

# Данные для разных типов активностей
ACTIVITY_TYPES_DATA = {
    'lesson': {
        'activity_type': ActivityEnum.LESSON,
        'topic': 'Урок рисования',
        'description': 'Обучение основам живописи',
        'date': datetime(2024, 12, 1),
        'time': time(14, 0),
    },
    'child_studio': {
        'activity_type': ActivityEnum.CHILD_STUDIO,
        'topic': 'Детская студия',
        'description': 'Творческие занятия для детей',
        'date': datetime(2024, 12, 2),
        'time': time(10, 0),
    },
    'mass_class': {
        'activity_type': ActivityEnum.MASS_CLASS,
        'topic': 'Мастер-класс',
        'description': 'Вечерний мастер-класс для взрослых',
        'date': datetime(2024, 12, 3),
        'time': time(18, 0),
    },
    'evening_sketch': {
        'activity_type': ActivityEnum.EVENING_SKETCH,
        'topic': 'Вечерние наброски',
        'description': 'Рисование с натуры',
        'date': datetime(2024, 12, 4),
        'time': time(19, 0),
    },
}

# Опции уроков
LESSON_OPTIONS = [
    LessonOption.SIGN_UP,
    LessonOption.WAIT_LIST,
]


class ActivityFixtures:
    """Класс с фабриками тестовых активностей."""

    @staticmethod
    def create_valid_lesson_activity(**kwargs):
        """Создать валидную активность для урока."""
        from src.application.domen.models import LessonActivity

        data = VALID_ACTIVITY_DATA.copy()
        data.update(kwargs)
        return LessonActivity(**data)

    @staticmethod
    def create_activity_by_type(activity_type: str, **kwargs):
        """Создать активность по типу."""
        from src.application.domen.models import LessonActivity

        data = ACTIVITY_TYPES_DATA.get(activity_type, ACTIVITY_TYPES_DATA['lesson'])
        data.update(kwargs)
        data['num_tickets'] = data.get('num_tickets', 1)
        data['lesson_option'] = data.get('lesson_option', LessonOption.SIGN_UP)
        return LessonActivity(**data)

    @staticmethod
    def create_multiple_lessons(count: int = 3, start_day: int = 1):
        """Создать несколько уроков."""
        from src.application.domen.models import LessonActivity

        lessons = []
        for i in range(count):
            day = start_day + i
            lessons.append(
                LessonActivity(
                    activity_type=ActivityEnum.LESSON,
                    topic=f'Урок {i + 1}',
                    description=f'Описание урока {i + 1}',
                    date=datetime(2024, 12, day),
                    time=time(14 + i, 0),
                    num_tickets=1,
                    lesson_option=LessonOption.SIGN_UP,
                )
            )
        return lessons

    @staticmethod
    def create_activity_with_custom_tickets(num_tickets: int):
        """Создать активность с указанным количеством билетов."""
        from src.application.domen.models import LessonActivity

        data = VALID_ACTIVITY_DATA.copy()
        data['num_tickets'] = num_tickets
        return LessonActivity(**data)

    @staticmethod
    def create_activity_without_time():
        """Создать активность без указанного времени."""
        from src.application.domen.models import LessonActivity

        data = VALID_ACTIVITY_DATA.copy()
        data['time'] = None
        return LessonActivity(**data)


# Тестовые данные для Google Sheets
SHEET_HEADERS = [
    'Имя',
    'Фамилия',
    'Телефон',
    'Тема',
    'Дата',
    'Время',
    'Количество билетов',
]

SHEET_ROW_DATA = {
    'Имя': 'Иван',
    'Фамилия': 'Иванов',
    'Телефон': '+79001234567',
    'Тема': 'Урок рисования',
    'Дата': '01.12.2024',
    'Время': '14:00',
    'Количество билетов': '2',
}


class SheetFixtures:
    """Класс с фабриками данных для Google Sheets."""

    @staticmethod
    def create_worksheet_mock():
        """Создать mock для Google Sheets worksheet."""
        from unittest.mock import MagicMock

        worksheet = MagicMock()
        worksheet.row_values = MagicMock(return_value=SHEET_HEADERS)
        worksheet.find = MagicMock(return_value=MagicMock(col=1))
        worksheet.update_cell = MagicMock()
        worksheet.insert_row = MagicMock(return_value={'updates': {'updatedRange': 'A1'}})
        worksheet.batch_update = MagicMock()
        worksheet.get_all_values = MagicMock(return_value=[SHEET_HEADERS])
        return worksheet

    @staticmethod
    def create_signup_row_data(user: UserDTO, activity_data: dict) -> dict:
        """Создать данные для строки в таблице записи."""
        return {
            'Имя': user.name,
            'Фамилия': user.last_name,
            'Телефон': str(user.phone),
            'Тема': activity_data.get('topic', ''),
            'Дата': activity_data.get('date', ''),
            'Время': activity_data.get('time', ''),
            'Количество билетов': str(activity_data.get('num_tickets', 1)),
        }
