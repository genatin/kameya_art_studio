from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    # Желательно вместо str использовать SecretStr
    # для конфиденциальных данных, например, токена бота
    LOCAL: bool = Field(default=False)

    bot_token: SecretStr
    DEVELOPER_ID: str
    SERVICE_FILE_NAME: str
    GSHEET_NAME: str
    USERS_PAGE: str = Field(default="users")
    LESSONS_PAGE: str = Field(default="уроки")
    CHILD_PAGE: str = Field(default="детская студия")
    MASTER_CL_PAGE: str = Field(default="мастер-классы")
    EVENING_PAGE: str = Field(default="вечерние наброски")

    REDIS_PASSWORD: SecretStr
    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int
    users_cache_time: int = Field(default=60 * 60)
    ADMINS: list[int]
    # welcome images/videos
    STATIC_DATA: Path = Path("static_data")
    WELCOME_IMAGE_PATH: Path = STATIC_DATA / Path("welcome_photo.jpg")
    WELCOME_VIDEO_PATH: Path = STATIC_DATA / Path("welcome_video.mp4")

    DB_PATH: Path = "/sqlite_data/kamey_art.db"  # Храним БД в volume

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# При импорте файла сразу создастся
# и провалидируется объект конфига,
# который можно далее импортировать из разных мест


@lru_cache
def get_config() -> Config:
    return Config()
