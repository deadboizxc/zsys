# core/db/duckdb.py — DuckDB драйвер
"""DuckDB backend — columnar analytical database driver.

Implements the :class:`~zsys.storage.base.Database` interface on top of
DuckDB, a high-performance columnar analytical engine.  This backend is
**not available on Android** due to missing native libraries.
"""
# RU: DuckDB бэкенд — драйвер колоночной аналитической базы данных.
# RU: Реализует интерфейс Database поверх DuckDB.
# RU: Недоступен на Android из-за отсутствия нативных библиотек.

import threading
import shutil
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from .base import Database, DatabaseError


class DuckDBDatabase(Database):
    """DuckDB implementation of the Database interface.

    All tables are created inside the ``core`` schema.  Concurrent access is
    serialised through a :class:`threading.Lock` so the instance is safe to
    share across threads.

    Attributes:
        _file: Absolute path to the on-disk DuckDB database file.
        _conn: Active DuckDB connection object.
        _lock: Reentrant mutex that guards every statement execution.
    """

    # RU: DuckDB-реализация интерфейса Database.
    # RU: Все таблицы создаются в схеме core; доступ потокобезопасен через Lock.

    def __init__(self, file: Union[str, Path]):
        """Initialise a DuckDB database at the given file path.

        Creates all missing parent directories before opening the connection,
        then bootstraps the ``core`` schema.

        Args:
            file: Path to the DuckDB database file; created if absent.

        Raises:
            ImportError: When the ``duckdb`` package is not installed.
        """
        # RU: Создаёт родительские директории, открывает соединение и схему core.
        super().__init__()
        try:
            import duckdb
        except ImportError:
            raise ImportError("duckdb не установлен. Установите: pip install duckdb")

        self._file = str(file)
        Path(self._file).parent.mkdir(parents=True, exist_ok=True)

        self._duckdb = duckdb
        self._conn = duckdb.connect(self._file)
        self._lock = threading.Lock()

        self._execute("CREATE SCHEMA IF NOT EXISTS core;")

    def _execute(self, sql: str, params: Optional[list] = None):
        """Execute a SQL statement inside the thread-safety lock.

        Args:
            sql: The SQL statement to execute.
            params: Optional positional parameters bound to ``$1``, ``$2`` …
                placeholders in *sql*.

        Returns:
            The DuckDB relation / cursor returned by ``connection.execute``.
        """
        # RU: Выполняет SQL-запрос под Lock для потокобезопасности.
        with self._lock:
            if params:
                return self._conn.execute(sql, params)
            return self._conn.execute(sql)

    def _ensure_table(self, module: str) -> None:
        """Create the module table inside the ``core`` schema if absent.

        The table uses a single ``UNIQUE`` text column ``var`` as the key and
        a text column ``val`` as the value, enabling upserts via
        ``ON CONFLICT``.

        Args:
            module: Logical module name used as the table name.
        """
        # RU: Создаёт таблицу модуля в схеме core, если она ещё не существует.
        sql = f'''
        CREATE TABLE IF NOT EXISTS core."{module}" (
            var TEXT UNIQUE NOT NULL,
            val TEXT NOT NULL
        );
        '''
        self._execute(sql)

    def get(self, module: str, variable: str, default: Any = None) -> Any:
        """Retrieve a stored value by module and variable name.

        Args:
            module: Table name within the ``core`` schema.
            variable: Key to look up in the ``var`` column.
            default: Value returned when the key is absent or a DuckDB error
                occurs.

        Returns:
            The stored string value, or *default* if not found.
        """
        # RU: Возвращает значение по ключу или default при отсутствии/ошибке.
        try:
            self._ensure_table(module)
            sql = f'SELECT val FROM core."{module}" WHERE var = $1'
            result = self._execute(sql, [variable]).fetchone()
            return default if result is None else result[0]
        except self._duckdb.Error:
            return default

    def set(self, module: str, variable: str, value: Any) -> None:
        """Persist a value; insert or update via ``ON CONFLICT(var) DO UPDATE``.

        The value is coerced to ``str`` before storage.

        Args:
            module: Table name within the ``core`` schema.
            variable: Key written to the ``var`` column.
            value: Value written to the ``val`` column; converted with
                ``str()``.
        """
        # RU: Сохраняет значение; использует upsert через ON CONFLICT(var) DO UPDATE.
        self._ensure_table(module)
        sql = f'''
        INSERT INTO core."{module}" (var, val) VALUES ($1, $2)
        ON CONFLICT(var) DO UPDATE SET val = $2
        '''
        self._execute(sql, [variable, str(value)])

    def remove(self, module: str, variable: str) -> None:
        """Delete a single key-value pair from the module table.

        Args:
            module: Table name within the ``core`` schema.
            variable: Key to delete from the ``var`` column.
        """
        # RU: Удаляет одну запись по ключу из таблицы модуля.
        self._ensure_table(module)
        sql = f'DELETE FROM core."{module}" WHERE var = $1'
        self._execute(sql, [variable])

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Return all key-value pairs stored in a module table.

        Args:
            module: Table name within the ``core`` schema.

        Returns:
            Dictionary mapping every ``var`` to its ``val``; empty dict on
            DuckDB error.
        """
        # RU: Возвращает все пары ключ-значение таблицы; пустой dict при ошибке.
        try:
            self._ensure_table(module)
            sql = f'SELECT var, val FROM core."{module}"'
            result = self._execute(sql).fetchall()
            return {row[0]: row[1] for row in result}
        except self._duckdb.Error:
            return {}

    def get_modules(self) -> List[str]:
        """List all table names registered under the ``core`` schema.

        Returns:
            List of table name strings; order is not guaranteed.
        """
        # RU: Возвращает имена всех таблиц в схеме core через information_schema.
        sql = """
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'core'
        """
        result = self._execute(sql).fetchall()
        return [row[0] for row in result]

    def close(self) -> None:
        """Close the active DuckDB connection and release file handles."""
        # RU: Закрывает соединение с базой данных и освобождает файловые дескрипторы.
        self._conn.close()

    def backup(self, target_path: Union[str, Path]) -> None:
        """Copy the database file to *target_path* as a point-in-time backup.

        The method closes the connection before copying so DuckDB flushes all
        WAL data, then reopens the connection so the instance remains usable.

        Args:
            target_path: Destination file path for the backup copy.

        Raises:
            DatabaseError: When the file copy or connection operations fail.
        """
        # RU: Создаёт резервную копию: закрывает соединение, копирует файл, переоткрывает соединение.
        try:
            self._conn.close()
            shutil.copy2(self._file, str(target_path))
            self._logger.info(f"DuckDB backup: {target_path}")
            self._conn = self._duckdb.connect(self._file)
        except Exception as e:
            raise DatabaseError(f"DuckDB backup failed: {e}") from e


__all__ = ["DuckDBDatabase"]
