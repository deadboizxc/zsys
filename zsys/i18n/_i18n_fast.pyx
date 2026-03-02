# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
"""Hot-path Cython extensions for zsys i18n.

Typed Cython implementations of the three most-called i18n functions.
Serves as the intermediate tier between pure Python and the C extension:

  Tier 1 — C extension ``_zsys_core`` (fastest, requires gcc at install).
  Tier 2 — Cython ``_i18n_fast.so``  (this file, ~10-30x vs pure Python).
  Tier 3 — Pure Python               (always available as fallback).

Functions
---------
deep_merge_c      : Recursive dict merge. Used at startup for locale loading.
nested_get_c      : Dot-notation key traversal. Fallback when C ext absent.
i18n_get_c        : Full translate-with-language-fallback hot path.

These are drop-in replacements for the pure-Python equivalents in i18n.py.
"""
# RU: Горячие пути i18n на Cython. Промежуточный уровень между чистым
# Python и C-расширением _zsys_core. drop-in замена для i18n.py.


cpdef dict deep_merge_c(dict base, dict override):
    """Recursively merge *override* into *base*, returning a new dict.

    Nested dicts are merged; all other values are overwritten.
    Neither input dict is modified.

    Args:
        base: Base dictionary.
        override: Dictionary whose values take precedence over *base*.

    Returns:
        New merged dict.

    # RU: Рекурсивно объединяет override в base, возвращая новый словарь.
    # RU: Вложенные словари объединяются, остальные значения перезаписываются.
    """
    cdef dict result = dict(base)
    cdef object key, value, existing

    for key, value in override.items():
        existing = result.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            result[key] = deep_merge_c(<dict>existing, <dict>value)
        else:
            result[key] = value
    return result


cpdef object nested_get_c(dict data, str key):
    """Traverse *data* using a dot-separated *key* string.

    Splits *key* on ``'.'`` and descends the nested dict.  Returns the
    leaf string value or ``None`` if any intermediate key is missing or
    the final value is not a string.

    Args:
        data: Top-level translation dict to traverse.
        key:  Dot-separated key, e.g. ``"module.section.name"``.

    Returns:
        Leaf string value, or ``None`` if the path does not exist or
        does not resolve to a ``str``.

    # RU: Обходит вложенный словарь по ключу с точечной нотацией.
    # RU: Возвращает строковое значение листа или None если путь не найден.
    """
    cdef list parts = key.split('.')
    cdef str part
    cdef object current = data

    for part in parts:
        if not isinstance(current, dict):
            return None
        current = (<dict>current).get(part)
        if current is None:
            return None
    return current if isinstance(current, str) else None


cpdef object i18n_get_c(
    dict translations,
    str current_lang,
    str default_lang,
    str full_key,
):
    """Look up *full_key* with automatic language fallback.

    First tries *current_lang*; if the key is absent, tries *default_lang*
    (when different from *current_lang*).

    Args:
        translations: Top-level dict mapping language code →
                      nested translation dict.
        current_lang: Active language code (e.g. ``"ru"``).
        default_lang: Fallback language code used when *key* is missing
                      in *current_lang*.
        full_key:     Dot-separated translation key.

    Returns:
        Translated string, or ``None`` when the key is absent in both
        languages.

    # RU: Ищет ключ с автоматическим фолбэком на язык по умолчанию.
    # RU: Сначала current_lang, затем default_lang если не найдено.
    """
    cdef dict lang_dict
    cdef list keys = full_key.split('.')
    cdef str k
    cdef object value

    # --- current language ---
    # RU: Сначала ищем в текущем языке
    lang_dict = translations.get(current_lang)
    if lang_dict is not None:
        value = lang_dict
        for k in keys:
            if not isinstance(value, dict):
                value = None
                break
            value = (<dict>value).get(k)
            if value is None:
                break
        if isinstance(value, str):
            return value

    # --- fallback language ---
    # RU: Фолбэк на язык по умолчанию
    if current_lang != default_lang:
        lang_dict = translations.get(default_lang)
        if lang_dict is not None:
            value = lang_dict
            for k in keys:
                if not isinstance(value, dict):
                    value = None
                    break
                value = (<dict>value).get(k)
                if value is None:
                    break
            if isinstance(value, str):
                return value

    return None
