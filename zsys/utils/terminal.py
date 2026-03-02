# -*- coding: utf-8 -*-
"""Terminal utilities — shell command execution and system resource monitoring.

Provides async and synchronous helpers for running shell commands, as well as
functions for reading RAM and CPU consumption of the current process.
Belongs to the zsys.utils subsystem.
"""
# RU: Утилиты терминала — выполнение команд оболочки и мониторинг системных ресурсов.
# RU: Содержит async/sync обёртки над subprocess, а также чтение RAM и CPU процесса.

import os
import asyncio
from typing import Optional, Tuple, Union

try:
    from zsys._core import get_proc_mem_mb as _c_get_mem, get_proc_cpu_pct as _c_get_cpu, C_AVAILABLE as _C
except ImportError:
    _c_get_mem = _c_get_cpu = None
    _C = False


# ============================================================================
# SHELL EXECUTION
# RU: ВЫПОЛНЕНИЕ КОМАНД
# ============================================================================

async def shell_exec(
    command: str,
    executable: Optional[str] = None,
    timeout: Optional[Union[int, float]] = None,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
) -> Tuple[int, str, str]:
    """
    Execute shell command asynchronously.
    
    Args:
        command: Command to execute
        executable: Path to shell (e.g., /bin/bash)
        timeout: Maximum wait time in seconds
        stdout: Stream for stdout (default PIPE)
        stderr: Stream for stderr (default PIPE)
    
    Returns:
        tuple: (return_code, stdout, stderr)
    
    Raises:
        asyncio.TimeoutError: When timeout exceeded
    
    Example:
        code, out, err = await shell_exec("ls -la")
        code, out, err = await shell_exec("ping localhost", timeout=5)
    """
    # RU: Выполняет команду оболочки асинхронно.
    process = await asyncio.create_subprocess_shell(
        cmd=command,
        stdout=stdout,
        stderr=stderr,
        shell=True,
        executable=executable
    )
    
    try:
        stdout_data, stderr_data = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        process.kill()
        raise
    
    return (
        process.returncode or 0,
        stdout_data.decode() if stdout_data else "",
        stderr_data.decode() if stderr_data else ""
    )


def shell_exec_sync(
    command: str,
    timeout: Optional[Union[int, float]] = None,
) -> Tuple[int, str, str]:
    """
    Synchronous version of shell_exec.
    
    Args:
        command: Command to execute
        timeout: Maximum wait time in seconds
    
    Returns:
        tuple: (return_code, stdout, stderr)
    
    Example:
        code, out, err = shell_exec_sync("ls -la")
    """
    # RU: Синхронная версия shell_exec.
    import subprocess
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            timeout=timeout,
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as e:
        return -1, "", f"Timeout: {e}"


# ============================================================================
# SYSTEM RESOURCES
# RU: СИСТЕМНЫЕ РЕСУРСЫ
# ============================================================================

def get_ram_usage() -> float:
    """Get RAM usage by current process in MB.

    Uses C extension (reads /proc/self/status) when available, falls back to psutil.

    Returns:
        float: RAM usage in MB.
    """
    # RU: Возвращает использование RAM текущим процессом в МБ.
    if _C and _c_get_mem is not None:
        return round(_c_get_mem(), 1)
    try:
        import psutil
        current_process = psutil.Process(os.getpid())
        mem = current_process.memory_info()[0] / 2.0 ** 20
        for child in current_process.children(recursive=True):
            mem += child.memory_info()[0] / 2.0 ** 20
        return round(mem, 1)
    except Exception:
        return 0.0


def get_cpu_usage() -> float:
    """Get CPU usage by current process in %.

    Uses C extension (reads /proc/self/stat) when available, falls back to psutil.

    Returns:
        float: CPU usage in percent.
    """
    # RU: Возвращает использование CPU текущим процессом в процентах.
    if _C and _c_get_cpu is not None:
        return round(_c_get_cpu(), 1)
    try:
        import psutil
        current_process = psutil.Process(os.getpid())
        cpu = current_process.cpu_percent()
        for child in current_process.children(recursive=True):
            cpu += child.cpu_percent()
        return round(cpu, 1)
    except Exception:
        return 0.0


__all__ = [
    # Shell commands and async execution
    # RU: Команды оболочки и асинхронное выполнение
    "shell_exec",
    "shell_exec_sync",
    # System resource monitoring
    # RU: Мониторинг системных ресурсов
    "get_ram_usage",
    "get_cpu_usage",
]
