# core/db/lmdb.py — LMDB драйвер
"""LMDB backend — Lightning Memory-Mapped Database storage driver.

Implements the Database interface on top of LMDB, a memory-mapped file-based
key-value store with a fixed 1 GB map_size. Not available on Android due to
missing mmap support.
"""
# RU: LMDB бэкенд — драйвер хранилища на основе Lightning Memory-Mapped Database.
# RU: Реализует интерфейс Database поверх LMDB — файлового хранилища с отображением
# RU: в память, фиксированным map_size 1 ГБ. Недоступен на Android.

import json
import shutil
import threading
from typing import Any, Dict, List, Union
from pathlib import Path

from .base import Database, DatabaseError


class LMDBDatabase(Database):
    """LMDB-backed implementation of the Database interface.

    Keys are stored as UTF-8 bytes in the form ``"module:variable"``.
    Values are JSON-serialised before writing and deserialised on read.
    All write operations run inside LMDB transactions for atomicity.

    Attributes:
        _path: Filesystem path to the LMDB directory.
        _env: Open ``lmdb.Environment`` instance.
        _lock: ``threading.Lock`` guarding concurrent access.
    """

    # RU: LMDB-реализация интерфейса Database.
    # RU: Ключи — байты вида "module:variable"; значения сериализуются в JSON.
    # RU: Все операции записи выполняются внутри LMDB-транзакций для атомарности.

    def __init__(self, path: Union[str, Path]):
        """Initialise an LMDB environment at the given path.

        Creates all missing parent directories before opening the environment.
        The map_size is fixed at 1 GB, which is the virtual address space
        reserved for the database file.

        Args:
            path: Filesystem path to the LMDB directory; created if absent.

        Raises:
            ImportError: When the ``lmdb`` package is not installed.
        """
        # RU: Инициализирует окружение LMDB по указанному пути.
        # RU: Создаёт родительские директории при необходимости; map_size = 1 ГБ.
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
        """Retrieve a value from LMDB by module and variable name.

        Looks up the key ``"<module>:<variable>"`` in a read-only transaction
        and JSON-deserialises the stored bytes.

        Args:
            module: Logical namespace that owns the variable.
            variable: Variable name within the module.
            default: Value returned when the key does not exist.

        Returns:
            The deserialised Python object, or *default* if the key is absent.
        """
        # RU: Читает значение из LMDB по составному ключу "module:variable".
        with self._env.begin() as txn:
            value = txn.get(f"{module}:{variable}".encode())
            if value is None:
                return default
            return json.loads(value)

    def set(self, module: str, variable: str, value: Any) -> None:
        """Persist a value in LMDB under the given module and variable.

        Serialises *value* to JSON bytes and writes them in a write transaction
        using the key ``"<module>:<variable>"``.

        Args:
            module: Logical namespace that owns the variable.
            variable: Variable name within the module.
            value: JSON-serialisable Python object to store.

        Returns:
            None.
        """
        # RU: Сохраняет значение в LMDB; ключ "module:variable", значение — JSON.
        with self._env.begin(write=True) as txn:
            txn.put(
                f"{module}:{variable}".encode(),
                json.dumps(value, ensure_ascii=False).encode(),
            )

    def remove(self, module: str, variable: str) -> None:
        """Delete a key from LMDB.

        Removes the entry for ``"<module>:<variable>"`` inside a write
        transaction. Silently succeeds if the key does not exist.

        Args:
            module: Logical namespace that owns the variable.
            variable: Variable name to delete.

        Returns:
            None.
        """
        # RU: Удаляет ключ "module:variable" из LMDB в рамках write-транзакции.
        with self._env.begin(write=True) as txn:
            txn.delete(f"{module}:{variable}".encode())

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Return all variables belonging to a module as a dictionary.

        Performs a prefix-scan over the LMDB cursor, collecting every entry
        whose key starts with ``"<module>:"``, then strips the prefix to
        produce plain variable names as dictionary keys.

        Args:
            module: Logical namespace whose variables to collect.

        Returns:
            Mapping of variable names to their deserialised Python values.
            Empty dict if the module has no stored variables.
        """
        # RU: Сканирует курсор по префиксу "module:" и возвращает все переменные модуля.
        collection = {}
        prefix = f"{module}:".encode()
        with self._env.begin() as txn:
            cursor = txn.cursor()
            for key, value in cursor:
                if key.startswith(prefix):
                    # Strip the "module:" prefix to get the bare variable name.
                    # RU: Убираем префикс "module:", оставляя только имя переменной.
                    var_name = key.decode().split(":", 1)[1]
                    collection[var_name] = json.loads(value)
        return collection

    def get_modules(self) -> List[str]:
        """Return a deduplicated list of all module names stored in the database.

        Iterates the full LMDB cursor and extracts the module portion (the part
        before the first ``":"`` separator) from every key.

        Returns:
            List of unique module name strings in arbitrary order.
        """
        # RU: Обходит все ключи и возвращает список уникальных имён модулей.
        modules = set()
        with self._env.begin() as txn:
            cursor = txn.cursor()
            for key, _ in cursor:
                # RU: Берём часть ключа до первого ":" — это имя модуля.
                module = key.decode().split(":")[0]
                modules.add(module)
        return list(modules)

    def close(self) -> None:
        """Close the LMDB environment and release all associated resources.

        Returns:
            None.
        """
        # RU: Закрывает окружение LMDB и освобождает связанные ресурсы.
        self._env.close()

    def backup(self, target_path: Union[str, Path]) -> None:
        """Copy the LMDB directory to *target_path* as a consistent backup.

        Closes the environment before copying so the data files are in a
        consistent state, then reopens it afterwards so the instance remains
        usable. The copy is performed with ``shutil.copytree``.

        Args:
            target_path: Destination path for the backup directory; must not
                already exist (``copytree`` requirement).

        Returns:
            None.

        Raises:
            DatabaseError: When the copy or reopen operation fails for any reason.
        """
        # RU: Создаёт резервную копию директории LMDB.
        # RU: Закрывает окружение перед копированием для консистентности,
        # RU: затем снова открывает его, чтобы экземпляр остался рабочим.
        try:
            self._env.close()
            shutil.copytree(self._path, str(target_path))
            self._logger.info(f"LMDB backup: {target_path}")
            # Reopen the environment so the instance stays operational.
            # RU: Переоткрываем окружение после копирования.
            self._env = self._lmdb.open(self._path, map_size=10**9)
        except Exception as e:
            raise DatabaseError(f"LMDB backup failed: {e}") from e


__all__ = ["LMDBDatabase"]
