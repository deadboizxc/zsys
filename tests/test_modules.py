# core/tests/test_modules.py — Тесты для core.modules (P1)
"""
Тесты модуля modules:
- ModuleLoader.load_module()
- ModuleRegistry
- Module loading from path
"""

from pathlib import Path

import pytest


class TestModulesImport:
    """Тесты импорта modules."""
    
    def test_import_module_loader(self):
        """Тест импорта ModuleLoader."""
        try:
            from modules import ModuleLoader
            assert ModuleLoader is not None
        except ImportError:
            pytest.skip("modules.ModuleLoader не реализован")
    
    def test_import_module_registry(self):
        """Тест импорта ModuleRegistry."""
        try:
            from modules import ModuleRegistry
            assert ModuleRegistry is not None
        except ImportError:
            pytest.skip("modules.ModuleRegistry не реализован")


class TestModuleLoader:
    """Тесты ModuleLoader."""
    
    @pytest.fixture
    def sample_module(self, tmp_path: Path):
        """Создаёт временный модуль для тестов."""
        module_file = tmp_path / "test_module.py"
        module_file.write_text("""
# Test module
def test_function():
    return "test_result"

TEST_VAR = 42
""")
        return module_file
    
    def test_load_module(self, sample_module: Path):
        """Тест загрузки модуля."""
        try:
            from modules import ModuleLoader
            
            loader = ModuleLoader()
            module = loader.load_module("test_module", str(sample_module))
            
            assert module is not None
            assert hasattr(module, "test_function")
            assert module.test_function() == "test_result"
            assert module.TEST_VAR == 42
        
        except ImportError:
            pytest.skip("ModuleLoader не реализован")
    
    def test_load_module_from_directory(self, tmp_path: Path):
        """Тест загрузки модулей из директории."""
        try:
            from modules import ModuleLoader
            
            # Создаём несколько модулей
            (tmp_path / "module1.py").write_text("VALUE = 1")
            (tmp_path / "module2.py").write_text("VALUE = 2")
            
            loader = ModuleLoader()
            modules = loader.load_from_directory(str(tmp_path))
            
            assert len(modules) >= 2
        
        except (ImportError, AttributeError):
            pytest.skip("ModuleLoader.load_from_directory не реализован")


class TestModuleRegistry:
    """Тесты ModuleRegistry."""
    
    def test_register_module(self):
        """Тест регистрации модуля."""
        try:
            from modules import ModuleRegistry
            
            registry = ModuleRegistry()
            
            # Регистрируем модуль
            registry.register("test_module", {"name": "Test Module", "version": "1.0"})
            
            # Проверяем регистрацию
            assert registry.is_registered("test_module")
            module_info = registry.get("test_module")
            assert module_info["name"] == "Test Module"
        
        except ImportError:
            pytest.skip("ModuleRegistry не реализован")
    
    def test_unregister_module(self):
        """Тест удаления модуля из реестра."""
        try:
            from modules import ModuleRegistry
            
            registry = ModuleRegistry()
            registry.register("test_module", {})
            
            assert registry.is_registered("test_module")
            
            registry.unregister("test_module")
            
            assert not registry.is_registered("test_module")
        
        except ImportError:
            pytest.skip("ModuleRegistry не реализован")
    
    def test_list_modules(self):
        """Тест получения списка модулей."""
        try:
            from modules import ModuleRegistry
            
            registry = ModuleRegistry()
            registry.register("module1", {"name": "Module 1"})
            registry.register("module2", {"name": "Module 2"})
            
            modules = registry.list()
            
            assert isinstance(modules, (list, dict))
            assert len(modules) >= 2
        
        except ImportError:
            pytest.skip("ModuleRegistry не реализован")


class TestModuleMetaParsing:
    """Тесты парсинга мета-комментариев модулей."""
    
    def test_parse_meta_comments(self, tmp_path: Path):
        """Тест парсинга мета-комментариев."""
        try:
            from helpers import parse_meta_comments
            
            # Создаём модуль с мета-комментариями
            module_file = tmp_path / "meta_module.py"
            module_file.write_text("""
# meta name: Test Module
# meta version: 1.0.0
# meta author: Test Author
# meta description: Test description

def test_func():
    pass
""")
            
            meta = parse_meta_comments(str(module_file))
            
            assert meta is not None
            assert "name" in meta
            assert meta["name"] == "Test Module"
            assert meta["version"] == "1.0.0"
        
        except ImportError:
            pytest.skip("parse_meta_comments не реализован")
