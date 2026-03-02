"""zsys.i18n - Internationalization module.

Provides locale-aware translation utilities for the ZSYS ecosystem.
Supports per-instance and global translation contexts, dynamic language
switching, and a convenient shorthand ``t()`` for string lookup.
"""
# RU: Модуль интернационализации ZSYS.
# RU: Поддерживает локальные и глобальные контексты перевода,
# RU: динамическое переключение языка и быстрый вызов t() для поиска строк.

from .i18n import (
    I18N,
    get_translation,
    set_language,
    GlobalI18N,
    init_global_i18n as init_i18n,
    register_i18n,
    global_t as t,
)

__all__ = [
    "I18N",
    "get_translation",
    "set_language",
    "GlobalI18N",
    "init_i18n",
    "register_i18n",
    "t",
]
