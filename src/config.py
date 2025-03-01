from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    # Желательно вместо str использовать SecretStr
    # для конфиденциальных данных, например, токена бота
    bot_token: SecretStr
    ADMIN_ID: str
    SERVICE_FILE_NAME: str
    GSHEET_NAME: str
    users_page: str = Field(default="users")
    lessons_page: str = Field(default="уроки")
    child_page: str = Field(default="детскаястудия")
    master_class_page: str = Field(default="мастер-классы")
    evening_page: str = Field(default="вечерние наброски")

    REDIS_PASSWORD: SecretStr
    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int

    # Начиная со второй версии pydantic, настройки класса настроек задаются
    # через model_config
    # В данном случае будет использоваться файла .env, который будет прочитан
    # с кодировкой UTF-8
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# При импорте файла сразу создастся
# и провалидируется объект конфига,
# который можно далее импортировать из разных мест


@lru_cache
def get_config() -> Config:
    return Config()
