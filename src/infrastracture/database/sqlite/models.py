from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastracture.database.sqlite.db import Base


# Модель для таблицы пользователей
class MClass(Base):
    __tablename__ = "mclass"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    file_id: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String)
