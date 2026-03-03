# core/config/env.py — Environment variable helpers
"""Thin wrapper around environs for unified .env file handling.

Provides a shared ``Env`` instance and helper functions to locate and
load ``.env`` files, normalising path resolution across all zsys projects.
"""
# RU: Обёртка над environs для унифицированной работы с .env файлами.
# RU: Предоставляет глобальный экземпляр Env и вспомогательные функции
# RU: для поиска и загрузки .env файлов.

from pathlib import Path
from typing import Optional, Union

import environs

# Global Env instance shared across the application.
# RU: Глобальный экземпляр Env, используемый во всём приложении.
env = environs.Env()


def load_env(
    env_path: Optional[Union[str, Path]] = None, override: bool = False
) -> bool:
    """Load environment variables from a .env file.

    Args:
        env_path: Path to the ``.env`` file. If ``None``, defaults to
            ``.env`` in the current working directory.
        override: When ``True``, overwrite variables that are already set
            in the process environment.

    Returns:
        ``True`` if the file was found and loaded; ``False`` if it does
        not exist.

    Example:
        load_env("config/.env")
        load_env(Path("userdata") / ".env", override=True)
    """
    # RU: Загружает переменные окружения из .env файла.
    # RU: Если env_path не указан, ищет .env в текущей директории.
    # RU: Возвращает True при успехе, False если файл не существует.
    if env_path is None:
        # RU: По умолчанию ищем .env в текущей рабочей директории.
        env_path = Path.cwd() / ".env"

    path = Path(env_path)

    if not path.exists():
        return False

    env.read_env(str(path), override=override)
    return True


def get_env_path(
    filename: str = ".env", search_dirs: Optional[list] = None
) -> Optional[Path]:
    """Search for an env file across a list of candidate directories.

    Args:
        filename: Name of the file to look for.
        search_dirs: Ordered list of directories to search. Defaults to
            the current working directory, ``userdata/``, and ``config/``
            subdirectories.

    Returns:
        ``Path`` to the first matching file, or ``None`` if not found.
    """
    # RU: Ищет .env файл в указанных директориях.
    # RU: Возвращает путь к первому найденному файлу или None.
    if search_dirs is None:
        # RU: Список директорий по умолчанию: cwd, userdata, config.
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
