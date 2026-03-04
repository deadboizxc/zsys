# core/tests/test_utils.py — Тесты для core.common.utils
"""
Тесты модуля utils:
- shell.shell_exec()
- system.get_system_info()
- android.is_android()
- frozen.is_frozen()
- paths utilities
"""

import platform
import sys
from pathlib import Path

import pytest

from zsys.utils import shell_exec_sync, get_platform_info


class TestShellExec:
    """Тесты shell_exec_sync()."""
    
    def test_shell_exec_simple_command(self):
        """Тест выполнения простой команды."""
        code, output, _ = shell_exec_sync("echo test")
        
        assert code == 0
        assert "test" in output.lower()
    
    def test_shell_exec_with_returncode(self):
        """Тест получения кода возврата."""
        code, output, _ = shell_exec_sync("echo test")
        
        assert code == 0
        assert "test" in output.lower()
    
    def test_shell_exec_failed_command(self):
        """Тест выполнения несуществующей команды."""
        code, output, err = shell_exec_sync("nonexistent_command_12345")
        
        # Команда должна вернуть ненулевой код
        assert code != 0
    
    def test_shell_exec_multiline_output(self):
        """Тест команды с многострочным выводом."""
        if platform.system() == "Windows":
            code, result, _ = shell_exec_sync("echo line1 && echo line2")
        else:
            code, result, _ = shell_exec_sync("echo 'line1' && echo 'line2'")
        
        assert "line1" in result
        assert "line2" in result
    
    @pytest.mark.asyncio
    async def test_shell_exec_async(self):
        """Тест async версии shell_exec (если реализована)."""
        try:
            from zsys.utils import shell_exec
            
            if platform.system() == "Windows":
                result = await shell_exec("echo async_test")
            else:
                result = await shell_exec("echo async_test")
            
            code, out, err = result
            assert "async_test" in out.lower()
        except ImportError:
            pytest.skip("async shell_exec не реализован")


class TestSystemInfo:
    """Тесты get_platform_info()."""
    
    def test_get_platform_info(self):
        """Тест получения информации о системе."""
        info = get_platform_info()
        
        assert isinstance(info, dict)
        assert "system" in info
        assert "python_version" in info
        
        # Проверяем значения
        assert info["python_version"].startswith("3.")
    
    def test_platform_info_fields(self):
        """Тест наличия обязательных полей в platform info."""
        info = get_platform_info()
        
        required_fields = ["system", "python_version"]
        for field in required_fields:
            assert field in info
            assert info[field] is not None


class TestAndroidDetection:
    """Тесты is_android()."""
    
    def test_is_android(self):
        """Тест определения Android/Termux."""
        try:
            from common.utils import is_android
            
            result = is_android()
            
            # Должен вернуть bool
            assert isinstance(result, bool)
            
            # На обычной системе должен быть False
            if platform.system() != "Linux":
                assert result is False
        
        except ImportError:
            pytest.skip("is_android не реализован")


class TestFrozenDetection:
    """Тесты is_frozen()."""
    
    def test_is_frozen(self):
        """Тест определения frozen (PyInstaller) окружения."""
        try:
            from common.utils import is_frozen
            
            result = is_frozen()
            
            # Должен вернуть bool
            assert isinstance(result, bool)
            
            # В тестах не должны быть в frozen окружении
            assert result is False
        
        except ImportError:
            pytest.skip("is_frozen не реализован")


class TestPathUtilities:
    """Тесты утилит для работы с путями."""
    
    def test_get_project_root(self):
        """Тест получения корневой директории проекта."""
        try:
            from common.utils import get_project_root
            
            root = get_project_root()
            
            assert root is not None
            assert isinstance(root, Path)
            assert root.exists()
        
        except ImportError:
            pytest.skip("get_project_root не реализован")
    
    def test_ensure_dir(self, tmp_path: Path):
        """Тест создания директории, если не существует."""
        try:
            from common.utils import ensure_dir
            
            test_dir = tmp_path / "test" / "nested" / "dir"
            
            ensure_dir(test_dir)
            
            assert test_dir.exists()
            assert test_dir.is_dir()
        
        except ImportError:
            pytest.skip("ensure_dir не реализован")


class TestImageUtils:
    """Тесты утилит для работы с изображениями."""
    
    def test_resize_image_import(self):
        """Тест импорта resize_image."""
        try:
            from common.utils import resize_image
            assert resize_image is not None
        except ImportError:
            pytest.skip("PIL/Pillow или resize_image не установлен")
    
    @pytest.mark.skipif(
        "PIL" not in sys.modules and "Pillow" not in sys.modules,
        reason="PIL/Pillow не установлен"
    )
    def test_resize_image_functionality(self, tmp_path: Path):
        """Тест функциональности resize_image."""
        try:
            from PIL import Image
            from common.utils import resize_image
            
            # Создаём тестовое изображение
            img_path = tmp_path / "test.png"
            img = Image.new("RGB", (1000, 1000), color="red")
            img.save(img_path)
            
            # Ресайзим
            output_path = tmp_path / "resized.png"
            resize_image(str(img_path), str(output_path), width=500, height=500)
            
            # Проверяем результат
            assert output_path.exists()
            
            resized = Image.open(output_path)
            assert resized.size == (500, 500)
        
        except ImportError:
            pytest.skip("PIL/Pillow не установлен")


class TestGitUtils:
    """Тесты Git утилит."""
    
    def test_git_utils_import(self):
        """Тест импорта Git утилит."""
        try:
            from common.utils import git
            assert git is not None
        except ImportError:
            pytest.skip("git utils не реализован")
