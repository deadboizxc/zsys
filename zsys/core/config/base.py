"""BaseConfig — universal Pydantic-based configuration base class.

All ZSYS project configurations inherit from this class, which provides
type-safe field validation, automatic environment variable loading,
.env file support, and a ``from_env()`` factory method.
"""
# RU: BaseConfig — универсальный базовый класс конфигурации на Pydantic.
# RU: Все конфигурации ZSYS наследуют его; поддержка .env и переменных окружения.

from typing import Any, Optional
from pydantic import BaseModel, Field
from pathlib import Path
import os


class BaseConfig(BaseModel):
    """Universal base configuration for all ZSYS projects.

    Subclass this to create type-safe, validated configuration objects
    that load values from environment variables and .env files automatically.

    Features:
        - Type-safe fields validated by Pydantic v2.
        - Automatic environment variable mapping (case-insensitive).
        - ``.env`` file loading via Pydantic settings.
        - ``from_env()`` factory for explicit .env file paths.

    Example::

        class MyBotConfig(BaseConfig):
            token: str
            api_id: int

            class Config:
                env_prefix = "BOT_"

        config = MyBotConfig()
        # Reads BOT_TOKEN and BOT_API_ID from the environment.

    Attributes:
        app_name: Application display name (default ``"ZSYS"``).
        debug: Enable debug mode; increases log verbosity.
        log_level: Minimum log level string; must be one of DEBUG/INFO/WARNING/ERROR/CRITICAL.
        work_dir: Working directory path (defaults to the current directory).
    """
    # RU: Универсальный базовый класс конфигурации ZSYS на Pydantic.

    # === Common fields ===

    app_name: str = Field(
        default="ZSYS",
        description="Application name"
    )

    debug: bool = Field(
        default=False,
        description="Debug mode"
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )

    work_dir: Path = Field(
        default_factory=lambda: Path.cwd(),
        description="Working directory"
    )

    class Config:
        """Pydantic model configuration."""
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"
        validate_assignment = True
        arbitrary_types_allowed = True

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "BaseConfig":
        """Load configuration from environment variables and an optional .env file.

        Args:
            env_file: Path to a ``.env`` file to load before reading the environment.
                If None or the file does not exist, only environment variables are used.

        Returns:
            Populated and validated configuration instance.
        """
        # RU: Загрузить конфигурацию из переменных окружения и опционального .env-файла.
        if env_file and os.path.exists(env_file):
            return cls(_env_file=env_file)
        return cls()
