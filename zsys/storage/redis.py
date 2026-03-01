# core/db/redis.py — Redis драйвер
"""
Реализация Database для Redis.
"""

import json
import threading
from datetime import datetime
from typing import Any, Dict, List, Union

from .base import Database, DatabaseError


class RedisDatabase(Database):
    """
    Redis реализация базы данных.
    
    Использует формат ключей: module:variable
    
    Attributes:
        _client: redis.Redis клиент
        _lock: threading.Lock для потокобезопасности
    """

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """
        Инициализация Redis.
        
        Args:
            host: Хост сервера Redis
            port: Порт сервера Redis
            db: Номер базы данных Redis
        """
        super().__init__()
        try:
            import redis
        except ImportError:
            raise ImportError("redis не установлен. Установите: pip install redis")
        
        self._client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self._lock = threading.Lock()

    def get(self, module: str, variable: str, default: Any = None) -> Any:
        """Получает значение из Redis."""
        key = f"{module}:{variable}"
        value = self._client.get(key)
        if value is None:
            return default
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    def set(self, module: str, variable: str, value: Any) -> None:
        """Записывает значение в Redis."""
        key = f"{module}:{variable}"
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        elif isinstance(value, bool):
            value = "1" if value else "0"
        elif not isinstance(value, str):
            value = str(value)
        self._client.set(key, value)

    def remove(self, module: str, variable: str) -> None:
        """Удаляет ключ из Redis."""
        key = f"{module}:{variable}"
        self._client.delete(key)

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Получает все ключи модуля."""
        collection = {}
        keys = self._client.keys(f"{module}:*")
        for key in keys:
            variable = key.split(":", 1)[1]
            value = self._client.get(key)
            try:
                collection[variable] = json.loads(value)
            except json.JSONDecodeError:
                collection[variable] = value
        return collection

    def get_modules(self) -> List[str]:
        """Получает список всех модулей."""
        modules = set()
        for key in self._client.keys("*"):
            if ":" in key:
                module = key.split(":")[0]
                modules.add(module)
        return list(modules)

    def close(self) -> None:
        """Закрывает соединение с Redis."""
        self._client.close()

    def backup(self, target_path: str) -> None:
        """
        Создает JSON backup всех данных.
        
        Args:
            target_path: Директория для сохранения
        """
        try:
            from pathlib import Path
            data = {}
            for module in self.get_modules():
                data[module] = self.get_collection(module)
            
            backup_file = Path(target_path) / f"redis_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self._logger.info(f"Redis backup: {backup_file}")
        except Exception as e:
            raise DatabaseError(f"Redis backup failed: {e}") from e


__all__ = ["RedisDatabase"]
