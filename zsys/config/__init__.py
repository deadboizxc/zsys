# core/config — Модуль конфигурации
"""
Унифицированная работа с конфигурацией для всех проектов zsys.

⚠️ ВАЖНО: BaseConfig находится в zsys.core.config и импортируется оттуда!
   Этот модуль (zsys.config) предоставляет вспомогательные функции и константы.

Компоненты:
    - BaseConfig: Базовый класс конфигурации (из zsys.core.config) ⭐
    - load_base_config: Функция загрузки конфига с .env
    - export_config_constants: Экспорт конфига как констант
    - env: environs.Env экземпляр для чтения .env файлов
    - Field: Pydantic Field для документирования полей
    - validator: Pydantic validator для валидации

Использование - Вариант 1 (РЕКОМЕНДУЕТСЯ):
    from zsys.core.config import BaseConfig, Field
    
    class MyConfig(BaseConfig):
        my_token: str
        my_port: int = 8000
        
        class Config:
            env_prefix = "MYAPP_"
    
    config = MyConfig()
    # Автоматически загружает из MYAPP_MY_TOKEN, MYAPP_MY_PORT и дефолтов

Использование - Вариант 2 (с load_base_config):
    from zsys.core.config import BaseConfig, Field
    from zsys.config import load_base_config
    
    class MyConfig(BaseConfig):
        token: str
    
    config = load_base_config(MyConfig, env_file=Path(".env"))

Использование - Вариант 3 (для сложных случаев):
    from zsys.config import env, load_env
    
    load_env(".env")
    db_type = env.str("DB_TYPE", default="sqlite")
    debug = env.bool("DEBUG", default=False)
"""

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
    """
    Unified config loading function.
    
    USAGE:
        from zsys.core.config import BaseConfig, Field
        from zsys.config import load_base_config
        
        class MyConfig(BaseConfig):
            token: str
            
            class Config:
                env_prefix = "MYAPP_"
        
        # Option 1: Auto-load from .env in current directory
        config = load_base_config(MyConfig)
        
        # Option 2: Specify exact .env path
        config = load_base_config(MyConfig, env_file=Path("custom.env"))
        
        # Option 3: Just load environment variables
        config = load_base_config(MyConfig, env_file=None)
    
    Args:
        config_class: Your config class (must inherit from BaseConfig)
        env_file: Path to .env file (optional). If None, doesn't load file.
        env_prefix: env_prefix to use (optional). If None, uses class Config.env_prefix
    
    Returns:
        Instance of config_class with values loaded from environment
    
    Raises:
        ValueError: If required fields are missing
    """
    
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
        raise ValueError(f"Failed to load {config_class.__name__}: {e}")


def export_config_constants(config: BaseConfig) -> dict:
    """
    Export config as module-level constants for backward compatibility.
    
    USAGE:
        from zsys.core.config import BaseConfig, Field
        from zsys.config import export_config_constants
        
        class MyBotConfig(BaseConfig):
            token: str
            owner_id: int
            
            class Config:
                env_prefix = "MYBOT_"
        
        config = MyBotConfig()
        
        # Export as module-level constants
        TOKEN = config.token
        OWNER_ID = config.owner_id
        
        # Or use helper:
        constants = export_config_constants(config)
        # constants = {'token': '...', 'owner_id': 123}
    
    Args:
        config: BaseConfig instance
    
    Returns:
        Dictionary with field_name -> field_value
    """
    
    result = {}
    for field_name, field_value in config.dict().items():
        # Convert snake_case to UPPER_CASE
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
