# -*- coding: utf-8 -*-
"""Internationalization support for zsys core.

Provides translation management and multi-language support.
"""

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
    
    def __init__(
        self,
        locales_path: Path,
        default_lang: str = "en",
        fallback_lang: Optional[str] = None
    ):
        """Initialize I18N manager.
        
        Args:
            locales_path: Path to locales directory.
            default_lang: Default language code.
            fallback_lang: Fallback language if key not found.
        """
        self.locales_path = Path(locales_path)
        self.default_lang = default_lang
        self.fallback_lang = fallback_lang or default_lang
        self.current_lang = default_lang
        self._translations: Dict[str, Dict[str, Any]] = {}
        self._load_all_translations()
    
    def _load_all_translations(self):
        """Load all translation files from locales directory."""
        if not self.locales_path.exists():
            self._translations[self.default_lang] = {}
            return
        
        # Load JSON files
        for json_file in self.locales_path.glob("*.json"):
            lang = json_file.stem
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    self._translations[lang] = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._translations[lang] = {}
        
        # Try to load CBOR files (if cbor2 available)
        try:
            import cbor2
            for cbor_file in self.locales_path.glob("*.cbor"):
                lang = cbor_file.stem
                if lang not in self._translations:
                    try:
                        with open(cbor_file, "rb") as f:
                            self._translations[lang] = cbor2.load(f)
                    except Exception:
                        pass
        except ImportError:
            pass
        
        # Ensure default language exists
        if self.default_lang not in self._translations:
            self._translations[self.default_lang] = {}
    
    def set_language(self, lang: str) -> bool:
        """Set current language.
        
        Args:
            lang: Language code.
        
        Returns:
            True if language is available.
        """
        if lang in self._translations:
            self.current_lang = lang
            return True
        return False
    
    def get_language(self) -> str:
        """Get current language code.
        
        Returns:
            Current language code.
        """
        return self.current_lang
    
    def get_available_languages(self) -> List[str]:
        """Get list of available languages.
        
        Returns:
            List of language codes.
        """
        return list(self._translations.keys())
    
    @lru_cache(maxsize=1024)
    def _get_nested(self, lang: str, key: str) -> Optional[str]:
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
        **kwargs
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
        lang = lang or self.current_lang
        
        # Try current language
        text = self._get_nested(lang, key)
        
        # Try fallback language
        if text is None and lang != self.fallback_lang:
            text = self._get_nested(self.fallback_lang, key)
        
        # Use default or key
        if text is None:
            text = default if default is not None else key
        
        # Format with kwargs
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
        if lang not in self._translations:
            self._translations[lang] = {}
        
        # Handle nested keys
        parts = key.split(".")
        current = self._translations[lang]
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
        
        # Clear cache
        self._get_nested.cache_clear()
    
    def clear_cache(self):
        """Clear translation cache."""
        self._get_nested.cache_clear()


# Global I18N instance (can be initialized by projects)
_global_i18n: Optional[I18N] = None


def init_i18n(locales_path: Path, default_lang: str = "en") -> I18N:
    """Initialize global I18N instance.
    
    Args:
        locales_path: Path to locales directory.
        default_lang: Default language code.
    
    Returns:
        I18N instance.
    """
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
    if _global_i18n is None:
        return False
    return _global_i18n.set_language(lang)


# Alias
t = get_translation


# ---------------------------------------------------------------------------
# GlobalI18N — Extended I18N with CBOR support, db backend, and proxy
# ---------------------------------------------------------------------------

