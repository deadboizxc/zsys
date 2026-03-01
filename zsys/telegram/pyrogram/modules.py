"""Pyrogram Module Management

Utilities for loading, unloading, and managing Pyrogram modules.
"""
# RU: Управление Pyrogram-модулями — загрузка, выгрузка, перезагрузка.

import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogram import Client


def get_module_path(module_name: str = "", core: bool = False) -> Path:
    """
    Get the path to a module file.
    
    Args:
        module_name: Name of the module (without .py extension)
        core: If True, look in core modules directory
    
    Returns:
        Path to module file (or directory if module_name is empty)
    """
    # RU: Получить путь к файлу модуля.
    if core:
        base = Path.cwd() / "modules"
    else:
        base = Path.cwd() / "custom_modules"

    if module_name:
        return base / f"{module_name}.py"
    return base


def get_module_dir(module_name: str = "", core: bool = False) -> Path:
    """Alias for get_module_path."""
    # RU: Псевдоним для get_module_path.
    return get_module_path(module_name, core)


def find_modules(directory: Optional[Path] = None) -> List[str]:
    """
    Find all modules in a directory.
    
    Args:
        directory: Directory to search (defaults to modules/)
    
    Returns:
        List of module names
    """
    # RU: Найти все модули в директории.
    if directory is None:
        directory = Path.cwd() / "modules"
    
    modules = []
    if directory.exists():
        for item in directory.iterdir():
            if item.is_file() and item.suffix == ".py" and not item.name.startswith("__"):
                modules.append(item.stem)
            elif item.is_dir() and (item / "__init__.py").exists():
                modules.append(item.name)
    
    return modules


async def load_module(
    module_name: str,
    client: Optional[Any] = None,
    core: bool = False,
    message: Optional[Any] = None,
) -> Optional[Any]:
    """Asynchronously load a module by name.

    Args:
        module_name: Module name (without .py extension).
        client: Pyrogram Client instance, exposed as app/client inside the module.
        core: If True, load from modules/; otherwise from custom_modules/.
        message: Optional message object for error reporting.

    Returns:
        Loaded module object, or None on failure.
    """
    # RU: Асинхронно загружает модуль по имени.
    base_dir = Path.cwd() / ("modules" if core else "custom_modules")
    # Search for the module as a .py file or as a package directory
    # RU: Ищем файл или пакет
    file_path = base_dir / f"{module_name}.py"
    pkg_path  = base_dir / module_name / "__init__.py"

    try:
        if file_path.exists():
            spec = importlib.util.spec_from_file_location(module_name, file_path)
        elif pkg_path.exists():
            spec = importlib.util.spec_from_file_location(
                module_name, pkg_path,
                submodule_search_locations=[str(base_dir / module_name)],
            )
        else:
            print(f"Module not found: {module_name}")
            return None

        if not spec or not spec.loader:
            return None

        module = importlib.util.module_from_spec(spec)
        # Expose the client inside the loaded module's namespace
        # RU: Делаем client доступным внутри модуля
        if client is not None:
            module.app    = client  # type: ignore[attr-defined]
            module.client = client  # type: ignore[attr-defined]
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Register old-style @Client.on_message handlers with the client
        if client is not None:
            for obj in vars(module).values():
                if callable(obj) and hasattr(obj, "handlers") and isinstance(obj.handlers, (list, tuple)):
                    for handler, group in obj.handlers:
                        try:
                            client.add_handler(handler, group)
                        except Exception:
                            pass

        return module
    except Exception as e:
        print(f"Failed to load module {module_name}: {e}")
        return None


async def unload_module(module_name: str, client: Optional[Any] = None) -> bool:
    """
    Unload a module from sys.modules.

    Args:
        module_name: Name of module to unload
        client:      Pyrogram client (used to remove handlers if provided)

    Returns:
        True if successful
    """
    # RU: Выгрузить модуль из sys.modules.
    if client is not None:
        # Remove handlers registered by this module
        try:
            mod = sys.modules.get(module_name)
            if mod:
                for obj in vars(mod).values():
                    if callable(obj) and hasattr(obj, "handlers") and isinstance(obj.handlers, (list, tuple)):
                        for handler, group in obj.handlers:
                            try:
                                client.remove_handler(handler, group)
                            except Exception:
                                pass
        except Exception:
            pass
    if module_name in sys.modules:
        del sys.modules[module_name]
        return True
    return False


