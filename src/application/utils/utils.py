from datetime import date


def format_date_russian(dt: date) -> str:
    weekdays = [
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
        "Суббота",
        "Воскресенье",
    ]
    months = [
        "Января",
        "Февраля",
        "Марта",
        "Апреля",
        "Мая",
        "Июня",
        "Июля",
        "Фвгуста",
        "Сентября",
        "Октября",
        "Ноября",
        "Декабря",
    ]
    return f"{weekdays[dt.weekday()]}, {dt.day} {months[dt.month - 1]} {dt.year}"
