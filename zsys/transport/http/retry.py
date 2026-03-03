# core/http/retry.py — Retry логика для HTTP запросов
"""HTTP retry logic — configurable exponential backoff with jitter.

Provides RetryConfig dataclass and retry_request() coroutine that wraps
any async callable with configurable retries, status-based retry decisions,
and full exception type filtering.
"""
# RU: Логика повторных HTTP-запросов с экспоненциальной задержкой и jitter.
# RU: RetryConfig задаёт параметры; retry_request оборачивает любую async-функцию.

import asyncio
import random
from dataclasses import dataclass, field
from typing import Callable, Optional, Set, Tuple, Any


@dataclass
class RetryConfig:
    """Configuration for HTTP request retry behaviour.

    Attributes:
        max_retries: Maximum number of retry attempts (not counting the first try).
        retry_statuses: HTTP status codes that trigger a retry (default: 429,500,502,503,504).
        backoff_factor: Base multiplier for exponential delay formula
            ``backoff_factor * 2**attempt``.
        max_backoff: Upper bound for the computed delay in seconds.
        jitter: When ``True``, multiplies delay by a random factor in ``[0.5, 1.5)``
            to spread retries under load.
        retry_exceptions: Tuple of exception types that trigger a retry.

    Example::

        config = RetryConfig(max_retries=5, backoff_factor=1.0)
    """

    # RU: Конфигурация retry-логики для HTTP-запросов.
    max_retries: int = 3
    retry_statuses: Set[int] = field(default_factory=lambda: {429, 500, 502, 503, 504})
    backoff_factor: float = 0.5
    max_backoff: float = 60.0
    jitter: bool = True
    retry_exceptions: Tuple[type, ...] = field(
        default_factory=lambda: (ConnectionError, TimeoutError, asyncio.TimeoutError)
    )

    def get_delay(self, attempt: int) -> float:
        """Compute the wait duration before the next retry attempt.

        Uses the formula ``backoff_factor * 2**attempt``, capped at
        ``max_backoff``, optionally multiplied by a random factor when
        ``jitter`` is enabled.

        Args:
            attempt: Zero-based attempt index (0 = first retry).

        Returns:
            Delay in seconds as a float.
        """
        # RU: Вычисляет задержку по формуле backoff_factor * 2**attempt с ограничением max_backoff.
        delay = self.backoff_factor * (2**attempt)
        delay = min(delay, self.max_backoff)

        if self.jitter:
            # RU: Добавляем случайный jitter в диапазоне [0.5, 1.5) для распределения нагрузки.
            delay = delay * (0.5 + random.random())

        return delay

    def should_retry_status(self, status: int) -> bool:
        """Return ``True`` if the given HTTP status code warrants a retry.

        Args:
            status: HTTP response status code.

        Returns:
            ``True`` when *status* is in :attr:`retry_statuses`.
        """
        # RU: Возвращает True если статус-код входит в список для retry.
        return status in self.retry_statuses

    def should_retry_exception(self, exc: Exception) -> bool:
        """Return ``True`` if the given exception warrants a retry.

        Args:
            exc: Exception instance to check.

        Returns:
            ``True`` when *exc* is an instance of any type in :attr:`retry_exceptions`.
        """
        # RU: Возвращает True если тип исключения входит в retry_exceptions.
        return isinstance(exc, self.retry_exceptions)


async def retry_request(func: Callable, config: RetryConfig, *args, **kwargs) -> Any:
    """Execute *func* with automatic retry on failure.

    On each attempt, calls ``await func(*args, **kwargs)``.  If the response
    has a ``status`` / ``status_code`` attribute matching
    :attr:`RetryConfig.retry_statuses`, or if a retryable exception is raised,
    the coroutine waits :meth:`RetryConfig.get_delay` seconds before retrying.
    Non-retryable exceptions propagate immediately.

    Args:
        func: Async callable to execute.
        config: Retry configuration instance.
        *args: Positional arguments forwarded to *func*.
        **kwargs: Keyword arguments forwarded to *func*.

    Returns:
        The return value of *func* on success.

    Raises:
        Exception: The last exception raised after all retry attempts are
            exhausted, or any non-retryable exception immediately.

    Example::

        config = RetryConfig(max_retries=3)
        result = await retry_request(make_request, config, url, headers=headers)
    """
    # RU: Выполняет async-функцию с повторными попытками согласно config.
    last_exception: Optional[Exception] = None

    for attempt in range(config.max_retries + 1):
        try:
            response = await func(*args, **kwargs)

            # RU: Проверяем HTTP статус ответа (aiohttp → .status, httpx → .status_code).
            status = getattr(response, "status", None) or getattr(
                response, "status_code", None
            )

            if (
                status
                and config.should_retry_status(status)
                and attempt < config.max_retries
            ):
                delay = config.get_delay(attempt)
                await asyncio.sleep(delay)
                continue

            return response

        except Exception as e:
            last_exception = e

            if not config.should_retry_exception(e):
                raise  # RU: Немедленно пробрасываем не-retryable исключения.

            if attempt < config.max_retries:
                delay = config.get_delay(attempt)
                await asyncio.sleep(delay)
            else:
                raise  # RU: Все попытки исчерпаны — пробрасываем последнее исключение.

    if last_exception:
        raise last_exception


__all__ = [
    "RetryConfig",
    "retry_request",
]
