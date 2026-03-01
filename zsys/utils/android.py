# -*- coding: utf-8 -*-
"""Android detection utilities for zsys core.

Provides functions to detect if code is running on Android (e.g., Termux).
"""

import platform
from typing import Final


def is_android() -> bool:
    """Check if the code is running on Android (e.g., in Termux).
    
    Returns:
        bool: True if running on Android, False otherwise.
    
    Examples:
        >>> if is_android():
        ...     print("Running on Android")
    """
    system: Final[str] = platform.system().lower()
    release: Final[str] = platform.release().lower()
    machine: Final[str] = platform.machine().lower()
    
    # Check by system name and release
    is_android_os = ("android" in system) or ("android" in release)
    
    # Check by architecture (aarch64, armv8, armv7, etc.)
    is_android_arch = (
        machine in ("aarch64", "armv8", "armv8l", "armv7l", "armv7")
        or machine.startswith("arm")
    )
    
    return is_android_os or is_android_arch


def get_platform_info() -> dict:
    """Get detailed platform information.
    
    Returns:
        dict: Platform information including system, release, machine, and android status.
    """
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "is_android": is_android()
    }
