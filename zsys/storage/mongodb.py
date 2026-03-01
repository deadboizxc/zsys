# core/db/mongodb.py — MongoDB драйвер
"""
Реализация Database для MongoDB.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Union

from .base import Database, DatabaseError


class MongoDatabase(Database):
    """
    MongoDB реализация базы данных.
    
    Attributes:
        _client: pymongo.MongoClient
        _database: Экземпляр базы данных MongoDB
    """

    def __init__(self, url: str, db_name: str):
        """
        Инициализация MongoDB.
        
        Args:
            url: URL подключения (mongodb://localhost:27017)
            db_name: Имя базы данных
        """
        super().__init__()
        try:
            import pymongo
        except ImportError:
            raise ImportError("pymongo не установлен. Установите: pip install pymongo")
        
        self._client = pymongo.MongoClient(url)
        self._database = self._client[db_name]

    def get(self, module: str, variable: str, default: Any = None) -> Any:
        """Получает значение из коллекции."""
        doc = self._database[module].find_one({"var": variable})
        return default if doc is None else doc["val"]

    def set(self, module: str, variable: str, value: Any) -> None:
        """Записывает значение в коллекцию."""
        self._database[module].replace_one(
            {"var": variable},
            {"var": variable, "val": value},
            upsert=True
        )

    def remove(self, module: str, variable: str) -> None:
        """Удаляет документ из коллекции."""
        self._database[module].delete_one({"var": variable})

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Получает все документы коллекции."""
        return {item["var"]: item["val"] for item in self._database[module].find()}

    def get_modules(self) -> List[str]:
        """Получает список всех коллекций."""
        return self._database.list_collection_names()

    def close(self) -> None:
        """Закрывает соединение."""
        self._client.close()

    def backup(self, target_path: str) -> None:
        """
        Создает JSON backup базы данных.
        
        Args:
            target_path: Директория для сохранения
        """
        try:
            from pathlib import Path
            data = {}
            for collection in self._database.list_collection_names():
                data[collection] = list(self._database[collection].find({}, {"_id": 0}))
            
            backup_file = Path(target_path) / f"mongodb_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self._logger.info(f"MongoDB backup: {backup_file}")
        except Exception as e:
            raise DatabaseError(f"MongoDB backup failed: {e}") from e


__all__ = ["MongoDatabase"]
