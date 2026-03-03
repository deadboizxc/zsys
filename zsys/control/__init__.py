"""Control package — process management exports for zsys.

Re-exports restart_process, stop_process, replace_executable,
get_current_file, find_new_file, and is_frozen from the control module.
"""
# RU: Пакет управления процессами — перезапуск, остановка, горячая замена.

from .control import (
    restart_process,
    stop_process,
    replace_executable,
    get_current_file,
    find_new_file,
    is_frozen,
)

__all__ = [
    "restart_process",
    "stop_process",
    "replace_executable",
    "get_current_file",
    "find_new_file",
    "is_frozen",
]
