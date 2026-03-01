# core/db/lmdb.py — LMDB драйвер
"""
Реализация Database для LMDB (Lightning Memory-Mapped Database).
Высокопроизводительная key-value БД, недоступна на Android.
"""

import json
import shutil
import threading
from typing import Any, Dict, List, Union
from pathlib import Path

from .base import Database, DatabaseError


class LMDBDatabase(Database):
    """
    LMDB реализация базы данных.
    
    Использует формат ключей: module:variable
    
    Attributes:
        _path: Путь к директории БД
        _env: lmdb.Environment
        _lock: threading.Lock для потокобезопасности
    """

    def __init__(self, path: Union[str, Path]):
        """
        Инициализация LMDB.
        
        Args:
            path: Путь к директории базы данных
        """
        super().__init__()
        try:
            import lmdb
        except ImportError:
            raise ImportError("lmdb не установлен. Установите: pip install lmdb")
        
        self._lmdb = lmdb
        self._path = str(path)
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        
        # map_size = 1 GB
        self._env = lmdb.open(self._path, map_size=10**9)
        self._lock = threading.Lock()

    def get(self, module: str, variable: str, default: Any = None) -> Any:
        """Получает значение из LMDB."""
        with self._env.begin() as txn:
            value = txn.get(f"{module}:{variable}".encode())
            if value is None:
                return default
            return json.loads(value)

    def set(self, module: str, variable: str, value: Any) -> None:
        """Записывает значение в LMDB."""
        with self._env.begin(write=True) as txn:
            txn.put(
                f"{module}:{variable}".encode(),
                json.dumps(value, ensure_ascii=False).encode()
            )

    def remove(self, module: str, variable: str) -> None:
        """Удаляет ключ из LMDB."""
        with self._env.begin(write=True) as txn:
            txn.delete(f"{module}:{variable}".encode())

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Получает все ключи модуля."""
        collection = {}
        prefix = f"{module}:".encode()
        with self._env.begin() as txn:
            cursor = txn.cursor()
            for key, value in cursor:
                if key.startswith(prefix):
                    var_name = key.decode().split(":", 1)[1]
                    collection[var_name] = json.loads(value)
        return collection

    def get_modules(self) -> List[str]:
        """Получает список всех модулей."""
        modules = set()
        with self._env.begin() as txn:
            cursor = txn.cursor()
            for key, _ in cursor:
                module = key.decode().split(":")[0]
                modules.add(module)
        return list(modules)

    def close(self) -> None:
        """Закрывает среду LMDB."""
        self._env.close()

    def backup(self, target_path: Union[str, Path]) -> None:
        """
        Создает копию директории БД.
        
        Args:
            target_path: Путь для сохранения копии
        """
        try:
            self._env.close()
            shutil.copytree(self._path, str(target_path))
            self._logger.info(f"LMDB backup: {target_path}")
            self._env = self._lmdb.open(self._path, map_size=10**9)
        except Exception as e:
            raise DatabaseError(f"LMDB backup failed: {e}") from e


__all__ = ["LMDBDatabase"]
