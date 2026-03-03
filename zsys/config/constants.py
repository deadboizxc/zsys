"""Universal configuration constants for the zsys ecosystem.

Defines immutable default values for file names, directory names, database
settings, HTTP parameters, and logging options shared across all projects.
Project-specific constants should be defined in their own config files.
"""
# RU: Универсальные константы конфигурации для экосистемы zsys.
# RU: Определяет неизменяемые значения по умолчанию для имён файлов,
# RU: директорий, БД, HTTP и логирования. Проектные константы —
# RU: в собственных конфиг-файлах проекта.

from typing import Final

# =============================================================================
# FILE NAMES
# =============================================================================

ENV_FILE_NAME: Final[str] = ".env"
"""Default environment file name."""

DB_DEFAULT_NAME: Final[str] = "db"
"""Default database name (used when not specified otherwise)."""

SESSION_DEFAULT_NAME: Final[str] = "session"
"""Default session file name for Pyrogram/Telethon."""

BOT_CONFIG_FILE_NAME: Final[str] = "bots.json"
"""Default bot configuration file name."""

CONFIG_FILE_NAME: Final[str] = "config.json"
"""Default configuration file name."""

# =============================================================================
# DIRECTORIES
# =============================================================================

USERDATA_DIR: Final[str] = "userdata"
"""Default userdata directory name."""

LOGS_DIR: Final[str] = "logs"
"""Default logs directory name."""

CACHE_DIR: Final[str] = "cache"
"""Default cache directory name."""

TEMP_DIR: Final[str] = "temp"
"""Default temporary directory name."""

# =============================================================================
# DATABASE DEFAULTS
# =============================================================================

DB_TIMEOUT: Final[int] = 30
"""Default database connection timeout in seconds."""

DB_POOL_SIZE: Final[int] = 5
"""Default database connection pool size."""

# =============================================================================
# HTTP DEFAULTS
# =============================================================================

HTTP_TIMEOUT: Final[int] = 30
"""Default HTTP request timeout in seconds."""

HTTP_MAX_RETRIES: Final[int] = 3
"""Default maximum number of HTTP retries."""

HTTP_RETRY_DELAY: Final[float] = 1.0
"""Default delay between HTTP retries in seconds."""

# =============================================================================
# LOGGING DEFAULTS
# =============================================================================

LOG_MAX_SIZE: Final[int] = 10 * 1024 * 1024  # 10 MB
"""Default maximum log file size in bytes."""

LOG_BACKUP_COUNT: Final[int] = 5
"""Default number of log backup files to keep."""

LOG_FORMAT: Final[str] = "[%(asctime)s] %(levelname)s - %(message)s"
"""Default log message format."""

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # File names
    "ENV_FILE_NAME",
    "DB_DEFAULT_NAME",
    "SESSION_DEFAULT_NAME",
    "BOT_CONFIG_FILE_NAME",
    "CONFIG_FILE_NAME",
    # Directories
    "USERDATA_DIR",
    "LOGS_DIR",
    "CACHE_DIR",
    "TEMP_DIR",
    # Database
    "DB_TIMEOUT",
    "DB_POOL_SIZE",
    # HTTP
    "HTTP_TIMEOUT",
    "HTTP_MAX_RETRIES",
    "HTTP_RETRY_DELAY",
    # Logging
    "LOG_MAX_SIZE",
    "LOG_BACKUP_COUNT",
    "LOG_FORMAT",
]
