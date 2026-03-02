"""ZSYS configuration management — Pydantic-based base config.

Provides BaseConfig as the universal parent for all ZSYS project
configurations, with environment variable loading and .env file support.
"""
# RU: Управление конфигурацией ZSYS — базовый класс на Pydantic.
# RU: Поддержка переменных окружения и .env-файлов.

from .base import BaseConfig

__all__ = ["BaseConfig"]
