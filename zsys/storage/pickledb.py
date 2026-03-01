# core/db/pickledb.py — PickleDB драйвер
"""
Реализация Database для PickleDB.
Простая pickle-based key-value БД.
"""

import shutil
from typing import Any, Dict, List, Union
from pathlib import Path

from .base import Database, DatabaseError


class PickleDBDatabase(Database):
    """
    PickleDB реализация базы данных.
    
    Использует формат ключей: module:variable
    
    Attributes:
        _path: Путь к pickle файлу
        _db: PickleDB instance
    """

    def __init__(self, path: Union[str, Path]):
        """
        Инициализация PickleDB.
        
        Args:
            path: Путь к pickle файлу базы данных
        """
        super().__init__()
        try:
            from pickledb import PickleDB
        except ImportError:
            raise ImportError("pickledb не установлен. Установите: pip install pickledb")
        
        self._path = str(path)
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            self._db = PickleDB(self._path)
        except Exception as e:
            raise DatabaseError(f"Не удалось открыть PickleDB: {e}") from e

    def get(self, module: str, variable: str, default: Any = None) -> Any:
        """Получает значение из БД."""
        key = f"{module}:{variable}"
        value = self._db.get(key)
        return default if value is None else value

    def set(self, module: str, variable: str, value: Any) -> None:
        """Записывает значение в БД."""
        key = f"{module}:{variable}"
        self._db.set(key, value)
        self._db.save()

    def remove(self, module: str, variable: str) -> None:
        """Удаляет ключ из БД."""
        key = f"{module}:{variable}"
        self._db.remove(key)
        self._db.save()

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Получает все ключи модуля."""
        result = {}
        prefix = f"{module}:"
        for key in self._db.all():
            if key.startswith(prefix):
                var_name = key.split(":", 1)[1]
                result[var_name] = self._db.get(key)
        return result

    def get_modules(self) -> List[str]:
        """Получает список всех модулей."""
        modules = set()
        for key in self._db.all():
            if ":" in key:
                module = key.split(":", 1)[0]
                modules.add(module)
        return list(modules)

    def close(self) -> None:
        """Сохраняет и закрывает БД."""
        self._db.save()

    def backup(self, target_path: Union[str, Path]) -> None:
        """
        Создает копию pickle файла.
        
        Args:
            target_path: Путь для сохранения копии
        """
        try:
            self._db.save()
            shutil.copy(self._path, str(target_path))
            self._logger.info(f"PickleDB backup: {target_path}")
        except Exception as e:
            raise DatabaseError(f"PickleDB backup failed: {e}") from e


__all__ = ["PickleDBDatabase"]
