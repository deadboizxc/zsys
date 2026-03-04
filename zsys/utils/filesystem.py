# -*- coding: utf-8 -*-
"""
Filesystem utilities - paths, platform detection, frozen state.

Combined utilities for:
- Project paths and resource management
- Frozen state detection (PyInstaller, Nuitka, cx_Freeze)
- Platform detection (Android, Termux, OS info)
"""
# RU: Утилиты файловой системы — пути к ресурсам, обнаружение платформы и состояния заморозки.

import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Dict, Literal, Optional, Union

# ============================================================================
# FROZEN STATE DETECTION
# ============================================================================


def is_frozen() -> bool:
    """
    Check if code is running in frozen state (compiled executable).

    Supports:
    - PyInstaller (sys.frozen, sys._MEIPASS)
    - cx_Freeze (sys.importers)
    - Nuitka (__compiled__)

    Returns:
        bool: True if running from compiled executable

    Example:
        if is_frozen():
            base_path = sys._MEIPASS
        else:
            base_path = os.getcwd()
    """
    # RU: Проверяет атрибуты sys и глобальный флаг __compiled__ для определения типа сборки.
    frozen_attrs: tuple[
        Literal["frozen"], Literal["_MEIPASS"], Literal["importers"]
    ] = (
        "frozen",  # RU: PyInstaller
        "_MEIPASS",  # RU: PyInstaller — временная папка с ресурсами
        "importers",  # RU: cx_Freeze
    )

    return (
        getattr(sys, "frozen", False)
        or any(hasattr(sys, attr) for attr in frozen_attrs)
        or globals().get(
            "__compiled__", False
        )  # RU: Nuitka устанавливает этот глобальный флаг
    )


def get_frozen_info() -> dict:
    """
    Get detailed frozen state information.

    Returns:
        dict: Information about frozen state and bundler type
    """
    # RU: Определяет тип сборщика по наличию характерных атрибутов и флагов.
    bundler = None

    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            bundler = "pyinstaller"
        elif hasattr(sys, "importers"):
            bundler = "cx_freeze"
        else:
            bundler = "unknown"
    elif globals().get("__compiled__", False):
        bundler = "nuitka"

    return {
        "is_frozen": is_frozen(),
        "bundler": bundler,
        "executable": sys.executable,
        "argv": sys.argv,
    }


# ============================================================================
# PLATFORM DETECTION
# ============================================================================


def is_android() -> bool:
    """
    Check if code is running on Android (Termux).

    Returns:
        bool: True if running on Android
    """
    # RU: Проверяет строку платформы на наличие подстроки 'android'.
    return "android" in platform.platform().lower()


def is_termux() -> bool:
    """
    Check if code is running in Termux.

    Returns:
        bool: True if running in Termux
    """
    # RU: Termux устанавливает PREFIX=/data/data/com.termux/files/usr.
    return os.environ.get("PREFIX", "").startswith("/data/data/com.termux")


def get_platform_info() -> Dict[str, str]:
    """
    Get information about current platform.

    Returns:
        dict: System information

    Example:
        info = get_platform_info()
        print(f"OS: {info['system']} {info['release']}")
    """
    # RU: Собирает системную информацию и флаги Android/Termux/заморозки в единый словарь.
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "is_android": str(is_android()),
        "is_frozen": str(is_frozen()),
        "is_termux": str(is_termux()),
    }


def get_home_dir() -> str:
    """Get user home directory.

    Returns:
        str: Absolute path to the current user's home directory.
    """
    # RU: Возвращает домашнюю директорию текущего пользователя через os.path.expanduser.
    return os.path.expanduser("~")


def get_temp_dir() -> str:
    """Get system temporary directory.

    Returns:
        str: Absolute path to the system temporary directory.
    """
    # RU: Возвращает временную директорию ОС через модуль tempfile.
    import tempfile

    return tempfile.gettempdir()


# ============================================================================
# PROJECT PATHS
# ============================================================================

# Global variable for project root
_PROJECT_ROOT: Optional[Path] = None


def _detect_project_root() -> Path:
    """
    Auto-detect project root.

    Priority:
    1. __main__ module directory (where script is executed)
    2. Current working directory (cwd)
    """
    # RU: Приоритет отдаётся __main__.__file__, чтобы корень совпадал с точкой запуска.
    main_module = sys.modules.get("__main__")
    if main_module and hasattr(main_module, "__file__") and main_module.__file__:
        return Path(main_module.__file__).parent.resolve()
    return Path.cwd().resolve()


def get_project_root() -> Path:
    """
    Get project root directory.

    Returns:
        Path: Project root path (where main.py is located)
    """
    # RU: Кэширует результат в _PROJECT_ROOT, чтобы избежать повторного обнаружения.
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        _PROJECT_ROOT = _detect_project_root()
    return _PROJECT_ROOT