async def reload_modules(
    module_name: str,
    client=None,
    message=None,
    core: bool = False,
) -> bool:
    """Reload a module: remove old handlers, reimport, and register new ones.

    Args:
        module_name: Module name (without .py extension).
        client: Pyrogram client used for handler registration.
        message: Optional message object for error output.
        core: If True, look in modules/; otherwise in custom_modules/.

    Returns:
        True on success, False on failure.
    """
    # RU: Перезагружает модуль: снимает старые хендлеры, импортирует заново, регистрирует новые.
    module_path = get_module_path(module_name, core=core)
    if not module_path.exists():
        return False

    # Remove old handlers to prevent duplicate registration after reload
    # RU: Снимаем старые хендлеры если клиент доступен
    old_module = sys.modules.get(module_name)
    if old_module and client is not None:
        for obj in vars(old_module).values():
            if callable(obj) and hasattr(obj, "handlers"):
                for handler, group in obj.handlers:
                    try:
                        client.remove_handler(handler, group)
                    except Exception:
                        pass

    # Reload the module from disk using a fresh module spec
    # RU: Перезагружаем модуль с диска
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if not spec or not spec.loader:
            return False
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception as e:
        print(f"Failed to reload {module_name}: {e}")
        return False

    # Register handlers defined in the freshly loaded module
    # RU: Регистрируем новые хендлеры
    if client is not None:
        for obj in vars(module).values():
            if callable(obj) and hasattr(obj, "handlers"):
                for handler, group in obj.handlers:
                    client.add_handler(handler, group)

    return True


def reload_all_modules(client=None) -> Dict[str, bool]:
    """
    Reload all loaded modules.
    
    Returns:
        Dictionary of results {module_name: success}
    """
    # RU: Перезагрузить все загруженные модули.
    results = {}
    for name in list(sys.modules.keys()):
        if not name.startswith("_") and "." not in name:
            try:
                importlib.reload(sys.modules[name])
                results[name] = True
            except Exception:
                results[name] = False
    return results


def is_module_enabled(module_name: str, core: bool = False) -> bool:
    """Check whether a module exists on disk and is not disabled.

    Args:
        module_name: Module name to check.
        core: If True, look in modules/; otherwise in custom_modules/.

    Returns:
        True if the module file is found and not marked as disabled.
    """
    # RU: Проверяет, существует ли модуль на диске (не отключён).
    base_dir = Path.cwd() / ("modules" if core else "custom_modules")
    # Skip modules that have a corresponding .disabled marker file
    # RU: Поддержка disabled-файлов (module.disabled)
    if (base_dir / f"{module_name}.disabled").exists():
        return False
    return (
        (base_dir / f"{module_name}.py").exists()
        or (base_dir / module_name / "__init__.py").exists()
    )


def is_package_installed(package_name: str) -> bool:
    """
    Check if a package is installed.
    
    Args:
        package_name: Name of package
    
    Returns:
        True if package is installed
    """
    # RU: Проверить, установлен ли пакет.
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False


def install_requirements(requirements_file: str) -> bool:
    """
    Install requirements from a file.
    
    Args:
        requirements_file: Path to requirements.txt
    
    Returns:
        True if successful
    """
    # RU: Установить зависимости из файла требований.
    try:
        import subprocess
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file],
            check=True
        )
        return True
    except Exception as e:
        print(f"Failed to install requirements: {e}")
        return False


def import_library(library_name: str) -> Optional[Any]:
    """
    Dynamically import a library.
    
    Args:
        library_name: Name of library to import
    
    Returns:
        Imported library or None if failed
    """
    # RU: Динамически импортировать библиотеку.
    try:
        return importlib.import_module(library_name)
    except ImportError:
        return None


# Module registry and help
try:
    from zsys.modules import modules_help
except ImportError:
    modules_help: Dict[str, Dict[str, str]] = {}  # type: ignore[assignment]
requirements_list: Dict[str, List[str]] = {}


__all__ = [
    "get_module_path",
    "get_module_dir",
    "find_modules",
    "load_module",
    "unload_module",
    "reload_modules",
    "reload_all_modules",
    "is_module_enabled",
    "is_package_installed",
    "install_requirements",
    "import_library",
    "modules_help",
    "requirements_list",
]