class GlobalI18N:
    """Extended I18N with CBOR caching, optional DB persistence, and lru_cache.

    Args:
        locales_path: Path to the locales directory (contains *.json / *.cbor).
        db: Optional database object with get(ns, key, default) / set(ns, key, val).
            If None, language preference is stored in memory only.
        default_lang: Default language code.
    """

    def __init__(
        self,
        locales_path: Path,
        db=None,
        default_lang: str = "en",
    ):
        self.locales_path = Path(locales_path)
        self.db = db
        self.default_lang = default_lang
        self.translations = self._load_all_translations()
        self.current_lang = self._load_saved_language()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _convert_json_to_cbor(json_path: Path, cbor_path: Path):
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
        try:
            import cbor2
            with open(path, "rb") as f:
                return cbor2.load(f)
        except Exception:
            return None

    def _load_json(self, path: Path) -> "Optional[Dict[str, Any]]":
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _load_all_translations(self) -> "Dict[str, Dict[str, Any]]":
        translations: "Dict[str, Any]" = {}

        if not self.locales_path.exists():
            return {self.default_lang: {}}

        for json_file in self.locales_path.glob("*.json"):
            lang = json_file.stem
            cbor_file = self.locales_path / f"{lang}.cbor"

            data = None
            if cbor_file.exists():
                data = self._load_cbor(cbor_file)
            if data is None:
                self._convert_json_to_cbor(json_file, cbor_file)
                data = self._load_cbor(cbor_file)
            if data is None:
                data = self._load_json(json_file)
            if data is None or not isinstance(data, dict):
                continue
            translations[lang] = data

        return translations or {self.default_lang: {}}

    def _load_saved_language(self) -> str:
        if self.db is not None:
            try:
                saved = self.db.get("core.i18n", "global_language", self.default_lang)
                if saved in self.translations:
                    return saved
            except Exception:
                pass
        return self.default_lang

    def _save_language(self):
        if self.db is not None:
            try:
                self.db.set("core.i18n", "global_language", self.current_lang)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @lru_cache(maxsize=1024)
    def get(self, key: str, module_name: "Optional[str]" = None, **kwargs) -> str:
        if module_name is None and "." in key:
            module_name, key = key.split(".", 1)

        full_key = f"{module_name}.{key}" if module_name else key

        if _C_AVAILABLE:
            lang_dict = self.translations.get(self.current_lang)
            value = _c_nested_get(lang_dict, full_key) if lang_dict else None
            if value is None and self.current_lang != self.default_lang:
                fb_dict = self.translations.get(self.default_lang)
                value = _c_nested_get(fb_dict, full_key) if fb_dict else None
            if value is None:
                return f"[{full_key}]"
            return value.format(**kwargs) if kwargs else value

        keys = full_key.split(".")

        try:
            value = self.translations[self.current_lang]
            for k in keys:
                value = value[k]
            return value.format(**kwargs) if kwargs else value
        except (KeyError, AttributeError):
            if self.current_lang != self.default_lang:
                try:
                    value = self.translations[self.default_lang]
                    for k in keys:
                        value = value[k]
                    return value.format(**kwargs) if kwargs else value
                except (KeyError, AttributeError):
                    return f"[{full_key}]"
            return f"[{full_key}]"

    def set_language(self, lang: str):
        if lang in self.translations:
            self.current_lang = lang
            self._save_language()
            self.get.cache_clear()

    def get_available_languages(self) -> List[str]:
        return sorted(self.translations.keys())

    def reload_translations(self):
        self.translations = self._load_all_translations()
        self.get.cache_clear()


# ---------------------------------------------------------------------------
# Global GlobalI18N instance + proxy
# ---------------------------------------------------------------------------

_global_global_i18n: "Optional[GlobalI18N]" = None


class _GlobalI18NProxy:
    """Proxy that delegates all attribute access to the active GlobalI18N.

    Works before init_i18n() — returns key as-is when not initialized.
    """

    def __getattr__(self, name: str):
        if _global_global_i18n is None:
            # Graceful fallback: .get() / .set_language() / etc. before init
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
        if _global_global_i18n is None:
            return key
        return _global_global_i18n.get(key, **kwargs)


def init_global_i18n(
    locales_path: Path,
    db=None,
    default_lang: str = "en",
) -> GlobalI18N:
    """Create and register the global GlobalI18N instance."""
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
    global _global_global_i18n
    _global_global_i18n = instance
    return instance


# Public proxy — always safe to import; delegates to instance set by init_global_i18n
global_t = _GlobalI18NProxy()
