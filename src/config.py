import base64

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic import Field
from pydantic import SecretStr
from pydantic import field_serializer
from pydantic import model_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class GoogleSettings(BaseModel):
    type: str
    project_id: str
    private_key_id: SecretStr
    private_key: SecretStr
    client_email: str
    client_id: str
    auth_uri: SecretStr
    token_uri: SecretStr
    auth_provider_x509_cert_url: str
    client_x509_cert_url: str
    universe_domain: str

    @field_serializer(
        'private_key_id', 'private_key', 'auth_uri', 'token_uri', when_used='always'
    )
    def dump_secret(self, v) -> Any:
        return v.get_secret_value()


class Config(BaseSettings):
    # Желательно вместо str использовать SecretStr
    # для конфиденциальных данных, например, токена бота
    LOCAL: bool = Field(default=False)

    bot_token: SecretStr
    DEVELOPER_ID: int
    GSHEET_NAME: str = Field(default='КАМЕЯ.Арт-Студия')
    LESSONS_PAGE: str = Field(default='уроки')
    CHILD_PAGE: str = Field(default='детская студия')
    MASTER_CL_PAGE: str = Field(default='мастер-классы')
    EVENING_PAGE: str = Field(default='вечерние наброски')

    REDIS_PASSWORD: SecretStr
    REDIS_HOST: str = Field(default='redis')
    REDIS_PORT: int
    users_cache_time: int = Field(default=60 * 60)
    admins: list[int]
    # welcome images/videos
    static_data_path: Path = Path('static_data')

    @property
    def welcome_image_path(self) -> Path:
        return self.static_data_path / 'welcome_photo.jpg'

    @property
    def welcome_video_path(self) -> Path:
        return self.static_data_path / 'welcome_video.mp4'

    @property
    def how_to_video_path(self) -> Path:
        return self.static_data_path / 'how_to.mp4'

    @property
    def about_video_path(self) -> Path:
        return self.static_data_path / 'about.mp4'

    @property
    def first_photo_path(self) -> Path:
        return self.static_data_path / 'first_seen.jpg'

    DB_PATH: str = '/sqlite_data/kamey_art.db'

    @property
    def db_url(self) -> str:
        return f'sqlite+aiosqlite://{self.DB_PATH}'

    GOOGLE_SETTINGS: str  # Base64 encoded GoogleSettings json string

    @property
    def google_settings(self) -> GoogleSettings:
        return GoogleSettings.model_validate_json(
            base64.b64decode(self.GOOGLE_SETTINGS).decode('utf-8')
        )

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    @model_validator(mode='after')
    def admins_setter(self) -> 'Config':
        if self.LOCAL:
            self.admins = [self.DEVELOPER_ID]
        elif self.DEVELOPER_ID not in self.admins:
            self.admins.append(self.DEVELOPER_ID)
        return self


@lru_cache
def get_config() -> Config:
    return Config()
