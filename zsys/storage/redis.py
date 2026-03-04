# core/db/redis.py — Redis драйвер
"""Redis database backend — persistent key-value storage via redis-py.

Implements the Database interface using Redis as the storage engine.
Keys are stored in ``module:variable`` format; dicts and lists are
serialised as JSON, booleans as ``"1"``/``"0"``, and all other
non-string values are coerced with :func:`str`.
"""
# RU: Redis-бэкенд базы данных — постоянное хранилище через redis-py.
# RU: Ключи хранятся в формате «модуль:переменная»; словари и списки
# RU: сериализуются как JSON, булевы — как «1»/«0», остальное — через str().

import json
import threading
from datetime import datetime
from typing import Any, Dict, List

from .base import Database, DatabaseError


class RedisDatabase(Database):
    """Redis-backed implementation of the Database interface.

    Stores every variable under the compound key ``"<module>:<variable>"``
    inside a single Redis database index.  The client is created with
    ``decode_responses=True`` so all values are returned as :class:`str`.
    Complex types (``dict``, ``list``) are round-tripped through JSON;
    booleans are stored as ``"1"`` or ``"0"``.

    Attributes:
        _client: Underlying ``redis.Redis`` client instance.
        _lock: ``threading.Lock`` used to serialise concurrent writes.
    """

    # RU: Реализация Database на базе Redis.
    # RU: Каждая переменная хранится под ключом «модуль:переменная».
    # RU: Клиент создаётся с decode_responses=True; словари/списки — JSON,
    # RU: булевы — «1»/«0».

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """Initialise and connect a Redis client.

        Imports ``redis`` lazily so the package remains optional.  The
        client is configured with ``decode_responses=True``.

        Args:
            host: Hostname or IP address of the Redis server.
            port: TCP port the Redis server listens on (default ``6379``).
            db: Zero-based Redis database index to select (default ``0``).

        Raises:
            ImportError: When the ``redis`` package is not installed.
        """
        # RU: Инициализирует и подключает Redis-клиент.
        # RU: Пакет redis импортируется лениво, чтобы оставаться опциональным.
        super().__init__()
        try:
            import redis
        except ImportError:
            raise ImportError("redis не установлен. Установите: pip install redis")

        self._client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self._lock = threading.Lock()

    def get(self, module: str, variable: str, default: Any = None) -> Any:
        """Retrieve a variable's value from Redis.

        Attempts to deserialise the stored string as JSON; falls back to
        returning the raw string when deserialisation fails.

        Args:
            module: Logical namespace / module name.
            variable: Variable name within *module*.
            default: Value returned when the key does not exist.

        Returns:
            The deserialised value, the raw string, or *default* if the
            key is absent.
        """
        # RU: Возвращает значение переменной из Redis.
        # RU: Пытается десериализовать JSON; при ошибке возвращает строку.
        key = f"{module}:{variable}"
        value = self._client.get(key)
        if value is None:
            return default
        try:
            return json.loads(value)  # deserialise JSON-encoded complex types
        except json.JSONDecodeError:
            return value  # plain string — return as-is

    def set(self, module: str, variable: str, value: Any) -> None:
        """Persist a variable's value in Redis.

        Serialisation rules applied before writing:

        * ``dict`` / ``list`` → JSON string (``ensure_ascii=False``).
        * ``bool`` → ``"1"`` for ``True``, ``"0"`` for ``False``.
        * Any other non-string type → ``str(value)``.

        Args:
            module: Logical namespace / module name.
            variable: Variable name within *module*.
            value: Value to store; must be JSON-serialisable when a
                ``dict`` or ``list``.

        Returns:
            ``None``
        """
        # RU: Сохраняет значение переменной в Redis.
        # RU: dict/list → JSON; bool → «1»/«0»; остальное → str().
        key = f"{module}:{variable}"
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)  # complex type → JSON
        elif isinstance(value, bool):
            value = "1" if value else "0"  # bool before int to avoid int branch
        elif not isinstance(value, str):
            value = str(value)
        self._client.set(key, value)

    def remove(self, module: str, variable: str) -> None:
        """Delete a single variable key from Redis.

        Args:
            module: Logical namespace / module name.
            variable: Variable name within *module* to delete.

        Returns:
            ``None``
        """
        # RU: Удаляет один ключ переменной из Redis.
        key = f"{module}:{variable}"
        self._client.delete(key)

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Return all variables stored under *module* as a dictionary.

        Uses a ``KEYS <module>:*`` pattern scan.  Each value is
        deserialised from JSON where possible.

        Args:
            module: Logical namespace whose variables to fetch.

        Returns:
            Mapping of variable name → deserialised value for every key
            that belongs to *module*.
        """
        # RU: Возвращает все переменные модуля в виде словаря.
        # RU: Значения десериализуются из JSON, если возможно.
        collection = {}
        keys = self._client.keys(f"{module}:*")  # scan keys matching the module prefix
        for key in keys:
            variable = key.split(":", 1)[1]  # strip "<module>:" prefix
            value = self._client.get(key)
            try:
                collection[variable] = json.loads(value)
            except json.JSONDecodeError:
                collection[variable] = value
        return collection

    def get_modules(self) -> List[str]:
        """Return the distinct module names present in the Redis database.

        Derives module names by scanning all keys and extracting the
        segment before the first ``":"`` separator.  Keys without a
        ``":"`` are ignored.

        Returns:
            Deduplicated list of module name strings.
        """
        # RU: Возвращает уникальные имена модулей, извлечённые из ключей Redis.
        # RU: Ключи без «:» игнорируются.
        modules = set()
        for key in self._client.keys("*"):
            if ":" in key:
                module = key.split(":")[0]  # first segment is the module name
                modules.add(module)
        return list(modules)

    def close(self) -> None:
        """Close the underlying Redis connection.

        Returns:
            ``None``
        """
        # RU: Закрывает соединение с Redis.
        self._client.close()

    def backup(self, target_path: str) -> None:
        """Export all data to a timestamped JSON file.

        Iterates over every module returned by :meth:`get_modules`,
        collects each module's collection via :meth:`get_collection`, and
        writes the aggregated dict to
        ``<target_path>/redis_backup_YYYYMMDD_HHMM.json``.

        Args:
            target_path: Directory path where the backup file is created.
                The directory must already exist.

        Returns:
            ``None``

        Raises:
            DatabaseError: When any step of the backup process fails
                (I/O error, serialisation error, etc.).
        """
        # RU: Экспортирует все данные в файл JSON с временно́й меткой.
        # RU: Файл создаётся в target_path; при любой ошибке бросает DatabaseError.
        try:
            from pathlib import Path

            data = {}
            for module in self.get_modules():
                data[module] = self.get_collection(module)

            # build timestamped filename, e.g. redis_backup_20240101_1530.json
            backup_file = (
                Path(target_path)
                / f"redis_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            )
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self._logger.info(f"Redis backup: {backup_file}")
        except Exception as e:
            raise DatabaseError(f"Redis backup failed: {e}") from e


__all__ = ["RedisDatabase"]
