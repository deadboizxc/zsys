# core/tests/test_db.py — Тесты для core.common.db
"""
Тесты модуля db:
- Database ABC (базовые операции)
- SQLite driver (CRUD операции)
- DuckDB driver (CRUD операции)
- factory.create_database()
"""

import pytest
from pathlib import Path

from zsys.storage import create_database
from zsys.storage.base import Database


class TestDatabaseFactory:
    """Тесты фабрики create_database()."""
    
    def test_create_sqlite_database(self, tmp_db_path: Path):
        """Тест создания SQLite БД через фабрику."""
        db = create_database(file_path=tmp_db_path, db_type="sqlite")
        
        assert db is not None
        assert isinstance(db, Database)
        
        # Базовые операции
        db.set("test_module", "key", "value")
        assert db.get("test_module", "key") == "value"
        
        db.close()
    
    def test_create_duckdb_database(self, tmp_path: Path):
        """Тест создания DuckDB БД через фабрику."""
        try:
            db_path = tmp_path / "test.duckdb"
            db = create_database(file_path=db_path, db_type="duckdb")
            
            assert db is not None
            assert isinstance(db, Database)
            
            # Базовые операции
            db.set("test_module", "key", "value")
            assert db.get("test_module", "key") == "value"
            
            db.close()
        except ImportError:
            pytest.skip("duckdb не установлен")
    
    def test_create_tinydb_database(self, tmp_path: Path):
        """Тест создания TinyDB БД через фабрику."""
        try:
            db_path = tmp_path / "test.json"
            db = create_database(file_path=db_path, db_type="tinydb")
            
            assert db is not None
            assert isinstance(db, Database)
            
            db.close()
        except ImportError:
            pytest.skip("tinydb не установлен")
    
    def test_create_invalid_driver(self):
        """Тест создания БД с несуществующим драйвером."""
        with pytest.raises(ValueError):
            create_database(db_type="invalid_driver")


class TestSQLiteDatabase:
    """Тесты SQLite драйвера."""
    
    @pytest.fixture
    def db(self, tmp_db_path: Path):
        """Создаёт и возвращает SQLite БД для тестов."""
        database = create_database(file_path=tmp_db_path, db_type="sqlite")
        yield database
        database.close()
    
    def test_set_and_get(self, db: Database, sample_data: dict):
        """Тест установки и получения значений."""
        for key, value in sample_data.items():
            db.set("test_module", key, value)
            retrieved = db.get("test_module", key)
            assert retrieved == value
    
    def test_get_default_value(self, db: Database):
        """Тест получения значения по умолчанию для несуществующего ключа."""
        value = db.get("test_module", "nonexistent", default="default_value")
        assert value == "default_value"
    
    def test_remove_key(self, db: Database):
        """Тест удаления ключа."""
        db.set("test_module", "key_to_remove", "value")
        assert db.get("test_module", "key_to_remove") == "value"
        
        db.remove("test_module", "key_to_remove")
        assert db.get("test_module", "key_to_remove") is None
    
    def test_get_collection(self, db: Database, sample_data: dict):
        """Тест получения всех данных модуля."""
        # Записываем данные
        for key, value in sample_data.items():
            db.set("test_module", key, value)
        
        # Получаем коллекцию
        collection = db.get_collection("test_module")
        
        assert isinstance(collection, dict)
        assert len(collection) >= len(sample_data)
        for key, value in sample_data.items():
            assert collection.get(key) == value
    
    def test_context_manager(self, tmp_db_path: Path):
        """Тест использования БД как context manager."""
        with create_database(file_path=tmp_db_path, db_type="sqlite") as db:
            db.set("test_module", "key", "value")
            assert db.get("test_module", "key") == "value"
    
    def test_dict_interface(self, db: Database):
        """Тест использования БД как словарь (MutableMapping)."""
        # Эти методы должны быть реализованы для MutableMapping
        assert hasattr(db, "__getitem__")
        assert hasattr(db, "__setitem__")
        assert hasattr(db, "__delitem__")
        assert hasattr(db, "__len__")
        assert hasattr(db, "__iter__")


class TestDuckDBDatabase:
    """Тесты DuckDB драйвера."""
    
    @pytest.fixture
    def db(self, tmp_path: Path):
        """Создаёт и возвращает DuckDB БД для тестов."""
        try:
            db_path = tmp_path / "test.duckdb"
            database = create_database(file_path=db_path, db_type="duckdb")
            yield database
            database.close()
        except ImportError:
            pytest.skip("duckdb не установлен")
    
    def test_set_and_get(self, db: Database, sample_data: dict):
        """Тест установки и получения значений."""
        for key, value in sample_data.items():
            db.set("test_module", key, value)
            retrieved = db.get("test_module", key)
            assert retrieved == value
    
    def test_get_collection(self, db: Database):
        """Тест получения всех данных модуля."""
        db.set("test_module", "key1", "value1")
        db.set("test_module", "key2", "value2")
        
        collection = db.get_collection("test_module")
        
        assert isinstance(collection, dict)
        assert collection.get("key1") == "value1"
        assert collection.get("key2") == "value2"


class TestDatabasePersistence:
    """Тесты сохранения данных между сессиями."""
    
    def test_sqlite_persistence(self, tmp_db_path: Path):
        """Тест сохранения данных в SQLite между открытием/закрытием."""
        # Первая сессия — записываем
        with create_database(file_path=tmp_db_path, db_type="sqlite") as db:
            db.set("test_module", "persistent_key", "persistent_value")
        
        # Вторая сессия — читаем
        with create_database(file_path=tmp_db_path, db_type="sqlite") as db:
            value = db.get("test_module", "persistent_key")
            assert value == "persistent_value"
