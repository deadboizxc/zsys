# -*- coding: utf-8 -*-
"""Internationalization support for zsys core.

Provides translation management and multi-language support.
"""
# RU: Поддержка интернационализации для ядра zsys.

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import lru_cache

try:
    from zsys._core import nested_get as _c_nested_get, C_AVAILABLE as _C_AVAILABLE
except ImportError:
    _C_AVAILABLE = False
    _c_nested_get = None


class I18N:
    """Internationalization manager for multi-language support.

    Example:
        i18n = I18N(Path("./locales"), default_lang="en")
        text = i18n.t("welcome_message")
        i18n.set_language("ru")
    """

    # RU: Менеджер интернационализации для поддержки нескольких языков.

    def __init__(
        self,
        locales_path: Path,
        default_lang: str = "en",
        fallback_lang: Optional[str] = None,
    ):
        """Initialize I18N manager.

        Args:
            locales_path: Path to locales directory.
            default_lang: Default language code.
            fallback_lang: Fallback language if key not found.
        """
        # RU: Инициализирует менеджер I18N.
        self.locales_path = Path(locales_path)
        self.default_lang = default_lang
        self.fallback_lang = fallback_lang or default_lang
        self.current_lang = default_lang
        self._translations: Dict[str, Dict[str, Any]] = {}
        self._load_all_translations()

    @staticmethod
    def _deep_merge_simple(base: dict, override: dict) -> dict:
        """Recursively merge override into base dict.

        Nested dicts are merged; other values are overwritten.
        """
        # RU: Рекурсивно объединяет override в base.
        result = dict(base)
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = I18N._deep_merge_simple(result[key], value)
            else:
                result[key] = value
        return result

    def _load_all_translations(self):
        """Load all translation files from locales directory recursively."""
        # RU: Загружает все файлы переводов из директории локалей рекурсивно.
        if not self.locales_path.exists():
            self._translations[self.default_lang] = {}
            return

        # Collect all JSON files grouped by language code, sorted for reproducibility
        # RU: Собираем все JSON-файлы, группируем по коду языка
        lang_files: "Dict[str, list]" = {}
        for json_file in sorted(self.locales_path.rglob("*.json")):
            lang = json_file.stem
            lang_files.setdefault(lang, []).append(json_file)

        for lang, files in lang_files.items():
            merged: dict = {}
            for json_file in files:
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        merged = I18N._deep_merge_simple(merged, data)
                except (json.JSONDecodeError, IOError):
                    pass
            self._translations[lang] = merged

        # Ensure default language exists
        # RU: Убеждаемся, что язык по умолчанию существует
        if self.default_lang not in self._translations:
            self._translations[self.default_lang] = {}

    def set_language(self, lang: str) -> bool:
        """Set current language.

        Args:
            lang: Language code.

        Returns:
            True if language is available.
        """
        # RU: Устанавливает текущий язык.
        if lang in self._translations:
            self.current_lang = lang
            return True
        return False

    def get_language(self) -> str:
        """Get current language code.

        Returns:
            Current language code.
        """
        # RU: Возвращает текущий языковой код.
        return self.current_lang

    def get_available_languages(self) -> List[str]:
        """Get list of available languages.

        Returns:
            List of language codes.
        """
        # RU: Возвращает список доступных языков.
        return list(self._translations.keys())

    @lru_cache(maxsize=1024)
    def _get_nested(self, lang: str, key: str) -> Optional[str]:
        """Retrieve a nested translation value by dot-separated key.

        Args:
            lang: Language code to look up.
            key: Dot-separated translation key (e.g., "section.subsection.key").

        Returns:
            Translated string or None if not found.
        """
        # RU: Получает вложенное значение перевода по ключу с точечной нотацией.
        if lang not in self._translations:
            return None
        if _C_AVAILABLE:
            return _c_nested_get(self._translations[lang], key)
        value = self._translations[lang]
        for part in key.split("."):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value if isinstance(value, str) else None

    def t(
        self,
        key: str,
        lang: Optional[str] = None,
        default: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Translate a key.

        Args:
            key: Translation key (supports dot notation).
            lang: Language code (uses current if not provided).
            default: Default value if key not found.
            **kwargs: Format arguments for the translation.

        Returns:
            Translated string.

        Example:
            i18n.t("welcome", name="User")  # "Hello, User!"
        """
        # RU: Переводит ключ на текущий или указанный язык.
        lang = lang or self.current_lang

        # Try current language
        # RU: Пробуем текущий язык
        text = self._get_nested(lang, key)

        # Try fallback language
        # RU: Пробуем резервный язык
        if text is None and lang != self.fallback_lang:
            text = self._get_nested(self.fallback_lang, key)

        # Use default or key
        # RU: Используем значение по умолчанию или сам ключ
        if text is None:
            text = default if default is not None else key

        # Format with kwargs
        # RU: Форматируем строку с переданными аргументами
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass

        return text

    def add_translation(self, lang: str, key: str, value: str):
        """Add or update a translation.

        Args:
            lang: Language code.
            key: Translation key.
            value: Translation value.
        """
        # RU: Добавляет или обновляет перевод.
        if lang not in self._translations:
            self._translations[lang] = {}

        # Handle nested keys
        # RU: Обрабатываем вложенные ключи
        parts = key.split(".")
        current = self._translations[lang]

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

        # Clear cache
        # RU: Очищаем кэш
        self._get_nested.cache_clear()

    def clear_cache(self):
        """Clear translation cache."""
        # RU: Очищает кэш переводов.
        self._get_nested.cache_clear()


# Global I18N instance (can be initialized by projects)
# RU: Глобальный экземпляр I18N (может быть инициализирован проектами)
_global_i18n: Optional[I18N] = None


def init_i18n(locales_path: Path, default_lang: str = "en") -> I18N:
    """Initialize global I18N instance.

    Args:
        locales_path: Path to locales directory.
        default_lang: Default language code.

    Returns:
        I18N instance.
    """
    # RU: Инициализирует глобальный экземпляр I18N.
    global _global_i18n
    _global_i18n = I18N(locales_path, default_lang)
    return _global_i18n


def get_translation(key: str, **kwargs) -> str:
    """Get translation from global I18N instance.

    Args:
        key: Translation key.
        **kwargs: Format arguments.

    Returns:
        Translated string.
    """
    # RU: Получает перевод из глобального экземпляра I18N.
    if _global_i18n is None:
        return key
    return _global_i18n.t(key, **kwargs)


def set_language(lang: str) -> bool:
    """Set language in global I18N instance.

    Args:
        lang: Language code.

    Returns:
        True if language available.
    """
    # RU: Устанавливает язык в глобальном экземпляре I18N.
    if _global_i18n is None:
        return False
    return _global_i18n.set_language(lang)


# Alias
# RU: Псевдоним
t = get_translation


# ---------------------------------------------------------------------------
# GlobalI18N — Extended I18N with CBOR support, db backend, and proxy
# RU: GlobalI18N — Расширенный I18N с поддержкой CBOR, опциональной БД и прокси
# ---------------------------------------------------------------------------


class GlobalI18N:
    """Extended I18N with CBOR caching, optional DB persistence, and lru_cache.

    Args:
        locales_path: Path to the locales directory (contains *.json / *.cbor).
        db: Optional database object with get(ns, key, default) / set(ns, key, val).
            If None, language preference is stored in memory only.
        default_lang: Default language code.
    """

    # RU: Расширенный I18N с кэшированием CBOR, опциональным сохранением в БД и lru_cache.

    def __init__(
        self,
        locales_path: Path,
        db=None,
        default_lang: str = "en",
    ):
        """Initialize GlobalI18N.

        Args:
            locales_path: Path to the locales directory.
            db: Optional database backend for language persistence.
            default_lang: Default language code.
        """
        # RU: Инициализирует GlobalI18N.
        self.locales_path = Path(locales_path)
        self.db = db
        self.default_lang = default_lang
        self.translations = self._load_all_translations()
        self.current_lang = self._load_saved_language()
        self._cache: "Dict[str, str]" = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # RU: Вспомогательные внутренние методы
    # ------------------------------------------------------------------

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """Recursively merge override into base dict.

        Nested dicts are merged; other values are overwritten.
        # RU: Рекурсивно объединяет override в base.
        # RU: Вложенные словари объединяются, остальные значения перезаписываются.
        """
        result = dict(base)
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = GlobalI18N._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _convert_json_to_cbor(json_path: Path, cbor_path: Path):
        """Convert a JSON locale file to CBOR format for faster loading.

        Args:
            json_path: Source JSON file path.
            cbor_path: Destination CBOR file path.
        """
        # RU: Конвертирует JSON-файл локали в формат CBOR для более быстрой загрузки.
        try:
            import cbor2

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            with open(cbor_path, "wb") as fw:
                cbor2.dump(data, fw)
        except Exception:
            pass

    @staticmethod
    def _load_cbor(path: Path) -> "Optional[Dict[str, Any]]":
        """Load a CBOR locale file.

        Args:
            path: Path to CBOR file.

        Returns:
            Parsed dictionary or None on failure.
        """
        # RU: Загружает файл локали в формате CBOR.
        try:
            import cbor2

            with open(path, "rb") as f:
                return cbor2.load(f)
        except Exception:
            return None

    def _load_json(self, path: Path) -> "Optional[Dict[str, Any]]":
        """Load a JSON locale file.

        Args:
            path: Path to JSON file.

        Returns:
            Parsed dictionary or None on failure.
        """
        # RU: Загружает JSON-файл локали.
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _load_all_translations(self) -> "Dict[str, Dict[str, Any]]":
        """Load all locale files recursively, merging subdirectory files per language.

        Scans the locales directory tree. Files are grouped by language code (stem).
        Root-level files prefer CBOR over JSON for performance. Subdirectory files
        are always loaded from JSON and deep-merged into the result.

        Returns:
            Dictionary mapping language codes to merged translation data.
        """
        # RU: Рекурсивно загружает все файлы локалей, объединяя поддиректории.
        translations: "Dict[str, Dict[str, Any]]" = {}

        if not self.locales_path.exists():
            return {self.default_lang: {}}

        # Collect all JSON files, grouped by language code, sorted for reproducibility
        # RU: Собираем все JSON-файлы, группируем по коду языка
        lang_files: "Dict[str, list]" = {}
        for json_file in sorted(self.locales_path.rglob("*.json")):
            lang = json_file.stem
            lang_files.setdefault(lang, []).append(json_file)

        for lang, files in lang_files.items():
            merged: "Dict[str, Any]" = {}
            for json_file in files:
                is_root = json_file.parent == self.locales_path
                data = None
                if is_root:
                    # Try CBOR cache for root-level files
                    cbor_file = self.locales_path / f"{lang}.cbor"
                    if cbor_file.exists():
                        data = self._load_cbor(cbor_file)
                    if data is None:
                        self._convert_json_to_cbor(json_file, cbor_file)
                        data = self._load_cbor(cbor_file)
                if data is None:
                    data = self._load_json(json_file)
                if data and isinstance(data, dict):
                    merged = self._deep_merge(merged, data)
            if merged:
                translations[lang] = merged

        return translations or {self.default_lang: {}}

    def _load_saved_language(self) -> str:
        """Load the previously saved language preference from the database.

        Returns:
            Saved language code or the default language if not available.
        """
        # RU: Загружает сохранённый языковой параметр из базы данных.
        if self.db is not None:
            try:
                saved = self.db.get("core.i18n", "global_language", self.default_lang)
                if saved in self.translations:
                    return saved
            except Exception:
                pass
        return self.default_lang

    def _save_language(self):
        """Persist the current language preference to the database."""
        # RU: Сохраняет текущий языковой параметр в базу данных.
        if self.db is not None:
            try:
                self.db.set("core.i18n", "global_language", self.current_lang)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Public API
    # RU: Публичный API
    # ------------------------------------------------------------------

    @staticmethod
    def _make_cache_key(key: str, module_name: "Optional[str]", kwargs: dict) -> str:
        """Unused — kept for API compatibility."""
        # RU: Не используется — сохранён для совместимости API.
        if kwargs:
            return f"{module_name or ''}.{key}|{sorted(kwargs.items())}"
        return f"{module_name or ''}.{key}"

    def get(self, key: str, module_name: "Optional[str]" = None, **kwargs) -> str:
        """Retrieve a translated string by key with optional format arguments.

        Args:
            key: Translation key, supports dot notation or module prefix.
            module_name: Optional module namespace prefix.
            **kwargs: Format arguments for the translated string.

        Returns:
            Translated and formatted string, or bracketed key if not found.
        """
        # RU: Возвращает переведённую строку по ключу с опциональным форматированием.
        if module_name is None and "." in key:
            module_name, key = key.split(".", 1)

        full_key = f"{module_name}.{key}" if module_name else key

        # Cache only for calls without format kwargs
        # RU: Кэшируем только вызовы без аргументов форматирования
        if not kwargs:
            cache_key = f"{self.current_lang}:{full_key}"
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        if _C_AVAILABLE:
            lang_dict = self.translations.get(self.current_lang)
            value = _c_nested_get(lang_dict, full_key) if lang_dict else None
            if value is None and self.current_lang != self.default_lang:
                fb_dict = self.translations.get(self.default_lang)
                value = _c_nested_get(fb_dict, full_key) if fb_dict else None
            if value is None:
                return f"[{full_key}]"
            result = value.format(**kwargs) if kwargs else value
        else:
            keys = full_key.split(".")
            try:
                value = self.translations[self.current_lang]
                for k in keys:
                    value = value[k]
                result = value.format(**kwargs) if kwargs else value
            except (KeyError, AttributeError):
                if self.current_lang != self.default_lang:
                    try:
                        value = self.translations[self.default_lang]
                        for k in keys:
                            value = value[k]
                        result = value.format(**kwargs) if kwargs else value
                    except (KeyError, AttributeError):
                        result = f"[{full_key}]"
                else:
                    result = f"[{full_key}]"

        if not kwargs:
            self._cache[f"{self.current_lang}:{full_key}"] = result
        return result

    def set_language(self, lang: str):
        """Set the current language and clear the translation cache.

        Args:
            lang: Language code to activate.
        """
        # RU: Устанавливает текущий язык и очищает кэш переводов.
        if lang in self.translations:
            self.current_lang = lang
            self._cache.clear()
            self._save_language()

    def get_available_languages(self) -> List[str]:
        """Return a sorted list of available language codes.

        Returns:
            Sorted list of language codes.
        """
        # RU: Возвращает отсортированный список доступных языковых кодов.
        return sorted(self.translations.keys())

    def reload_translations(self):
        """Reload all translation files from disk and clear the cache."""
        # RU: Перезагружает все файлы переводов с диска и очищает кэш.
        self.translations = self._load_all_translations()
        self._cache.clear()


# ---------------------------------------------------------------------------
# Global GlobalI18N instance + proxy
# RU: Глобальный экземпляр GlobalI18N и прокси
# ---------------------------------------------------------------------------

_global_global_i18n: "Optional[GlobalI18N]" = None


class _GlobalI18NProxy:
    """Proxy that delegates all attribute access to the active GlobalI18N.

    Works before init_i18n() — returns key as-is when not initialized.
    """

    # RU: Прокси, делегирующий доступ к атрибутам активному экземпляру GlobalI18N.

    def __getattr__(self, name: str):
        """Delegate attribute access to the active GlobalI18N instance.

        Args:
            name: Attribute name to look up.

        Returns:
            Attribute from the global instance or a no-op callable if uninitialized.
        """
        # RU: Перенаправляет доступ к атрибутам активному экземпляру GlobalI18N.
        if _global_global_i18n is None:
            # Graceful fallback: .get() / .set_language() / etc. before init
            # RU: Безопасный резерв: .get() / .set_language() / и др. до инициализации
            if name == "get":
                return lambda key, *a, **kw: key
            if name in ("set_language", "reload_translations", "get.cache_clear"):
                return lambda *a, **kw: None
            if name == "get_available_languages":
                return lambda: []
            if name == "current_lang":
                return "en"
            return lambda *a, **kw: None
        return getattr(_global_global_i18n, name)

    def __call__(self, key: str, **kwargs) -> str:
        """Translate a key using the global GlobalI18N instance.

        Args:
            key: Translation key.
            **kwargs: Format arguments.

        Returns:
            Translated string or key if uninitialized.
        """
        # RU: Переводит ключ с помощью глобального экземпляра GlobalI18N.
        if _global_global_i18n is None:
            return key
        return _global_global_i18n.get(key, **kwargs)


def init_global_i18n(
    locales_path: Path,
    db=None,
    default_lang: str = "en",
) -> GlobalI18N:
    """Create and register the global GlobalI18N instance."""
    # RU: Создаёт и регистрирует глобальный экземпляр GlobalI18N.
    global _global_global_i18n
    _global_global_i18n = GlobalI18N(locales_path, db=db, default_lang=default_lang)
    return _global_global_i18n


def register_i18n(instance: GlobalI18N) -> GlobalI18N:
    """Register an existing GlobalI18N instance as the global one.

    Use this if you create GlobalI18N yourself and want zsys modules to use it.

        i18n = GlobalI18N(locales_path=..., db=db)
        t = i18n  # project alias
        register_i18n(i18n)  # so `from zsys.i18n import t` also works
    """
    # RU: Регистрирует существующий экземпляр GlobalI18N как глобальный.
    global _global_global_i18n
    _global_global_i18n = instance
    return instance


# Public proxy — always safe to import; delegates to instance set by init_global_i18n
# RU: Публичный прокси — всегда безопасен для импорта; делегирует экземпляру, установленному init_global_i18n
global_t = _GlobalI18NProxy()
