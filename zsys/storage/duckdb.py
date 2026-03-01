# core/db/duckdb.py — DuckDB драйвер
"""
Реализация Database для DuckDB.
Аналитическая колоночная БД, недоступна на Android.
"""

import threading
import shutil
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from .base import Database, DatabaseError


class DuckDBDatabase(Database):
    """
    DuckDB реализация базы данных.
    
    Использует схему 'core' для всех таблиц.
    
    Attributes:
        _file: Путь к файлу БД
        _conn: DuckDB соединение
        _lock: threading.Lock для потокобезопасности
    """

    def __init__(self, file: Union[str, Path]):
        """
        Инициализация DuckDB.
        
        Args:
            file: Путь к файлу базы данных
        """
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
        """Выполняет SQL запрос с блокировкой."""
        with self._lock:
            if params:
                return self._conn.execute(sql, params)
            return self._conn.execute(sql)

    def _ensure_table(self, module: str) -> None:
        """Создает таблицу если не существует."""
        sql = f'''
        CREATE TABLE IF NOT EXISTS core."{module}" (
            var TEXT UNIQUE NOT NULL,
            val TEXT NOT NULL
        );
        '''
        self._execute(sql)

    def get(self, module: str, variable: str, default: Any = None) -> Any:
        """Получает значение из таблицы."""
        try:
            self._ensure_table(module)
            sql = f'SELECT val FROM core."{module}" WHERE var = $1'
            result = self._execute(sql, [variable]).fetchone()
            return default if result is None else result[0]
        except self._duckdb.Error:
            return default

    def set(self, module: str, variable: str, value: Any) -> None:
        """Записывает значение в таблицу."""
        self._ensure_table(module)
        sql = f'''
        INSERT INTO core."{module}" (var, val) VALUES ($1, $2)
        ON CONFLICT(var) DO UPDATE SET val = $2
        '''
        self._execute(sql, [variable, str(value)])

    def remove(self, module: str, variable: str) -> None:
        """Удаляет переменную из таблицы."""
        self._ensure_table(module)
        sql = f'DELETE FROM core."{module}" WHERE var = $1'
        self._execute(sql, [variable])

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Получает все значения таблицы."""
        try:
            self._ensure_table(module)
            sql = f'SELECT var, val FROM core."{module}"'
            result = self._execute(sql).fetchall()
            return {row[0]: row[1] for row in result}
        except self._duckdb.Error:
            return {}

    def get_modules(self) -> List[str]:
        """Получает список всех таблиц в схеме core."""
        sql = """
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'core'
        """
        result = self._execute(sql).fetchall()
        return [row[0] for row in result]

    def close(self) -> None:
        """Закрывает соединение."""
        self._conn.close()

    def backup(self, target_path: Union[str, Path]) -> None:
        """
        Создает копию файла БД.
        
        Args:
            target_path: Путь для сохранения копии
        """
        try:
            self._conn.close()
            shutil.copy2(self._file, str(target_path))
            self._logger.info(f"DuckDB backup: {target_path}")
            self._conn = self._duckdb.connect(self._file)
        except Exception as e:
            raise DatabaseError(f"DuckDB backup failed: {e}") from e


__all__ = ["DuckDBDatabase"]
