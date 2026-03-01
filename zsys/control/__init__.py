"""
Core Control Module - Process management utilities.

Provides cross-platform process control, restart, and update functionality.
"""

from .control import (
    restart_process,
    stop_process,
    replace_executable,
    get_current_file,
    find_new_file,
    is_frozen,
)

__all__ = [
    'restart_process',
    'stop_process',
    'replace_executable', 
    'get_current_file',
    'find_new_file',
    'is_frozen',
]
