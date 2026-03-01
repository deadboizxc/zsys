# core/tests/conftest.py — Pytest fixtures
"""
Общие fixtures для всех тестов core/.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Generator

import pytest

# Добавляем core/ в sys.path для импортов
CORE_DIR = Path(__file__).parent.parent
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))


@pytest.fixture(scope="session")
def event_loop():
    """
    Создаёт единый event loop для всех async тестов.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def tmp_env_file(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Создаёт временный .env файл для тестов.
    
    Returns:
        Path к временному .env файлу
    """
    env_file = tmp_path / ".env"
    env_file.write_text(
        "TEST_VAR=test_value\n"
        "TEST_INT=42\n"
        "TEST_BOOL=True\n"
        "TEST_LIST=item1,item2,item3\n"
    )
    yield env_file
    # Cleanup
    if env_file.exists():
        env_file.unlink()


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Создаёт путь для временной БД.
    
    Returns:
        Path к временной БД
    """
    db_path = tmp_path / "test.db"
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def tmp_log_file(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Создаёт путь для временного лог-файла.
    
    Returns:
        Path к временному лог-файлу
    """
    log_file = tmp_path / "test.log"
    yield log_file
    # Cleanup
    if log_file.exists():
        log_file.unlink()


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """
    Очищает переменные окружения перед тестом и восстанавливает после.
    """
    # Сохраняем оригинальные переменные
    original_env = os.environ.copy()
    
    # Очищаем тестовые переменные
    test_vars = ["TEST_VAR", "TEST_INT", "TEST_BOOL", "TEST_LIST"]
    for var in test_vars:
        os.environ.pop(var, None)
    
    yield
    
    # Восстанавливаем оригинальные переменные
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_logger() -> logging.Logger:
    """
    Создаёт mock-логгер для тестов.
    
    Returns:
        Настроенный logging.Logger
    """
    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)
    
    # Добавляем handler в память
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


@pytest.fixture
def sample_data() -> dict:
    """
    Возвращает типовые данные для тестов БД.
    
    Returns:
        Dict с тестовыми данными
    """
    return {
        "string": "test_value",
        "integer": 42,
        "float": 3.14,
        "boolean": True,
        "list": [1, 2, 3],
        "dict": {"key": "value"},
        "none": None,
    }
