# core/db/pickledb.py — PickleDB драйвер
"""PickleDB storage backend — pickle-based key-value file database.

Implements the ``Database`` interface using the ``pickledb`` library.
All write operations persist immediately via an automatic ``save()`` call,
so no explicit flush is required by the caller.
"""
# RU: PickleDB бэкенд хранилища — файловая key-value БД на основе pickle.
# RU: Реализует интерфейс Database; каждая запись автоматически сохраняется на диск.

import shutil
from pathlib import Path
from typing import Any, Dict, List, Union

from .base import Database, DatabaseError


class PickleDBDatabase(Database):
    """PickleDB implementation of the Database interface.

    Stores every entry under a composite key formatted as ``"module:variable"``.
    Every mutating operation calls ``save()`` immediately, guaranteeing that the
    on-disk file is always up-to-date after each write.

    Attributes:
        _path: Absolute string path to the pickle file on disk.
        _db: Underlying ``PickleDB`` instance used for all storage operations.
    """

    # RU: Реализация Database на основе PickleDB.
    # RU: Ключи хранятся в формате "module:variable"; каждая запись сразу сохраняется на диск.

    def __init__(self, path: Union[str, Path]):
        """Initialize a PickleDB database at the given file path.

        Creates all missing parent directories before opening the file.

        Args:
            path: Path to the pickle database file. The file is created if it
                does not exist; parent directories are created automatically.

        Raises:
            ImportError: When the ``pickledb`` package is not installed.
            DatabaseError: When the underlying ``PickleDB`` constructor fails
                for any reason (e.g. corrupted file, permission error).
        """
        # RU: Инициализация PickleDB: создаём родительские директории и открываем файл.
        super().__init__()
        try:
            from pickledb import PickleDB
        except ImportError:
            raise ImportError(
                "pickledb не установлен. Установите: pip install pickledb"
            )

        self._path = str(path)
        Path(self._path).parent.mkdir(
            parents=True, exist_ok=True
        )  # RU: Создаём директории при необходимости.

        try:
            self._db = PickleDB(self._path)
        except Exception as e:
            raise DatabaseError(f"Не удалось открыть PickleDB: {e}") from e

    def get(self, module: str, variable: str, default: Any = None) -> Any:
        """Retrieve a value from the database.

        Args:
            module: Logical namespace that groups related variables.
            variable: Name of the variable within ``module``.
            default: Value returned when the key is absent. Defaults to ``None``.

        Returns:
            The stored value for ``module:variable``, or ``default`` if the key
            does not exist.
        """
        # RU: Читаем значение по составному ключу; возвращаем default при отсутствии.
        key = f"{module}:{variable}"
        value = self._db.get(key)
        return default if value is None else value

    def set(self, module: str, variable: str, value: Any) -> None:
        """Store a value and immediately persist the database to disk.

        Args:
            module: Logical namespace that groups related variables.
            variable: Name of the variable within ``module``.
            value: Arbitrary picklable object to store.
        """
        # RU: Записываем значение и сразу сохраняем файл на диск.
        key = f"{module}:{variable}"
        self._db.set(key, value)
        self._db.save()  # RU: Авто-сохранение после каждой записи.

    def remove(self, module: str, variable: str) -> None:
        """Delete a key from the database and immediately persist the change.

        Args:
            module: Logical namespace that groups related variables.
            variable: Name of the variable within ``module`` to remove.
        """
        # RU: Удаляем ключ и сразу сохраняем файл на диск.
        key = f"{module}:{variable}"
        self._db.remove(key)
        self._db.save()  # RU: Авто-сохранение после удаления.

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Return all variables stored under a given module namespace.

        Iterates over every key in the database and collects those that start
        with the ``"module:"`` prefix, stripping the prefix from the returned
        dict keys.

        Args:
            module: Logical namespace whose variables should be collected.

        Returns:
            A dictionary mapping variable names to their stored values.
            Returns an empty dict when no keys match the prefix.
        """
        # RU: Собираем все ключи с префиксом "module:" в словарь {variable: value}.
        result = {}
        prefix = f"{module}:"
        for key in self._db.all():
            if key.startswith(prefix):
                var_name = key.split(":", 1)[1]  # RU: Отрезаем префикс модуля.
                result[var_name] = self._db.get(key)
        return result

    def get_modules(self) -> List[str]:
        """Return a deduplicated list of all module namespaces present in the database.

        Returns:
            List of unique module name strings derived from the ``"module:variable"``
            key format. Keys without a colon separator are ignored.
        """
        # RU: Извлекаем уникальные имена модулей из всех ключей формата "module:variable".
        modules = set()
        for key in self._db.all():
            if ":" in key:
                module = key.split(":", 1)[0]  # RU: Берём часть до первого двоеточия.
                modules.add(module)
        return list(modules)

    def close(self) -> None:
        """Flush all pending changes to disk and close the database.

        It is safe to call this method multiple times; subsequent calls are
        no-ops from the caller's perspective.
        """
        # RU: Сохраняем все изменения на диск при закрытии.
        self._db.save()

    def backup(self, target_path: Union[str, Path]) -> None:
        """Copy the current database file to a backup location.

        Flushes the database to disk before copying to ensure the backup
        reflects the latest state.

        Args:
            target_path: Destination file path for the backup copy.

        Raises:
            DatabaseError: When the file copy operation fails for any reason
                (e.g. permission denied, disk full).
        """
        # RU: Сохраняем БД и копируем файл в указанное место для резервной копии.
        try:
            self._db.save()
            shutil.copy(self._path, str(target_path))
            self._logger.info(f"PickleDB backup: {target_path}")
        except Exception as e:
            raise DatabaseError(f"PickleDB backup failed: {e}") from e


__all__ = ["PickleDBDatabase"]
