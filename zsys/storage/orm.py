"""
ORM Session Manager for SQLAlchemy.

Centralized database session management and engine creation.
Provides connection pooling, session factory, and context managers.
"""

from typing import Optional, Generator, Type, TypeVar
from contextlib import contextmanager
from sqlalchemy import create_engine, Engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool, QueuePool

T = TypeVar('T')


class ORMConfig:
    """Configuration for ORM engine and sessions."""
    
    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        connect_args: Optional[dict] = None
    ):
        """
        Initialize ORM configuration.
        
        Args:
            database_url: Database URL (postgresql://user:pass@host/db)
            echo: Echo SQL statements
            pool_size: Number of connections to keep in pool
            max_overflow: Max overflow connections
            pool_recycle: Recycle connections after N seconds
            pool_pre_ping: Test connections before using
            connect_args: Additional SQLAlchemy connect args
        """
        self.database_url = database_url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        self.connect_args = connect_args or {}


class DatabaseSession:
    """
    Centralized SQLAlchemy session and engine management.
    
    Handles:
    - Engine creation with connection pooling
    - Session factory setup
    - Context manager for transactions
    - Automatic cleanup
    
    Usage:
        db = DatabaseSession(ORMConfig("sqlite:///db.sqlite3"))
        
        # Use as context manager
        with db.get_session() as session:
            user = session.query(User).filter(User.id == 1).first()
        
        # Or with dependency injection (FastAPI)
        def get_db():
            with db.get_session() as session:
                yield session
    """
    
    def __init__(self, config: ORMConfig):
        """Initialize database session manager."""
        self.config = config
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._init_engine()
    
    def _init_engine(self) -> None:
        """Initialize SQLAlchemy engine with pooling."""
        # Determine pool class based on database type
        is_sqlite = "sqlite" in self.config.database_url
        
        if is_sqlite:
            # SQLite doesn't use connection pooling
            pool_class = StaticPool
            connect_args = {"check_same_thread": False}
            engine_kwargs = {
                "echo": self.config.echo,
                "poolclass": pool_class,
                "connect_args": connect_args,
            }
        else:
            # Use connection pooling for other databases
            pool_class = QueuePool
            engine_kwargs = {
                "echo": self.config.echo,
                "poolclass": pool_class,
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "pool_recycle": self.config.pool_recycle,
                "pool_pre_ping": self.config.pool_pre_ping,
                "connect_args": self.config.connect_args,
            }
        
        # Create engine
        self.engine = create_engine(self.config.database_url, **engine_kwargs)
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Add event listeners for better connection handling
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Enable foreign keys for SQLite."""
            if is_sqlite:
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session as context manager.
        
        Auto-commits on success, auto-rollbacks on error.
        
        Yields:
            SQLAlchemy Session
        
        Example:
            with db.get_session() as session:
                users = session.query(User).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session_dependency(self) -> Generator[Session, None, None]:
        """
        Get session generator for FastAPI dependency injection.
        
        Usage in FastAPI:
            from fastapi import Depends
            
            def get_db():
                return db.get_session_dependency()
            
            @app.get("/users")
            def list_users(session: Session = Depends(get_db)):
                return session.query(User).all()
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def create_all(self) -> None:
        """Create all tables in database."""
        if self.engine is None:
            raise RuntimeError("Engine not initialized")
        # Import Base from base_model to get all models
        from .base_model import Base
        Base.metadata.create_all(bind=self.engine)
    
    def drop_all(self) -> None:
        """Drop all tables from database (DANGEROUS!)."""
        if self.engine is None:
            raise RuntimeError("Engine not initialized")
        # Import Base to get all models
        from .base_model import Base
        Base.metadata.drop_all(bind=self.engine)
    
    def close(self) -> None:
        """Close all connections."""
        if self.engine:
            self.engine.dispose()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global instance (can be overridden)
_db_instance: Optional[DatabaseSession] = None


def init_db(config: ORMConfig) -> DatabaseSession:
    """
    Initialize global database session manager.
    
    Should be called once at application startup.
    
    Args:
        config: ORM configuration
    
    Returns:
        DatabaseSession instance
    
    Example:
        from zsys.core.db import init_db, ORMConfig
        
        db = init_db(ORMConfig(
            database_url="sqlite:///db.sqlite3",
            echo=True
        ))
    """
    global _db_instance
    _db_instance = DatabaseSession(config)
    return _db_instance


def get_db() -> Optional[DatabaseSession]:
    """Get global database session manager."""
    return _db_instance


__all__ = [
    'ORMConfig',
    'DatabaseSession',
    'init_db',
    'get_db',
]
