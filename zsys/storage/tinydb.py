# core/db/tinydb.py — TinyDB драйвер
"""TinyDB backend — lightweight JSON-file storage driver.

Implements the Database interface using TinyDB, storing all data in a single
JSON file where each module name maps to a separate TinyDB table.  No external
database server is required, making this backend ideal for Android/Termux
environments.
"""
# RU: TinyDB-бэкенд — хранилище на основе JSON-файла.
# RU: Каждый модуль соответствует отдельной таблице TinyDB; не требует
# RU: внешних зависимостей, подходит для Android/Termux.

import shutil
from pathlib import Path
from typing import Any, Dict, List, Union

from .base import Database, DatabaseError


class TinyDBDatabase(Database):
    """TinyDB implementation of the Database interface.

    Persists all data in a single JSON file on disk.  Each *module* argument
    passed to the CRUD methods is mapped to a dedicated TinyDB table inside
    that file, providing logical namespacing without multiple files.

    Attributes:
        _path: Absolute string path to the backing JSON file.
        _db: Live ``TinyDB`` instance connected to ``_path``.
        _Query: Cached reference to the TinyDB ``Query`` factory class.
    """

    # RU: TinyDB-реализация интерфейса Database.
    # RU: Данные хранятся в JSON-файле; каждый модуль — отдельная таблица.

    def __init__(self, path: Union[str, Path]):
        """Initialise the TinyDB backend and open the JSON file.

        Creates all missing parent directories before opening the database so
        callers do not need to pre-create the directory tree.

        Args:
            path: File-system path to the JSON database file.  The file is
                created automatically if it does not already exist.

        Raises:
            ImportError: When the ``tinydb`` package is not installed.
        """
        # RU: Инициализирует TinyDB: создаёт директории и открывает файл.
        super().__init__()
        try:
            from tinydb import Query, TinyDB
        except ImportError:
            raise ImportError("tinydb не установлен. Установите: pip install tinydb")

        self._Query = Query
        self._path = str(path)
        Path(self._path).parent.mkdir(
            parents=True, exist_ok=True
        )  # RU: создаём родительские директории при необходимости

        self._db = TinyDB(self._path)

    def get(self, module: str, variable: str, default: Any = None) -> Any:
        """Retrieve a single variable value from a module table.

        Args:
            module: Table name corresponding to the logical module.
            variable: Name of the variable to look up.
            default: Value returned when the variable does not exist.

        Returns:
            The stored value for *variable*, or *default* if not found.
        """
        # RU: Возвращает значение переменной из таблицы модуля.
        table = self._db.table(module)
        data = table.get(
            self._Query().name == variable
        )  # RU: Query().name — поиск по полю «name»
        return data["value"] if data else default

    def set(self, module: str, variable: str, value: Any) -> None:
        """Persist a variable value into a module table.

        Uses TinyDB ``upsert`` so the record is created on first write and
        updated on subsequent writes without duplicating rows.

        Args:
            module: Table name corresponding to the logical module.
            variable: Name of the variable to store.
            value: Arbitrary JSON-serialisable value to persist.
        """
        # RU: Сохраняет значение переменной; upsert создаёт или обновляет запись.
        table = self._db.table(module)
        table.upsert({"name": variable, "value": value}, self._Query().name == variable)

    def remove(self, module: str, variable: str) -> None:
        """Delete a variable record from a module table.

        Silently does nothing if the variable does not exist.

        Args:
            module: Table name corresponding to the logical module.
            variable: Name of the variable to delete.
        """
        # RU: Удаляет запись переменной из таблицы; игнорирует отсутствие записи.
        table = self._db.table(module)
        table.remove(self._Query().name == variable)

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Return all variables stored in a module table as a dictionary.

        Args:
            module: Table name corresponding to the logical module.

        Returns:
            Mapping of variable names to their stored values.  Returns an
            empty dict when the table contains no records.
        """
        # RU: Возвращает все переменные таблицы в виде словаря {имя: значение}.
        table = self._db.table(module)
        return {entry["name"]: entry["value"] for entry in table.all()}

    def get_modules(self) -> List[str]:
        """List all table names present in the database.

        Returns:
            List of module (table) name strings currently known to TinyDB,
            including the built-in ``_default`` table if it was ever used.
        """
        # RU: Возвращает список имён всех таблиц (модулей) в базе данных.
        return list(self._db.tables())

    def close(self) -> None:
        """Flush pending writes and close the underlying TinyDB file handle."""
        # RU: Сбрасывает незаписанные данные и закрывает файл базы данных.
        self._db.close()

    def backup(self, target_path: Union[str, Path]) -> None:
        """Copy the JSON database file to *target_path* as a point-in-time backup.

        The method closes the database before copying to ensure the JSON file
        is fully flushed, then reopens it so the instance remains usable.

        Args:
            target_path: Destination file path for the backup copy.  Parent
                directories must already exist.

        Raises:
            DatabaseError: When the file copy or reopen operation fails for
                any reason.
        """
        # RU: Создаёт резервную копию JSON-файла базы данных.
        try:
            self._db.close()  # RU: закрываем БД, чтобы сбросить буферы перед копированием
            shutil.copy(self._path, str(target_path))
            self._logger.info(f"TinyDB backup: {target_path}")
            from tinydb import TinyDB

            self._db = TinyDB(self._path)  # RU: переоткрываем БД после копирования
        except Exception as e:
            raise DatabaseError(f"TinyDB backup failed: {e}") from e


__all__ = ["TinyDBDatabase"]
