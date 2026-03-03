# core/db/mongodb.py — MongoDB драйвер
"""MongoDB storage backend — pymongo-based Database implementation.

Each module name maps to a distinct MongoDB collection.
Values are stored as documents with ``var``/``val`` fields and upserted
via ``replace_one`` so writes are idempotent.
"""
# RU: MongoDB бэкенд хранилища — реализация Database на основе pymongo.
# RU: Каждый модуль соответствует отдельной коллекции MongoDB.
# RU: Значения хранятся как документы с полями ``var``/``val``
# RU: и записываются через ``replace_one`` с upsert=True.

import json
from datetime import datetime
from typing import Any, Dict, List, Union

from .base import Database, DatabaseError


class MongoDatabase(Database):
    """MongoDB-backed implementation of the Database interface.

    Each module name is treated as a MongoDB collection name.
    Documents follow the schema ``{"var": <name>, "val": <value>}``
    and are upserted so repeated writes never create duplicates.

    Attributes:
        _client: Active ``pymongo.MongoClient`` connection.
        _database: The ``pymongo`` database object for the selected DB.
    """

    # RU: Реализация Database на основе MongoDB.
    # RU: Каждый модуль — отдельная коллекция; документы хранятся
    # RU: в формате {"var": ..., "val": ...} и перезаписываются через upsert.

    def __init__(self, url: str, db_name: str):
        """Initialize the MongoDB client and select the target database.

        Args:
            url: MongoDB connection URI, e.g. ``mongodb://localhost:27017``.
            db_name: Name of the MongoDB database to use.

        Raises:
            ImportError: When ``pymongo`` is not installed in the environment.
        """
        # RU: Инициализация клиента MongoDB и выбор целевой базы данных.
        # RU: Если pymongo не установлен — выбрасывается ImportError с подсказкой.
        super().__init__()
        try:
            import pymongo
        except ImportError:
            raise ImportError("pymongo не установлен. Установите: pip install pymongo")

        self._client = pymongo.MongoClient(url)
        self._database = self._client[db_name]

    def get(self, module: str, variable: str, default: Any = None) -> Any:
        """Retrieve a variable's value from the named module collection.

        Args:
            module: Collection name corresponding to the calling module.
            variable: Key of the stored variable to look up.
            default: Value returned when the variable is not found.

        Returns:
            The stored value associated with *variable*, or *default* if
            no matching document exists in the collection.
        """
        # RU: Получает значение переменной из коллекции модуля.
        doc = self._database[module].find_one({"var": variable})
        return default if doc is None else doc["val"]

    def set(self, module: str, variable: str, value: Any) -> None:
        """Persist a variable value into the named module collection.

        Uses ``replace_one`` with ``upsert=True`` so the operation is
        idempotent — an existing document is replaced, otherwise a new
        one is created.

        Args:
            module: Collection name corresponding to the calling module.
            variable: Key under which the value is stored.
            value: Arbitrary serialisable value to persist.
        """
        # RU: Сохраняет значение в коллекцию через replace_one с upsert=True.
        self._database[module].replace_one(
            {"var": variable}, {"var": variable, "val": value}, upsert=True
        )

    def remove(self, module: str, variable: str) -> None:
        """Delete a variable document from the named module collection.

        Args:
            module: Collection name corresponding to the calling module.
            variable: Key of the variable document to delete.
        """
        # RU: Удаляет документ переменной из коллекции модуля.
        self._database[module].delete_one({"var": variable})

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Return all variable/value pairs stored in a module collection.

        Args:
            module: Collection name whose documents are to be fetched.

        Returns:
            A dictionary mapping each ``var`` field to its ``val`` field
            for every document found in the collection.
        """
        # RU: Возвращает все пары переменная/значение из коллекции модуля.
        return {item["var"]: item["val"] for item in self._database[module].find()}

    def get_modules(self) -> List[str]:
        """Return the names of all collections present in the database.

        Returns:
            A list of collection name strings, one per module that has
            ever written data to this database.
        """
        # RU: Возвращает список имён всех коллекций (модулей) в базе данных.
        return self._database.list_collection_names()

    def close(self) -> None:
        """Close the underlying MongoDB client connection.

        Should be called when the database object is no longer needed to
        release network resources held by the pymongo client.
        """
        # RU: Закрывает соединение с MongoDB и освобождает сетевые ресурсы.
        self._client.close()

    def backup(self, target_path: str) -> None:
        """Export the entire database to a timestamped JSON file.

        Iterates over all collections, fetches every document excluding
        the ``_id`` field, and serialises the result to a JSON file named
        ``mongodb_backup_YYYYMMDD_HHMM.json`` inside *target_path*.

        Args:
            target_path: Directory path where the backup file will be written.

        Raises:
            DatabaseError: When any I/O or serialisation error occurs during
                the backup process.
        """
        # RU: Экспортирует всю базу данных в JSON-файл с временной меткой.
        try:
            from pathlib import Path

            data = {}
            for collection in self._database.list_collection_names():
                # Exclude MongoDB's internal _id field from the export
                # RU: Поле _id исключается из экспорта проекцией {"_id": 0}.
                data[collection] = list(self._database[collection].find({}, {"_id": 0}))

            # Build timestamped filename and write JSON
            # RU: Формируем имя файла с меткой времени и записываем JSON.
            backup_file = (
                Path(target_path)
                / f"mongodb_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            )
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self._logger.info(f"MongoDB backup: {backup_file}")
        except Exception as e:
            raise DatabaseError(f"MongoDB backup failed: {e}") from e


__all__ = ["MongoDatabase"]
