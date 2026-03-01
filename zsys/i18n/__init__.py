"""zsys.i18n - Internationalization module."""

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
