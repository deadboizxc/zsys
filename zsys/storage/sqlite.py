# core/db/sqlite.py — SQLite драйвер
"""
Реализация Database для SQLite.
"""

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
    """
    Validate table name to prevent SQL injection.
    
    Args:
        name: Table/module name to validate
    
    Returns:
        The validated name
    
    Raises:
        ValueError: If name contains invalid characters
    """
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
    """
    SQLite реализация базы данных.
    
    Потокобезопасная, использует WAL режим для производительности.
    
    Attributes:
        _file: Путь к файлу БД
        _conn: SQLite соединение
        _cursor: Курсор для запросов
        _lock: Мьютекс для потокобезопасности
    """
    
    def __init__(self, file: Union[str, Path]):
        """
        Инициализация SQLite БД.
        
        Args:
            file: Путь к файлу базы данных
        """
        super().__init__()
        self._file = str(file)
        
        # Создать директорию если нужно
        Path(self._file).parent.mkdir(parents=True, exist_ok=True)
        
        self._conn = sqlite3.connect(self._file, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.row_factory = sqlite3.Row
        self._cursor = self._conn.cursor()
        self._lock = threading.Lock()

    @staticmethod
    def _parse_row(row: sqlite3.Row) -> Any:
        """Преобразует строку БД в Python тип."""
        row_type = row["type"]
        if row_type == "bool":
            return row["val"] == "1"
        elif row_type == "int":
            return int(row["val"])
        elif row_type == "str":
            return row["val"]
        else:
            return json.loads(row["val"])

    def _execute(self, module: str, sql: str, params: Optional[Dict] = None) -> sqlite3.Cursor:
        """Выполняет SQL запрос с автоматическим созданием таблицы."""
        # Validate module name to prevent SQL injection
        module = _validate_table_name(module)
        
        with self._lock:
            try:
                return self._cursor.execute(sql, params or {})
            except sqlite3.OperationalError as e:
                if str(e).startswith("no such table"):
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
        """Получает значение из БД."""
        module = _validate_table_name(module)
        sql = f'SELECT * FROM "{module}" WHERE var = :var'
        try:
            cur = self._execute(module, sql, {"var": variable})
            row = cur.fetchone()
            return default if row is None else self._parse_row(row)
        except sqlite3.OperationalError:
            return default

    def set(self, module: str, variable: str, value: Any) -> None:
        """Записывает значение в БД."""
        module = _validate_table_name(module)
        sql = f'''
        INSERT INTO "{module}" (var, val, type) VALUES (:var, :val, :type)
        ON CONFLICT(var) DO UPDATE SET val = :val, type = :type WHERE var = :var
        '''
        
        if isinstance(value, bool):
            val, typ = "1" if value else "0", "bool"
        elif isinstance(value, int):
            val, typ = str(value), "int"
        elif isinstance(value, str):
            val, typ = value, "str"
        else:
            val, typ = json.dumps(value, ensure_ascii=False), "json"
        
        self._execute(module, sql, {"var": variable, "val": val, "type": typ})
        self._conn.commit()

    def remove(self, module: str, variable: str) -> None:
        """Удаляет переменную из БД."""
        module = _validate_table_name(module)
        sql = f'DELETE FROM "{module}" WHERE var = :var'
        self._execute(module, sql, {"var": variable})
        self._conn.commit()

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Получает все значения модуля."""
        module = _validate_table_name(module)
        sql = f'SELECT * FROM "{module}"'
        try:
            cur = self._execute(module, sql)
            return {row["var"]: self._parse_row(row) for row in cur}
        except sqlite3.OperationalError:
            return {}

    def get_modules(self) -> List[str]:
        """Получает список всех таблиц/модулей."""
        sql = "SELECT name FROM sqlite_master WHERE type='table';"
        result = self._cursor.execute(sql).fetchall()
        return [row[0] for row in result]

    def close(self) -> None:
        """Закрывает соединение с БД."""
        self._conn.commit()
        self._conn.close()

    def backup(self, target_path: Union[str, Path]) -> None:
        """
        Создает резервную копию БД.
        
        Args:
            target_path: Путь для сохранения копии
        """
        try:
            self._conn.commit()
            shutil.copy2(self._file, str(target_path))
            self._logger.info(f"Backup SQLite: {target_path}")
        except Exception as e:
            raise DatabaseError(f"Ошибка backup: {e}") from e


__all__ = ["SqliteDatabase"]
