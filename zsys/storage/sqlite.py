# core/db/sqlite.py — SQLite драйвер
"""Thread-safe SQLite storage backend — typed key/value store per module.

Implements the :class:`Database` interface using SQLite with WAL journal mode
for improved read concurrency.  Each logical module maps to its own table;
values are stored as text alongside a ``type`` column so that ``bool``,
``int``, ``str``, and arbitrary JSON objects survive a round-trip without
losing their Python type.
"""
# RU: Потокобезопасный SQLite-бэкенд — хранилище типизированных пар ключ/значение.
# RU: Каждый модуль отображается на отдельную таблицу; тип значения сохраняется
# RU: в столбце ``type``, что позволяет корректно восстанавливать Python-объекты.

import sqlite3
import threading
import json
import shutil
import re
from typing import Any, Dict, Optional, Union, List
from pathlib import Path

from .base import Database, DatabaseError


# Allowed characters for table/module names (SQL injection protection)
# Allow dots for namespaced modules like "core.main"
_VALID_TABLE_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_.]*$')


def _validate_table_name(name: str) -> str:
    """Validate and return a table name, raising on unsafe input.

    Guards every dynamic SQL statement against injection by rejecting any name
    that does not match :data:`_VALID_TABLE_NAME_PATTERN`.  Names must start
    with a letter or underscore, contain only alphanumeric characters,
    underscores, or dots (for namespaced modules such as ``"core.main"``), and
    be between 1 and 128 characters long.

    Args:
        name: Candidate table or module name to validate.

    Returns:
        The original ``name`` string, unchanged, when it passes validation.

    Raises:
        ValueError: If ``name`` is empty, exceeds 128 characters, or contains
            characters not matched by :data:`_VALID_TABLE_NAME_PATTERN`.
    """
    # RU: Проверяет имя таблицы на допустимые символы для защиты от SQL-инъекций.
    if not name or len(name) > 128:
        raise ValueError(f"Invalid table name length: {len(name) if name else 0}")
    if not _VALID_TABLE_NAME_PATTERN.match(name):
        raise ValueError(
            f"Invalid table name '{name}'. "
            "Only alphanumeric characters, underscores, and dots are allowed, "
            "must start with letter or underscore."
        )
    return name


