# core/http/retry.py — Retry логика для HTTP запросов
"""
Конфигурация и логика повторных попыток для HTTP запросов.
"""

import asyncio
import random
from dataclasses import dataclass, field
from typing import Callable, Optional, Set, Tuple, Any


@dataclass
class RetryConfig:
    """
    Конфигурация retry логики.
    
    Attributes:
        max_retries: Максимальное количество повторных попыток
        retry_statuses: HTTP статусы для retry (429, 500, 502, 503, 504)
        backoff_factor: Множитель для экспоненциальной задержки
        max_backoff: Максимальная задержка в секундах
        jitter: Добавлять случайный jitter к задержке
        retry_exceptions: Исключения для retry
    
    Example:
        config = RetryConfig(max_retries=5, backoff_factor=1.0)
    """
    max_retries: int = 3
    retry_statuses: Set[int] = field(default_factory=lambda: {429, 500, 502, 503, 504})
    backoff_factor: float = 0.5
    max_backoff: float = 60.0
    jitter: bool = True
    retry_exceptions: Tuple[type, ...] = field(
        default_factory=lambda: (ConnectionError, TimeoutError, asyncio.TimeoutError)
    )
    
    def get_delay(self, attempt: int) -> float:
        """
        Вычисляет задержку перед следующей попыткой.
        
        Args:
            attempt: Номер попытки (начиная с 0)
        
        Returns:
            Задержка в секундах
        """
        delay = self.backoff_factor * (2 ** attempt)
        delay = min(delay, self.max_backoff)
        
        if self.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay
    
    def should_retry_status(self, status: int) -> bool:
        """Проверяет, нужно ли retry для данного статуса."""
        return status in self.retry_statuses
    
    def should_retry_exception(self, exc: Exception) -> bool:
        """Проверяет, нужно ли retry для данного исключения."""
        return isinstance(exc, self.retry_exceptions)


async def retry_request(
    func: Callable,
    config: RetryConfig,
    *args,
    **kwargs
) -> Any:
    """
    Выполняет функцию с retry логикой.
    
    Args:
        func: Асинхронная функция для выполнения
        config: Конфигурация retry
        *args: Аргументы для func
        **kwargs: Keyword аргументы для func
    
    Returns:
        Результат выполнения func
    
    Raises:
        Последнее исключение после исчерпания попыток
    
    Example:
        config = RetryConfig(max_retries=3)
        result = await retry_request(make_request, config, url, headers=headers)
    """
    last_exception: Optional[Exception] = None
    
    for attempt in range(config.max_retries + 1):
        try:
            response = await func(*args, **kwargs)
            
            # Проверяем статус (если это HTTP response)
            status = getattr(response, "status", None) or getattr(response, "status_code", None)
            
            if status and config.should_retry_status(status) and attempt < config.max_retries:
                delay = config.get_delay(attempt)
                await asyncio.sleep(delay)
                continue
            
            return response
            
        except Exception as e:
            last_exception = e
            
            if not config.should_retry_exception(e):
                raise
            
            if attempt < config.max_retries:
                delay = config.get_delay(attempt)
                await asyncio.sleep(delay)
            else:
                raise
    
    if last_exception:
        raise last_exception


__all__ = [
    "RetryConfig",
    "retry_request",
]
