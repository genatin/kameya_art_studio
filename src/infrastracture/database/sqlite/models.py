from datetime import datetime
from enum import StrEnum

from aiogram.types import ContentType
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.application.domen.text import RU
from src.infrastracture.database.sqlite.db import Base


class ActivityTypeEnum(StrEnum):
    MASTERCLASS = RU.mass_class
    LESSON = RU.lesson
    KIDS_STUDIO = RU.child_studio
    EVENING_SKETCH = RU.evening_sketch


class ActivityType(Base):
    __tablename__ = 'activity_types'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    activities: Mapped[list['Activity']] = relationship(
        'Activity', back_populates='activity_type', cascade='all, delete'
    )

    def __repr__(self) -> str:
        return f"<ActivityType(id={self.id}, name='{self.name}')>"


# Модель для таблицы пользователей
class Activity(Base):
    __tablename__ = 'activities'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    theme: Mapped[str] = mapped_column(String)
    file_id: Mapped[str] = mapped_column(String, nullable=True)
    content_type: Mapped[str | None] = mapped_column(
        String, nullable=True, server_default=ContentType.PHOTO
    )
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    date_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    type_id: Mapped[int] = mapped_column(ForeignKey('activity_types.id'), nullable=False)
    activity_type: Mapped['ActivityType'] = relationship(
        'ActivityType', back_populates='activities'
    )


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nickname: Mapped[str] = mapped_column(String, nullable=True)
    phone: Mapped[str] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    last_name: Mapped[str] = mapped_column(String, nullable=True)
