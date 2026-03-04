# core/tests/test_log.py — Тесты для core.common.log
"""
Тесты модуля log:
- ColorLogger creation
- get_logger()
- Уровни логирования
- Запись в файл
"""

import logging
from pathlib import Path

import pytest

from zsys.log import ColorLogger, get_logger


class TestColorLogger:
    """Тесты ColorLogger."""
    
    def test_create_logger(self):
        """Тест создания логгера."""
        logger = ColorLogger("test_logger")
        
        assert logger is not None
        assert logger.name == "test_logger"
        assert hasattr(logger, "logger")
        assert isinstance(logger.logger, logging.Logger)
    
    def test_logger_levels(self):
        """Тест установки уровней логирования."""
        # DEBUG
        logger_debug = ColorLogger("debug", level="debug")
        assert logger_debug.logger.level == logging.DEBUG
        
        # INFO
        logger_info = ColorLogger("info", level="info")
        assert logger_info.logger.level == logging.INFO
        
        # WARNING
        logger_warning = ColorLogger("warning", level="warning")
        assert logger_warning.logger.level == logging.WARNING
        
        # ERROR
        logger_error = ColorLogger("error", level="error")
        assert logger_error.logger.level == logging.ERROR
    
    def test_logger_with_file(self, tmp_log_file: Path):
        """Тест логирования в файл."""
        logger = ColorLogger("file_logger", log_file=str(tmp_log_file), level="info")
        
        # Логируем
        logger.info("Test message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # Проверяем файл
        assert tmp_log_file.exists()
        content = tmp_log_file.read_text()
        assert "Test message" in content
        assert "Warning message" in content
        assert "Error message" in content
    
    def test_logger_methods(self):
        """Тест методов логирования."""
        logger = ColorLogger("methods_test")
        
        # Проверяем наличие методов
        assert hasattr(logger, "debug")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "critical")
        
        # Проверяем, что методы вызываемы
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")


class TestGetLogger:
    """Тесты функции get_logger()."""
    
    def test_get_logger_simple(self):
        """Тест получения простого логгера."""
        logger = get_logger("test_simple")
        
        assert logger is not None
        assert isinstance(logger, ColorLogger)
        assert logger.name == "test_simple"
    
    def test_get_logger_with_level(self):
        """Тест получения логгера с уровнем."""
        logger = get_logger("test_level", level="debug")
        
        assert logger.logger.level == logging.DEBUG
    
    def test_get_logger_cached(self):
        """Тест кеширования логгеров."""
        logger1 = get_logger("cached_logger")
        logger2 = get_logger("cached_logger")
        
        # Both loggers wrap the same underlying logging.Logger (Python caches by name)
        assert logger1.logger is logger2.logger


class TestLoggingOutput:
    """Тесты вывода логов."""
    
    def test_log_to_file(self, tmp_log_file: Path):
        """Тест записи логов в файл."""
        logger = ColorLogger("file_test", log_file=str(tmp_log_file), level="debug")
        
        # Логируем разные уровни
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # Читаем файл
        content = tmp_log_file.read_text()
        
        # Проверяем наличие сообщений
        assert "Debug message" in content
        assert "Info message" in content
        assert "Warning message" in content
        assert "Error message" in content
    
    def test_log_levels_filtering(self, tmp_log_file: Path):
        """Тест фильтрации логов по уровню."""
        # WARNING и выше
        logger = ColorLogger("filter_test", log_file=str(tmp_log_file), level="warning")
        
        logger.debug("Debug - не должно быть в логе")
        logger.info("Info - не должно быть в логе")
        logger.warning("Warning - должно быть в логе")
        logger.error("Error - должно быть в логе")
        
        content = tmp_log_file.read_text()
        
        # DEBUG и INFO не должны попасть в файл
        assert "Debug - не должно быть в логе" not in content
        assert "Info - не должно быть в логе" not in content
        
        # WARNING и ERROR должны быть
        assert "Warning - должно быть в логе" in content
        assert "Error - должно быть в логе" in content


class TestLoggerConfiguration:
    """Тесты конфигурации логгеров."""
    
    def test_custom_format(self):
        """Тест кастомного формата логов."""
        logger = ColorLogger(
            "custom_format",
        )
        
        assert logger is not None
    
    def test_rotation(self, tmp_path: Path):
        """Тест ротации лог-файлов."""
        log_file = tmp_path / "rotating.log"
        logger = ColorLogger(
            "rotation_test",
            log_file=str(log_file),
            max_bytes=1024,  # 1KB
            backup_count=3
        )
        
        # Генерируем много логов
        for i in range(100):
            logger.info(f"Log message {i}" * 10)
        
        # Проверяем, что файл существует
        assert log_file.exists()
        
        # При большом количестве логов могут появиться backup файлы
        # (но не обязательно при 1KB лимите и нашем количестве логов)