def set_project_root(path: Union[str, Path]) -> None:
    """
    Manually set project root.

    Args:
        path: Path to project root

    Example:
        set_project_root(Path(__file__).parent)
    """
    # RU: Принудительно перезаписывает кэшированный корень проекта указанным путём.
    global _PROJECT_ROOT
    _PROJECT_ROOT = Path(path).resolve()


def resource_path(relative_path: Union[str, Path]) -> str:
    """
    Get absolute path to a resource.

    Works in both normal and PyInstaller frozen mode.
    Path is relative to PROJECT_ROOT.

    Args:
        relative_path: Relative path to resource

    Returns:
        str: Absolute path to resource

    Example:
        font_path = resource_path("fonts/Arial.ttf")
        config_path = resource_path(Path("config") / "settings.json")
    """
    # RU: В режиме заморозки PyInstaller распаковывает ресурсы в _MEIPASS, иначе — корень проекта.
    if is_frozen():
        # PyInstaller creates temp folder _MEIPASS
        base_path = Path(
            getattr(sys, "_MEIPASS", get_project_root())
        )  # RU: _MEIPASS — временная папка с распакованными ресурсами
    else:
        base_path = get_project_root()

    return str(base_path / relative_path)


def userdata_path(
    relative_path: Union[str, Path] = "", subfolder: str = "", create: bool = True
) -> str:
    """
    Get path to file/folder in userdata directory.

    Path relative to PROJECT_ROOT/userdata/.

    Args:
        relative_path: Relative path inside userdata
        subfolder: Subfolder inside userdata (sessions, database, config, etc.)
        create: Create directory if doesn't exist

    Returns:
        str: Absolute path to resource in userdata

    Example:
        db_path = userdata_path("app.sqlite3", subfolder="database")
        config_path = userdata_path("settings.json", subfolder="config")
        session_path = userdata_path("user.session", subfolder="sessions")
    """
    # RU: Создаёт иерархию userdata/{subfolder}/ и возвращает абсолютный путь к файлу.
    userdata_folder = get_project_root() / "userdata"

    if subfolder:
        base_folder = userdata_folder / subfolder
    else:
        base_folder = userdata_folder

    if create:
        base_folder.mkdir(parents=True, exist_ok=True)

    if relative_path:
        return str((base_folder / relative_path).resolve())
    else:
        return str(base_folder.resolve())


def get_ffmpeg_paths() -> Dict[str, Optional[str]]:
    """
    Get paths to ffmpeg and ffprobe.

    Searches in project bin/ directory first, then in system PATH.

    Returns:
        dict: Dict with 'ffmpeg' and 'ffprobe' keys, values are paths or None

    Example:
        paths = get_ffmpeg_paths()
        if paths["ffmpeg"]:
            subprocess.run([paths["ffmpeg"], "-i", "input.mp4"])
    """
    # RU: Ищет бинарники в bin/ffmpeg/{os}/, при отсутствии — fallback на системный PATH.
    os_type = platform.system().lower()
    exe_suffix = ".exe" if os_type == "windows" else ""
    executables = ["ffmpeg", "ffprobe"]
    paths: Dict[str, Optional[str]] = {}

    # On Android use only system binaries
    if is_android():
        return {exe: shutil.which(f"{exe}{exe_suffix}") for exe in executables}

    # Determine bin directory
    bin_dir = (
        "win64"
        if os_type == "windows"
        else "linux64"
        if os_type == "linux"
        else "darwin64"
    )

    for exe in executables:
        # Search in project bin/ first
        if is_frozen():
            custom_dir = (
                Path(getattr(sys, "_MEIPASS", get_project_root()))
                / "bin"
                / "ffmpeg"
                / bin_dir
            )
        else:
            custom_dir = get_project_root() / "bin" / "ffmpeg" / bin_dir

        custom_path = custom_dir / f"{exe}{exe_suffix}"

        if custom_path.exists():
            paths[exe] = str(custom_path)
        else:
            # Fallback to system PATH
            paths[exe] = shutil.which(f"{exe}{exe_suffix}")

    return paths


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Create directory if it does not exist.

    Args:
        path: Path to directory

    Returns:
        Path: Created directory Path object
    """
    # RU: Создаёт директорию со всеми промежуточными уровнями без ошибки при существующем пути.
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


__all__ = [
    # Frozen state
    "is_frozen",
    "get_frozen_info",
    # Platform detection
    "is_android",
    "is_termux",
    "get_platform_info",
    "get_home_dir",
    "get_temp_dir",
    # Project paths
    "get_project_root",
    "set_project_root",
    "resource_path",
    "userdata_path",
    "get_ffmpeg_paths",
    "ensure_dir",
]
