# core/db/tinydb.py — TinyDB драйвер
"""
Реализация Database для TinyDB.
JSON-based БД без внешних зависимостей, идеально для Android/Termux.
"""

import shutil
from typing import Any, Dict, List, Union
from pathlib import Path

from .base import Database, DatabaseError


class TinyDBDatabase(Database):
    """
    TinyDB реализация базы данных.
    
    Хранит данные в JSON файле, каждый модуль = отдельная таблица.
    
    Attributes:
        _path: Путь к JSON файлу
        _db: TinyDB instance
    """

    def __init__(self, path: Union[str, Path]):
        """
        Инициализация TinyDB.
        
        Args:
            path: Путь к JSON файлу базы данных
        """
        super().__init__()
        try:
            from tinydb import TinyDB, Query
        except ImportError:
            raise ImportError("tinydb не установлен. Установите: pip install tinydb")
        
        self._Query = Query
        self._path = str(path)
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        
        self._db = TinyDB(self._path)

    def get(self, module: str, variable: str, default: Any = None) -> Any:
        """Получает значение из таблицы."""
        table = self._db.table(module)
        data = table.get(self._Query().name == variable)
        return data["value"] if data else default

    def set(self, module: str, variable: str, value: Any) -> None:
        """Записывает значение в таблицу."""
        table = self._db.table(module)
        table.upsert({"name": variable, "value": value}, self._Query().name == variable)

    def remove(self, module: str, variable: str) -> None:
        """Удаляет переменную из таблицы."""
        table = self._db.table(module)
        table.remove(self._Query().name == variable)

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Получает все переменные таблицы."""
        table = self._db.table(module)
        return {entry["name"]: entry["value"] for entry in table.all()}

    def get_modules(self) -> List[str]:
        """Получает список всех таблиц."""
        return list(self._db.tables())

    def close(self) -> None:
        """Закрывает БД."""
        self._db.close()

    def backup(self, target_path: Union[str, Path]) -> None:
        """
        Создает копию JSON файла.
        
        Args:
            target_path: Путь для сохранения копии
        """
        try:
            self._db.close()
            shutil.copy(self._path, str(target_path))
            self._logger.info(f"TinyDB backup: {target_path}")
            from tinydb import TinyDB
            self._db = TinyDB(self._path)
        except Exception as e:
            raise DatabaseError(f"TinyDB backup failed: {e}") from e


__all__ = ["TinyDBDatabase"]
