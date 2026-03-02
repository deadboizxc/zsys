# core/config — Configuration module for zsys projects
"""Unified configuration handling for all zsys projects.

``BaseConfig`` lives in ``zsys.core.config`` and should be imported from
there. This module re-exports it alongside helper functions, Pydantic
utilities, and shared constants.

⚠️ NOTE: BaseConfig is defined in zsys.core.config — import it from there!
   This module (zsys.config) provides helper functions and constants.

Components:
    - BaseConfig: Base configuration class (from zsys.core.config) ⭐
    - load_base_config: Helper to instantiate a config with optional .env loading
    - export_config_constants: Dump a config instance as UPPER_CASE constants dict
    - env: ``environs.Env`` instance for reading .env files directly
    - Field: Pydantic Field for annotating config fields
    - validator: Pydantic validator decorator

Usage — Option 1 (RECOMMENDED):
    from zsys.core.config import BaseConfig, Field

    class MyConfig(BaseConfig):
        my_token: str
        my_port: int = 8000

        class Config:
            env_prefix = "MYAPP_"

    config = MyConfig()
    # Automatically populated from MYAPP_MY_TOKEN, MYAPP_MY_PORT, and defaults

Usage — Option 2 (with load_base_config):
    from zsys.core.config import BaseConfig, Field
    from zsys.config import load_base_config

    class MyConfig(BaseConfig):
        token: str

    config = load_base_config(MyConfig, env_file=Path(".env"))

Usage — Option 3 (low-level env access):
    from zsys.config import env, load_env

    load_env(".env")
    db_type = env.str("DB_TYPE", default="sqlite")
    debug = env.bool("DEBUG", default=False)
"""
# RU: Унифицированная работа с конфигурацией для всех проектов zsys.
# RU: BaseConfig находится в zsys.core.config — импортировать оттуда!
# RU: Этот модуль предоставляет вспомогательные функции и константы.

from typing import Optional, Type
from pathlib import Path

from .env import env, load_env, get_env_path

# Import BaseConfig from core - this is the single source of truth
from zsys.core.config import BaseConfig

def load_base_config(
    config_class: type,
    env_file: Optional[Path] = None,
    env_prefix: Optional[str] = None
) -> BaseConfig:
    """Instantiate a BaseConfig subclass, optionally loading a .env file first.

    Args:
        config_class: Config class to instantiate (must subclass ``BaseConfig``).
        env_file: Path to a ``.env`` file. If ``None``, no file is loaded and
            the config is populated solely from the current environment.
        env_prefix: Env-variable prefix override. If ``None``, the prefix
            defined on ``config_class.Config.env_prefix`` is used.

    Returns:
        Populated instance of ``config_class``.

    Raises:
        ValueError: When required fields are absent or validation fails.

    Example:
        config = load_base_config(MyConfig)
        config = load_base_config(MyConfig, env_file=Path("custom.env"))
    """
    # RU: Загружает .env файл (если указан) и создаёт экземпляр конфига.
    # RU: Если файл не существует — молча продолжает (переменные могут
    # RU: быть уже установлены в окружении).

    # Load .env file if provided
    if env_file is not None:
        if env_file.exists():
            load_env(env_file)
        # If doesn't exist, silently continue (might have env vars set)

    # Create config instance
    try:
        config = config_class()
        return config
    except Exception as e:
        # RU: Оборачиваем исключение Pydantic в ValueError с именем класса.
        raise ValueError(f"Failed to load {config_class.__name__}: {e}")


def export_config_constants(config: BaseConfig) -> dict:
    """Serialize a config instance as a dict of UPPER_CASE constant names.

    Converts every field name from ``snake_case`` to ``UPPER_CASE`` so the
    result can be unpacked as module-level constants for backward
    compatibility with codebases that expect ``TOKEN``, ``OWNER_ID``, etc.

    Args:
        config: Populated ``BaseConfig`` instance to export.

    Returns:
        Mapping of ``UPPER_CASE_FIELD_NAME`` → field value for every field
        declared on the config.

    Example:
        constants = export_config_constants(config)
        # {'TOKEN': '...', 'OWNER_ID': 123}
    """
    # RU: Экспортирует поля конфига как UPPER_CASE константы для обратной совместимости.

    result = {}
    for field_name, field_value in config.dict().items():
        # RU: Конвертируем snake_case в UPPER_CASE для совместимости.
        const_name = field_name.upper()
        result[const_name] = field_value
    return result


# Import constants
from .constants import (
    ENV_FILE_NAME, DB_DEFAULT_NAME, SESSION_DEFAULT_NAME,
    BOT_CONFIG_FILE_NAME, CONFIG_FILE_NAME,
    USERDATA_DIR, LOGS_DIR, CACHE_DIR, TEMP_DIR,
    DB_TIMEOUT, DB_POOL_SIZE,
    HTTP_TIMEOUT, HTTP_MAX_RETRIES, HTTP_RETRY_DELAY,
    LOG_MAX_SIZE, LOG_BACKUP_COUNT, LOG_FORMAT,
)

# Export Pydantic utilities for convenience
try:
    from pydantic import Field, validator, root_validator
    _HAS_ROOT_VALIDATOR = True
except ImportError:
    from pydantic import Field, validator
    root_validator = None  # type: ignore
    _HAS_ROOT_VALIDATOR = False

# Build __all__ list based on available imports
if _HAS_ROOT_VALIDATOR:
    __all__ = [
        # Core config
        "env",
        "load_env",
        "get_env_path",
        "BaseConfig",
        "load_base_config",
        "export_config_constants",
        # Pydantic utilities
        "Field",
        "validator",
        "root_validator",
        # Constants
        "ENV_FILE_NAME",
        "DB_DEFAULT_NAME",
        "SESSION_DEFAULT_NAME",
        "BOT_CONFIG_FILE_NAME",
        "CONFIG_FILE_NAME",
        "USERDATA_DIR",
        "LOGS_DIR",
        "CACHE_DIR",
        "TEMP_DIR",
        "DB_TIMEOUT",
        "DB_POOL_SIZE",
        "HTTP_TIMEOUT",
        "HTTP_MAX_RETRIES",
        "HTTP_RETRY_DELAY",
        "LOG_MAX_SIZE",
        "LOG_BACKUP_COUNT",
        "LOG_FORMAT",
    ]
else:
    __all__ = [
        # Core config
        "env",
        "load_env",
        "get_env_path",
        "BaseConfig",
        "load_base_config",
        "export_config_constants",
        # Pydantic utilities
        "Field",
        "validator",
        # Constants
        "ENV_FILE_NAME",
        "DB_DEFAULT_NAME",
        "SESSION_DEFAULT_NAME",
        "BOT_CONFIG_FILE_NAME",
        "CONFIG_FILE_NAME",
        "USERDATA_DIR",
        "LOGS_DIR",
        "CACHE_DIR",
        "TEMP_DIR",
        "DB_TIMEOUT",
        "DB_POOL_SIZE",
        "HTTP_TIMEOUT",
        "HTTP_MAX_RETRIES",
        "HTTP_RETRY_DELAY",
        "LOG_MAX_SIZE",
        "LOG_BACKUP_COUNT",
        "LOG_FORMAT",
    ]
