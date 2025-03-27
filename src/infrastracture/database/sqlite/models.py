from enum import StrEnum

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.application.domen.text import ru
from src.infrastracture.database.sqlite.db import Base


class ActivityTypeEnum(StrEnum):
    MASTERCLASS = ru.mass_class
    LESSON = ru.lesson
    KIDS_STUDIO = ru.child_studio
    EVENING_SKETCH = ru.evening_sketch


class ActivityType(Base):
    __tablename__ = "activity_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    activities: Mapped[list["Activity"]] = relationship(
        "Activity", back_populates="activity_type"
    )

    def __repr__(self):
        return f"<ActivityType(id={self.id}, name='{self.name}')>"


# Модель для таблицы пользователей
class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    theme: Mapped[str] = mapped_column(String)
    file_id: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String)

    type_id: Mapped[int] = mapped_column(
        ForeignKey("activity_types.id"), nullable=False
    )
    activity_type: Mapped["ActivityType"] = relationship(
        "ActivityType", back_populates="activities"
    )

    @validates("activity_type")
    def validate_activity_type(self, key, activity_type):
        if not any(activity_type.name == t.value for t in ActivityTypeEnum):
            raise ValueError("Invalid activity type")
        return activity_type
