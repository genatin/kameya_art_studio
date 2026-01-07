from src.config import Config

_temp_db_path = "tests/kamey_art_test.db"

with open(_temp_db_path, "w") as f:
    pass  # Create an empty file


class TestConfig(Config):
    """Настройки для тестов."""

    @property
    def db_url(self) -> str:
        """URL для тестовой БД."""
        return f"sqlite+aiosqlite:///{_temp_db_path}"

    def cleanup(self):
        """Очистка временных файлов."""
        # if os.path.exists(_temp_db_path):
        #     os.unlink(_temp_db_path)


def get_test_config() -> TestConfig:
    """Получить тестовую конфигурацию."""
    return TestConfig()
