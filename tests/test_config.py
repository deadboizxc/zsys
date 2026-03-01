# core/tests/test_config.py — Тесты для core.common.config
"""
Тесты модуля config:
- env.load_env()
- env.str(), env.int(), env.bool(), env.list()
- BaseSettings (pydantic-settings)
"""

import os
from pathlib import Path

import pytest

from common.config import env, load_env, get_env_path


class TestEnvLoading:
    """Тесты загрузки .env файлов."""
    
    def test_load_env_existing_file(self, tmp_env_file: Path, clean_env):
        """Тест загрузки существующего .env файла."""
        # Загружаем файл
        result = load_env(tmp_env_file)
        
        assert result is True
        assert os.getenv("TEST_VAR") == "test_value"
        assert os.getenv("TEST_INT") == "42"
    
    def test_load_env_nonexistent_file(self, tmp_path: Path, clean_env):
        """Тест загрузки несуществующего файла."""
        nonexistent = tmp_path / "nonexistent.env"
        result = load_env(nonexistent)
        
        assert result is False
    
    def test_load_env_override(self, tmp_env_file: Path, clean_env):
        """Тест перезаписи существующих переменных."""
        # Устанавливаем переменную
        os.environ["TEST_VAR"] = "original_value"
        
        # Загружаем без override
        load_env(tmp_env_file, override=False)
        assert os.getenv("TEST_VAR") == "original_value"
        
        # Загружаем с override
        load_env(tmp_env_file, override=True)
        assert os.getenv("TEST_VAR") == "test_value"
    
    def test_get_env_path_found(self, tmp_path: Path):
        """Тест поиска .env файла в указанных директориях."""
        # Создаём .env в tmp_path
        env_file = tmp_path / ".env"
        env_file.write_text("TEST=1")
        
        # Ищем
        found = get_env_path(".env", search_dirs=[tmp_path])
        
        assert found == env_file
        assert found.exists()
    
    def test_get_env_path_not_found(self, tmp_path: Path):
        """Тест поиска несуществующего .env файла."""
        found = get_env_path(".env", search_dirs=[tmp_path])
        
        assert found is None


class TestEnvVariables:
    """Тесты чтения переменных окружения."""
    
    def test_env_str(self, tmp_env_file: Path, clean_env):
        """Тест чтения строковой переменной."""
        load_env(tmp_env_file)
        
        value = env.str("TEST_VAR")
        assert value == "test_value"
        
        # Default value
        default = env.str("NONEXISTENT", default="default")
        assert default == "default"
    
    def test_env_int(self, tmp_env_file: Path, clean_env):
        """Тест чтения целочисленной переменной."""
        load_env(tmp_env_file)
        
        value = env.int("TEST_INT")
        assert value == 42
        assert isinstance(value, int)
        
        # Default value
        default = env.int("NONEXISTENT", default=100)
        assert default == 100
    
    def test_env_bool(self, tmp_env_file: Path, clean_env):
        """Тест чтения булевой переменной."""
        load_env(tmp_env_file)
        
        value = env.bool("TEST_BOOL")
        assert value is True
        
        # Default value
        default = env.bool("NONEXISTENT", default=False)
        assert default is False
    
    def test_env_list(self, tmp_env_file: Path, clean_env):
        """Тест чтения списковой переменной."""
        load_env(tmp_env_file)
        
        value = env.list("TEST_LIST")
        assert value == ["item1", "item2", "item3"]
        assert isinstance(value, list)
        
        # Default value
        default = env.list("NONEXISTENT", default=["a", "b"])
        assert default == ["a", "b"]


class TestBaseSettings:
    """Тесты BaseSettings (pydantic-settings)."""
    
    def test_base_settings_import(self):
        """Тест импорта BaseSettings."""
        try:
            from common.config import BaseSettings
            assert BaseSettings is not None
        except ImportError:
            pytest.skip("pydantic-settings не установлен")
    
    def test_base_settings_usage(self, tmp_env_file: Path, clean_env):
        """Тест использования BaseSettings."""
        try:
            from common.config import BaseSettings
            from pydantic import Field
            
            # Создаём настройки
            class AppSettings(BaseSettings):
                test_var: str = Field(default="default")
                test_int: int = Field(default=0)
            
            # Загружаем .env
            load_env(tmp_env_file)
            
            # Создаём экземпляр
            settings = AppSettings()
            
            assert settings.test_var == "test_value"
            assert settings.test_int == 42
        
        except ImportError:
            pytest.skip("pydantic-settings не установлен")
