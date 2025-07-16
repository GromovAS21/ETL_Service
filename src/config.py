import logging
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

JOBS_DIR = Path(__file__).parent.parent / "jobs"


class MainDatabaseSettings(BaseSettings):
    """Настройки подключения к основной базе данных."""
    model_config = SettingsConfigDict(
        env_prefix="MAIN_DB_",
        env_file=(".env",),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    host: str = Field(...)
    port: int = Field(...)
    user: str = Field(...)
    password: str = Field(...)
    database: str = Field(...)

    @property
    def connection_url(self) -> str:
        """Возвращает строку подключения к основной базе данных."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class AnalyticDatabaseSettings(BaseSettings):
    """Настройки подключения к аналитической базе данных."""
    model_config = SettingsConfigDict(
        env_prefix="ANALYTIC_DB_",
        env_file=(".env",),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    host: str = Field(...)
    port: int = Field(...)
    user: str = Field(...)
    password: str = Field(...)
    database: str = Field(...)

    @property
    def connection_url(self) -> str:
        """Возвращает строку подключения к аналитической базе данных."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisConfig(BaseSettings):
    """Настройки подключения к Redis."""
    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=(".env",),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    host: str = Field(...)
    port: int = Field(...)
    username: str | None = Field(None)
    password: str | None = Field(None)

    @property
    def connection_url(self) -> str:
        """Возвращает строку подключения к Redis."""
        if self.username and self.password:
            return f"redis://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"redis://{self.host}:{self.port}"


class LogSettings(BaseSettings):
    """Настройки логирования."""

    base_dir: Path = Path(__file__).parent.parent
    level: int = logging.INFO
    log_format: str = '%(asctime)s %(levelname)s %(message)s'
    file: Path = base_dir / "logs" / "app.log"


class Settings(BaseSettings):
    """Настройки приложения."""
    main_database: MainDatabaseSettings = MainDatabaseSettings()
    analytic_database: AnalyticDatabaseSettings = AnalyticDatabaseSettings()
    redis: RedisConfig = RedisConfig()
    log: LogSettings = LogSettings()


settings = Settings()
