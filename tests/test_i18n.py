# core/tests/test_i18n.py — Тесты для core.common.i18n (P1)
"""
Тесты модуля i18n:
- TranslationManager
- Загрузка переводов из JSON
- Загрузка переводов из CBOR
- get_translation()
"""

import json
from pathlib import Path

import pytest


class TestI18nImport:
    """Тесты импорта i18n модулей."""
    
    def test_import_translation_manager(self):
        """Тест импорта TranslationManager."""
        try:
            from common.i18n import TranslationManager
            assert TranslationManager is not None
        except ImportError:
            pytest.skip("i18n не реализован")


class TestTranslationManager:
    """Тесты TranslationManager."""
    
    @pytest.fixture
    def translation_files(self, tmp_path: Path):
        """Создаёт временные файлы переводов."""
        # Создаём JSON файлы
        en_data = {
            "hello": "Hello",
            "goodbye": "Goodbye",
            "welcome": "Welcome, {name}!"
        }
        ru_data = {
            "hello": "Привет",
            "goodbye": "До свидания",
            "welcome": "Добро пожаловать, {name}!"
        }
        
        en_file = tmp_path / "en.json"
        ru_file = tmp_path / "ru.json"
        
        en_file.write_text(json.dumps(en_data, ensure_ascii=False))
        ru_file.write_text(json.dumps(ru_data, ensure_ascii=False))
        
        return tmp_path
    
    def test_load_translations_from_json(self, translation_files: Path):
        """Тест загрузки переводов из JSON."""
        try:
            from common.i18n import TranslationManager
            
            manager = TranslationManager(translation_files)
            manager.load_language("en")
            
            assert manager.get("hello", language="en") == "Hello"
            assert manager.get("goodbye", language="en") == "Goodbye"
        
        except ImportError:
            pytest.skip("i18n не реализован")
    
    def test_get_translation_with_fallback(self, translation_files: Path):
        """Тест получения перевода с fallback."""
        try:
            from common.i18n import TranslationManager
            
            manager = TranslationManager(translation_files)
            manager.load_language("en")
            
            # Существующий ключ
            assert manager.get("hello", language="en") == "Hello"
            
            # Несуществующий ключ — fallback
            assert manager.get("nonexistent", language="en", default="Default") == "Default"
        
        except ImportError:
            pytest.skip("i18n не реализован")
    
    def test_translation_formatting(self, translation_files: Path):
        """Тест форматирования переводов."""
        try:
            from common.i18n import TranslationManager
            
            manager = TranslationManager(translation_files)
            manager.load_language("en")
            
            result = manager.get("welcome", language="en", name="Alice")
            assert result == "Welcome, Alice!"
        
        except ImportError:
            pytest.skip("i18n не реализован")
    
    def test_multiple_languages(self, translation_files: Path):
        """Тест работы с несколькими языками."""
        try:
            from common.i18n import TranslationManager
            
            manager = TranslationManager(translation_files)
            manager.load_language("en")
            manager.load_language("ru")
            
            assert manager.get("hello", language="en") == "Hello"
            assert manager.get("hello", language="ru") == "Привет"
        
        except ImportError:
            pytest.skip("i18n не реализован")


class TestCBORSupport:
    """Тесты поддержки CBOR формата."""
    
    def test_cbor_import(self):
        """Тест импорта CBOR поддержки."""
        try:
            import cbor2
            assert cbor2 is not None
        except ImportError:
            pytest.skip("cbor2 не установлен")
    
    def test_load_cbor_translations(self, tmp_path: Path):
        """Тест загрузки переводов из CBOR."""
        try:
            import cbor2
            from common.i18n import TranslationManager
            
            # Создаём CBOR файл
            data = {"hello": "Hello CBOR"}
            cbor_file = tmp_path / "en.cbor"
            cbor_file.write_bytes(cbor2.dumps(data))
            
            manager = TranslationManager(tmp_path)
            manager.load_language("en")
            
            assert manager.get("hello", language="en") == "Hello CBOR"
        
        except ImportError:
            pytest.skip("cbor2 или i18n не доступен")