class SqliteDatabase(Database):
    """Thread-safe SQLite implementation of the :class:`Database` interface.

    A single SQLite file backs the store.  All public methods acquire
    :attr:`_lock` before touching the cursor, making the instance safe to
    share across threads.  WAL journal mode is enabled at construction time so
    that readers do not block writers.  Tables are created lazily on the first
    write to a previously unseen module (see :meth:`_execute`).  Each row
    records the serialised value together with its Python type tag so that
    :meth:`_parse_row` can reconstruct the original object faithfully.

    Attributes:
        _file: Absolute path to the SQLite database file on disk.
        _conn: Persistent :class:`sqlite3.Connection` opened with
            ``check_same_thread=False``.
        _cursor: Reusable :class:`sqlite3.Cursor` for all statements.
        _lock: :class:`threading.Lock` that serialises cursor access.
    """
    # RU: Потокобезопасная SQLite-реализация интерфейса Database.
    # RU: Использует WAL-режим; таблицы создаются лениво при первом обращении.

    def __init__(self, file: Union[str, Path]):
        """Open (or create) the SQLite database at *file*.

        Creates all intermediate directories if they do not exist, then opens
        a connection with WAL journal mode and installs
        :attr:`sqlite3.Row` as the row factory so columns are accessible by
        name throughout the class.

        Args:
            file: Path to the SQLite database file.  The file and its parent
                directories are created automatically if they do not exist.
        """
        # RU: Открывает (или создаёт) файл БД, включает WAL-режим и инициализирует мьютекс.
        super().__init__()
        self._file = str(file)

        # Создать директорию если нужно
        Path(self._file).parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(self._file, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")  # RU: WAL для неблокирующего чтения
        self._conn.row_factory = sqlite3.Row
        self._cursor = self._conn.cursor()
        self._lock = threading.Lock()

    @staticmethod
    def _parse_row(row: sqlite3.Row) -> Any:
        """Deserialize a typed SQLite row back to its original Python object.

        The ``type`` column drives dispatch: ``"bool"`` is reconstructed from
        the sentinel strings ``"1"``/``"0"``; ``"int"`` is cast with
        :func:`int`; ``"str"`` is returned verbatim; anything else is decoded
        with :func:`json.loads`.

        Args:
            row: A :class:`sqlite3.Row` containing at least the ``val`` and
                ``type`` columns produced by :meth:`_execute`.

        Returns:
            The Python value corresponding to the stored ``(val, type)`` pair.
            Returns a :class:`bool`, :class:`int`, :class:`str`, or any object
            that :func:`json.loads` can reconstruct (e.g. ``dict``, ``list``).
        """
        # RU: Преобразует строку БД в исходный Python-тип по метке в столбце ``type``.
        row_type = row["type"]
        if row_type == "bool":
            return row["val"] == "1"  # RU: "1" → True, всё остальное → False
        elif row_type == "int":
            return int(row["val"])
        elif row_type == "str":
            return row["val"]
        else:
            return json.loads(row["val"])  # RU: JSON для dict/list и прочих объектов

    def _execute(self, module: str, sql: str, params: Optional[Dict] = None) -> sqlite3.Cursor:
        """Execute *sql* against *module*'s table, auto-creating it if absent.

        Acquires :attr:`_lock` before delegating to the shared cursor.  If the
        statement raises :exc:`sqlite3.OperationalError` with a message that
        starts with ``"no such table"``, the missing table is created with the
        canonical ``(var TEXT UNIQUE, val TEXT, type TEXT)`` schema and the
        original statement is retried exactly once.

        Args:
            module: Validated module name used as the table name in *sql*.
                Must already have been passed through :func:`_validate_table_name`.
            sql: Parameterised SQL statement to execute.
            params: Optional mapping of named bind parameters for *sql*.
                Defaults to an empty dict when omitted.

        Returns:
            The :class:`sqlite3.Cursor` after successful execution, ready for
            ``fetchone()`` / ``fetchall()`` calls.

        Raises:
            sqlite3.OperationalError: Re-raised for any error other than a
                missing-table condition, or if the retry itself fails.
        """
        # RU: Выполняет SQL с блокировкой; при отсутствии таблицы создаёт её и повторяет запрос.
        module = _validate_table_name(module)  # RU: Повторная проверка на случай прямого вызова

        with self._lock:
            try:
                return self._cursor.execute(sql, params or {})
            except sqlite3.OperationalError as e:
                if str(e).startswith("no such table"):
                    # RU: Таблица ещё не существует — создаём и повторяем запрос
                    create_sql = f'''
                    CREATE TABLE IF NOT EXISTS "{module}" (
                        var TEXT UNIQUE NOT NULL,
                        val TEXT NOT NULL,
                        type TEXT NOT NULL
                    )
                    '''
                    self._cursor.execute(create_sql)
                    self._conn.commit()
                    return self._cursor.execute(sql, params or {})
                raise

    def get(self, module: str, variable: str, default: Any = None) -> Any:
        """Retrieve a single value from *module* by *variable* name.

        Args:
            module: Logical module (table) name; validated against
                :data:`_VALID_TABLE_NAME_PATTERN`.
            variable: Key whose associated value should be returned.
            default: Fallback value returned when *variable* is not found or
                the table does not yet exist.  Defaults to ``None``.

        Returns:
            The stored Python value reconstructed by :meth:`_parse_row`, or
            *default* when the key is absent or the table does not exist.

        Raises:
            ValueError: If *module* fails :func:`_validate_table_name`.
        """
        # RU: Возвращает значение переменной из таблицы модуля или default при отсутствии.
        module = _validate_table_name(module)
        sql = f'SELECT * FROM "{module}" WHERE var = :var'
        try:
            cur = self._execute(module, sql, {"var": variable})
            row = cur.fetchone()
            return default if row is None else self._parse_row(row)
        except sqlite3.OperationalError:
            return default

    def set(self, module: str, variable: str, value: Any) -> None:
        """Persist *value* under *variable* in *module*, inserting or replacing.

        Serialises *value* to a ``(val, type)`` pair before writing:
        ``bool`` → ``"1"``/``"0"`` with type ``"bool"``; ``int`` → decimal
        string with type ``"int"``; ``str`` → verbatim with type ``"str"``;
        everything else → :func:`json.dumps` with type ``"json"``.
        The table is created automatically if it does not yet exist.

        Args:
            module: Logical module (table) name; validated against
                :data:`_VALID_TABLE_NAME_PATTERN`.
            variable: Key under which the value is stored.
            value: Python value to persist.  Must be JSON-serialisable when
                it is not a ``bool``, ``int``, or ``str``.

        Returns:
            ``None``.

        Raises:
            ValueError: If *module* fails :func:`_validate_table_name`.
            TypeError: If *value* is not JSON-serialisable.
        """
        # RU: Сохраняет значение в таблицу модуля, вставляя или обновляя строку.
        module = _validate_table_name(module)
        sql = f'''
        INSERT INTO "{module}" (var, val, type) VALUES (:var, :val, :type)
        ON CONFLICT(var) DO UPDATE SET val = :val, type = :type WHERE var = :var
        '''

        if isinstance(value, bool):
            val, typ = "1" if value else "0", "bool"  # RU: bool проверяем до int — bool подкласс int
        elif isinstance(value, int):
            val, typ = str(value), "int"
        elif isinstance(value, str):
            val, typ = value, "str"
        else:
            val, typ = json.dumps(value, ensure_ascii=False), "json"

        self._execute(module, sql, {"var": variable, "val": val, "type": typ})
        self._conn.commit()

    def remove(self, module: str, variable: str) -> None:
        """Delete *variable* from *module*, silently succeeding if absent.

        Args:
            module: Logical module (table) name; validated against
                :data:`_VALID_TABLE_NAME_PATTERN`.
            variable: Key to delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If *module* fails :func:`_validate_table_name`.
        """
        # RU: Удаляет переменную из таблицы модуля; не ошибается при отсутствии ключа.
        module = _validate_table_name(module)
        sql = f'DELETE FROM "{module}" WHERE var = :var'
        self._execute(module, sql, {"var": variable})
        self._conn.commit()

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Return all key/value pairs stored under *module* as a dict.

        Args:
            module: Logical module (table) name; validated against
                :data:`_VALID_TABLE_NAME_PATTERN`.

        Returns:
            A :class:`dict` mapping every ``var`` to its deserialized Python
            value.  Returns an empty dict when the table does not exist or an
            :exc:`sqlite3.OperationalError` occurs.

        Raises:
            ValueError: If *module* fails :func:`_validate_table_name`.
        """
        # RU: Возвращает все переменные модуля в виде словаря; пустой dict при отсутствии таблицы.
        module = _validate_table_name(module)
        sql = f'SELECT * FROM "{module}"'
        try:
            cur = self._execute(module, sql)
            return {row["var"]: self._parse_row(row) for row in cur}
        except sqlite3.OperationalError:
            return {}

    def get_modules(self) -> List[str]:
        """Return the names of all tables (modules) present in the database.

        Queries ``sqlite_master`` directly, so the result reflects the current
        on-disk schema without acquiring :attr:`_lock`.

        Returns:
            A :class:`list` of table-name strings.  Empty when the database
            contains no tables yet.
        """
        # RU: Возвращает список всех таблиц (модулей) из sqlite_master.
        sql = "SELECT name FROM sqlite_master WHERE type='table';"
        result = self._cursor.execute(sql).fetchall()
        return [row[0] for row in result]

    def close(self) -> None:
        """Flush pending writes and close the database connection.

        Commits any outstanding transaction before closing so that no data is
        lost if the caller omits an explicit :meth:`set` commit.

        Returns:
            ``None``.
        """
        # RU: Фиксирует транзакцию и закрывает соединение с БД.
        self._conn.commit()
        self._conn.close()

    def backup(self, target_path: Union[str, Path]) -> None:
        """Copy the database file to *target_path* as a point-in-time backup.

        Commits the current transaction first so the copy reflects the latest
        state.  Uses :func:`shutil.copy2` to preserve file metadata.

        Args:
            target_path: Destination path for the backup file.  The parent
                directory must already exist.

        Returns:
            ``None``.

        Raises:
            DatabaseError: Wraps any exception raised during the copy
                (e.g. :exc:`OSError`, :exc:`PermissionError`).
        """
        # RU: Создаёт резервную копию файла БД по указанному пути; оборачивает ошибки в DatabaseError.
        try:
            self._conn.commit()
            shutil.copy2(self._file, str(target_path))
            self._logger.info(f"Backup SQLite: {target_path}")
        except Exception as e:
            raise DatabaseError(f"Ошибка backup: {e}") from e


__all__ = ["SqliteDatabase"]
