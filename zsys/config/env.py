# core/config/env.py — Работа с переменными окружения
"""
Обёртка над environs для унифицированной работы с .env файлами.

Использование:
    from core.config import env, load_env
    
    # Загрузить конкретный файл
    load_env("/path/to/.env")
    
    # Читать переменные
    db_type = env.str("DB_TYPE", default="sqlite")
    port = env.int("PORT", default=8000)
    debug = env.bool("DEBUG", default=False)
    hosts = env.list("ALLOWED_HOSTS", default=["localhost"])
"""

from pathlib import Path
from typing import Optional, Union

import environs

# Глобальный экземпляр Env
env = environs.Env()


def load_env(
    env_path: Optional[Union[str, Path]] = None,
    override: bool = False
) -> bool:
    """
    Загружает переменные окружения из .env файла.
    
    Args:
        env_path: Путь к .env файлу. Если None, ищет .env в текущей директории.
        override: Перезаписывать ли существующие переменные окружения.
    
    Returns:
        True если файл найден и загружен, False если файл не существует.
    
    Example:
        load_env("config/.env")
        load_env(Path("userdata") / ".env", override=True)
    """
    if env_path is None:
        env_path = Path.cwd() / ".env"
    
    path = Path(env_path)
    
    if not path.exists():
        return False
    
    env.read_env(str(path), override=override)
    return True


def get_env_path(
    filename: str = ".env",
    search_dirs: Optional[list] = None
) -> Optional[Path]:
    """
    Ищет .env файл в указанных директориях.
    
    Args:
        filename: Имя файла для поиска.
        search_dirs: Список директорий для поиска. По умолчанию: cwd, userdata.
    
    Returns:
        Путь к найденному файлу или None.
    """
    if search_dirs is None:
        search_dirs = [
            Path.cwd(),
            Path.cwd() / "userdata",
            Path.cwd() / "config",
        ]
    
    for dir_path in search_dirs:
        env_file = Path(dir_path) / filename
        if env_file.exists():
            return env_file
    
    return None


__all__ = [
    "env",
    "load_env",
    "get_env_path",
]
