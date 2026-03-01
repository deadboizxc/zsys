"""
Core Control Module - Process management utilities for zsys ecosystem.

Provides:
- Process restart functionality
- Graceful shutdown
- Hot-reload support
- Cross-platform process management
"""

import os
import sys
import glob
import time
import platform
import subprocess
import tempfile
import asyncio
from typing import NoReturn, Optional, Any, Callable
from multiprocessing import Process

# Global state
_is_stopping: bool = False
_restart_event = asyncio.Event()
_restart_event.set()  # Allow first restart

__all__ = [
    'restart_process',
    'stop_process', 
    'replace_executable',
    'get_current_file',
    'find_new_file',
    'is_frozen',
]


def is_frozen() -> bool:
    """Check if running as frozen executable (PyInstaller/cx_Freeze)."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_current_file() -> str:
    """Get path to current executable file."""
    if is_frozen():
        return sys.executable
    return os.path.abspath(sys.argv[0])


def find_new_file(pattern: str, exclude_current: bool = True) -> Optional[str]:
    """
    Find new file matching glob pattern.
    
    Args:
        pattern: Glob pattern to match files (e.g., "app_*.exe")
        exclude_current: Whether to exclude current executable from results
        
    Returns:
        Path to first matching file, or None if not found
    """
    current_file = get_current_file() if exclude_current else None
    files = glob.glob(pattern)
    
    if exclude_current and current_file:
        files = [f for f in files if f != current_file]
    
    return files[0] if files else None


def _get_script_extension() -> str:
    """Get OS-specific script extension."""
    system = platform.system().lower()
    if system == "windows":
        return ".bat"
    elif system in ["linux", "darwin"]:
        return ".sh"
    else:
        raise NotImplementedError(f"Unsupported OS: {system}")


def _start_new_process():
    """Start new process with same arguments."""
    python = sys.executable
    os.execv(python, [python] + sys.argv)


async def restart_process(
    cleanup_callback: Optional[Callable[[], Any]] = None,
    delay: float = 3.0
) -> NoReturn:
    """
    Restart current process.
    
    Args:
        cleanup_callback: Optional async/sync function to call before restart
        delay: Delay in seconds before starting new process
    """
    global _restart_event
    
    if not _restart_event.is_set():
        return  # Already restarting
    
    _restart_event.clear()
    
    # Run cleanup if provided
    if cleanup_callback:
        if asyncio.iscoroutinefunction(cleanup_callback):
            await cleanup_callback()
        else:
            cleanup_callback()
    
    await asyncio.sleep(delay)
    
    # Start new process
    process = Process(target=_start_new_process)
    process.start()
    process.join()
    
    os._exit(0)


async def stop_process(
    cleanup_callback: Optional[Callable[[], Any]] = None,
    exit_code: int = 0,
    force_exit: bool = True
) -> None:
    """
    Gracefully stop current process.
    
    Args:
        cleanup_callback: Optional async/sync function for cleanup
        exit_code: Exit code for process termination
        force_exit: If True, use os._exit() for immediate termination
    """
    global _is_stopping
    
    if _is_stopping:
        return
    
    _is_stopping = True
    
    try:
        if cleanup_callback:
            if asyncio.iscoroutinefunction(cleanup_callback):
                await cleanup_callback()
            else:
                cleanup_callback()
    except Exception as e:
        print(f"Error during cleanup: {e}")
    
    if force_exit:
        os._exit(exit_code)
    else:
        sys.exit(exit_code)


async def replace_executable(
    new_file: str,
    cleanup_callback: Optional[Callable[[], Any]] = None,
    delete_old: bool = True,
    delay: float = 5.0
) -> NoReturn:
    """
    Replace current executable with new one.
    
    Stops current process, starts new executable, and optionally deletes old one.
    
    Args:
        new_file: Path to new executable file
        cleanup_callback: Optional async/sync function for cleanup
        delete_old: Whether to delete old executable after starting new one
        delay: Delay before starting new executable
    """
    current_pid = os.getpid()
    current_file = get_current_file()
    
    # Run cleanup
    if cleanup_callback:
        if asyncio.iscoroutinefunction(cleanup_callback):
            await cleanup_callback()
        else:
            cleanup_callback()
    
    await asyncio.sleep(delay)
    
    script_ext = _get_script_extension()
    
    # Generate restart script
    if script_ext == ".bat":
        script_content = f"""@echo off
timeout /t 5 >nul
start "" "{new_file}"
timeout /t 3 >nul
taskkill /F /PID {current_pid} >nul 2>&1
"""
        if delete_old:
            script_content += f'timeout /t 2 >nul\ndel /f /q "{current_file}"\n'
        script_content += "exit 0\n"
    else:
        script_content = f"""#!/bin/bash
sleep 5
"{new_file}"
sleep 3
kill -9 {current_pid}
"""
        if delete_old:
            script_content += f'rm -f "{current_file}"\n'
        script_content += "exit 0\n"
    
    script_path = os.path.join(tempfile.gettempdir(), f"restart_script{script_ext}")
    
    with open(script_path, "w") as f:
        f.write(script_content)
    
    if script_ext == ".sh":
        os.chmod(script_path, 0o755)
    
    # Launch restart script
    if script_ext == ".bat":
        process = await asyncio.to_thread(
            subprocess.Popen,
            ["cmd.exe", "/c", script_path],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    else:
        process = await asyncio.to_thread(
            subprocess.Popen,
            ["bash", script_path]
        )
    
    await asyncio.to_thread(process.communicate)
    os._exit(0)
