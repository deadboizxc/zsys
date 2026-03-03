# -*- coding: utf-8 -*-
"""Time utilities — formatting, conversion, and measurement helpers for zsys.

Provides Unix-timestamp conversion, human-readable duration strings,
duration string parsing (e.g. ``1h30m``), and uptime formatting.
C extension is used for ``human_time`` and ``parse_duration`` when available.
"""
# RU: Утилиты времени — форматирование, конвертация и измерение для zsys.
# RU: C-расширение применяется для human_time и parse_duration при наличии.

import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

try:
    from zsys._core import (
        human_time as _c_human_time,
        parse_duration as _c_parse_duration,
        C_AVAILABLE as _C,
    )
except ImportError:
    _C = False

__all__ = [
    "timestamp_to_date",
    "timestamp_to_datetime",
    "human_time",
    "human_time_delta",
    "current_timestamp",
    "time_difference",
    "parse_duration",
    "format_uptime",
]


def timestamp_to_date(
    timestamp: Union[int, float], fmt: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """Convert Unix timestamp to formatted date string.

    Args:
        timestamp: Unix timestamp.
        fmt: Date format string.

    Returns:
        str: Formatted date string.
    """
    # RU: Конвертирует Unix-метку времени в строку даты.
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime(fmt)


def timestamp_to_datetime(timestamp: Union[int, float]) -> datetime:
    """Convert Unix timestamp to datetime object.

    Args:
        timestamp: Unix timestamp.

    Returns:
        datetime: Datetime object.
    """
    # RU: Конвертирует Unix-метку времени в объект datetime.
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def human_time(seconds: Union[int, float], short: bool = True) -> str:
    """Convert seconds to human-readable time string.

    Args:
        seconds: Number of seconds.
        short: Use short format (d., h., min., sec.) or long format.

    Returns:
        str: Human-readable time string.
    """
    # RU: Конвертирует секунды в строку вида "1 дн. 2 ч.".
    if _C:
        return _c_human_time(int(seconds), short)
    seconds = int(seconds)
    delta = timedelta(seconds=seconds)
    parts = []

    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    if short:
        if days:
            parts.append(f"{days} дн.")
        if hours:
            parts.append(f"{hours} ч.")
        if minutes:
            parts.append(f"{minutes} мин.")
        if secs or not parts:
            parts.append(f"{secs} сек.")
    else:
        if days:
            parts.append(f"{days} {'день' if days == 1 else 'дней'}")
        if hours:
            parts.append(f"{hours} {'час' if hours == 1 else 'часов'}")
        if minutes:
            parts.append(f"{minutes} {'минута' if minutes == 1 else 'минут'}")
        if secs or not parts:
            parts.append(f"{secs} {'секунда' if secs == 1 else 'секунд'}")

    return " ".join(parts)


def human_time_delta(td: timedelta, short: bool = True) -> str:
    """Convert timedelta to human-readable string.

    Args:
        td: Timedelta object.
        short: Use short format.

    Returns:
        str: Human-readable time string.
    """
    # RU: Конвертирует timedelta в читаемую строку.
    return human_time(int(td.total_seconds()), short=short)


def current_timestamp() -> int:
    """Get current Unix timestamp.

    Returns:
        int: Current Unix timestamp.
    """
    # RU: Возвращает текущую Unix-метку времени.
    return int(time.time())


def time_difference(
    timestamp1: Union[int, float], timestamp2: Union[int, float]
) -> int:
    """Calculate absolute difference between two timestamps.

    Args:
        timestamp1: First timestamp.
        timestamp2: Second timestamp.

    Returns:
        int: Absolute difference in seconds.
    """
    # RU: Возвращает абсолютную разницу между двумя метками времени в секундах.
    return abs(int(timestamp1 - timestamp2))


def parse_duration(text: str) -> Optional[int]:
    """Parse duration string to seconds.

    Supports formats like: 1h, 30m, 1d, 2w, 1h30m

    Args:
        text: Duration string.

    Returns:
        int: Duration in seconds, or None if invalid.
    """
    # RU: Парсит строку длительности в секунды.
    if _C:
        return _c_parse_duration(text)
    import re

    units = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
        "w": 604800,
    }

    # Try single unit: "30m", "2h"
    # RU: Пробуем формат с одной единицей: "30m", "2h"
    match = re.match(r"^(\d+)([smhdw])$", text.lower())
    if match:
        value, unit = match.groups()
        return int(value) * units[unit]

    # Try combined: "1h30m", "2d12h"
    # RU: Пробуем комбинированный формат: "1h30m", "2d12h"
    total = 0
    pattern = re.compile(r"(\d+)([smhdw])")
    matches = pattern.findall(text.lower())
    if matches:
        for value, unit in matches:
            total += int(value) * units[unit]
        return total if total > 0 else None

    return None


def format_uptime(start_time: Union[int, float]) -> str:
    """Format uptime from start timestamp.

    Args:
        start_time: Start Unix timestamp.

    Returns:
        str: Human-readable uptime string.
    """
    # RU: Форматирует время работы с момента запуска.
    uptime_seconds = current_timestamp() - int(start_time)
    return human_time(uptime_seconds)
