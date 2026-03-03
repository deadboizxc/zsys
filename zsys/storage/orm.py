"""SQLAlchemy ORM session manager — engine creation, connection pooling, session factory.

Centralises database session management for SQLAlchemy-backed storage.
Supports SQLite (StaticPool, no threading) and other databases (QueuePool),
exposes a context-manager session interface, and a module-level singleton
for application-wide access.
"""
# RU: Менеджер ORM-сессий SQLAlchemy — создание движка, пул соединений, фабрика сессий.
# RU: Централизованное управление сессиями: SQLite (StaticPool) и прочие БД (QueuePool),
# RU: контекстный менеджер сессий, глобальный синглтон на уровне модуля.

from typing import Optional, Generator, Type, TypeVar
from contextlib import contextmanager
from sqlalchemy import create_engine, Engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool, QueuePool

T = TypeVar("T")


class ORMConfig:
    """Pydantic-style configuration dataclass for SQLAlchemy engine parameters.

    Attributes:
        database_url: SQLAlchemy-compatible database URL.
        echo: Whether to echo SQL statements to stdout.
        pool_size: Number of persistent connections in the pool (ignored for SQLite).
        max_overflow: Maximum extra connections beyond pool_size (ignored for SQLite).
        pool_recycle: Seconds before a connection is recycled (ignored for SQLite).
        pool_pre_ping: If True, test each connection with a ping before use.
        connect_args: Extra keyword arguments forwarded to the DBAPI ``connect()`` call.
    """

    # RU: Конфигурация движка SQLAlchemy: URL базы данных, параметры пула соединений.

    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        connect_args: Optional[dict] = None,
    ):
        """Initialise ORM configuration with engine and pool parameters.

        Args:
            database_url: SQLAlchemy database URL, e.g. ``postgresql://user:pass@host/db``
                or ``sqlite:///path/to/db.sqlite3``.
            echo: Echo every SQL statement to stdout; useful for debugging.
            pool_size: Number of connections to keep open in the connection pool.
                Ignored when connecting to SQLite (StaticPool is used instead).
            max_overflow: Maximum number of connections to allow above ``pool_size``.
                Ignored for SQLite.
            pool_recycle: Recycle connections after this many seconds to avoid
                stale-connection errors from the server.  Ignored for SQLite.
            pool_pre_ping: If ``True``, issue a lightweight ping before each
                connection checkout to detect and discard broken connections.
            connect_args: Additional keyword arguments passed verbatim to the
                underlying DBAPI ``connect()`` call.  Defaults to ``{}``.

        Returns:
            None

        Raises:
            Nothing on construction; invalid URLs surface at engine-creation time.
        """
        # RU: Сохраняем все параметры конфигурации как атрибуты экземпляра.
        self.database_url = database_url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        self.connect_args = connect_args or {}


class DatabaseSession:
    """SQLAlchemy engine and session-factory manager with context-manager support.

    Uses ``StaticPool`` for SQLite connections (single-file, no threading) and
    ``QueuePool`` for all other databases.  Registers a ``connect`` event listener
    that issues ``PRAGMA foreign_keys=ON`` for every new SQLite connection.

    Attributes:
        config: The ``ORMConfig`` instance used to build this manager.
        engine: The active SQLAlchemy ``Engine``, or ``None`` before initialisation.
        SessionLocal: The ``sessionmaker`` factory bound to ``engine``, or ``None``
            before initialisation.

    Example::

        db = DatabaseSession(ORMConfig("sqlite:///db.sqlite3"))

        # Use as context manager
        with db.get_session() as session:
            user = session.query(User).filter(User.id == 1).first()

        # FastAPI dependency injection
        def get_db():
            with db.get_session() as session:
                yield session
    """

    # RU: Менеджер движка и фабрики сессий SQLAlchemy с поддержкой контекстного менеджера.

    def __init__(self, config: ORMConfig):
        """Initialise the database session manager and create the engine.

        Args:
            config: An ``ORMConfig`` instance carrying all engine and pool settings.

        Returns:
            None

        Raises:
            sqlalchemy.exc.ArgumentError: If ``config.database_url`` is malformed.
        """
        # RU: Сохраняем конфигурацию и немедленно инициализируем движок.
        self.config = config
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._init_engine()

    def _init_engine(self) -> None:
        """Create the SQLAlchemy engine and session factory.

        Selects ``StaticPool`` with ``check_same_thread=False`` for SQLite URLs and
        ``QueuePool`` with the configured pool parameters for all other databases.
        Registers a ``connect`` event that enables ``PRAGMA foreign_keys=ON`` for
        every new SQLite connection.

        Returns:
            None

        Raises:
            sqlalchemy.exc.OperationalError: If the database cannot be reached
                during initial engine setup.
        """
        # RU: Определяем класс пула и параметры движка в зависимости от типа БД.
        # Determine pool class based on database type
        is_sqlite = "sqlite" in self.config.database_url

        if is_sqlite:
            # SQLite doesn't use connection pooling — StaticPool reuses a single connection.
            # RU: SQLite не поддерживает пул потоков — используем StaticPool с одним соединением.
            pool_class = StaticPool
            connect_args = {"check_same_thread": False}
            engine_kwargs = {
                "echo": self.config.echo,
                "poolclass": pool_class,
                "connect_args": connect_args,
            }
        else:
            # Use connection pooling for other databases
            # RU: Для остальных БД включаем QueuePool с параметрами из конфигурации.
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
        # RU: Создаём движок с собранными параметрами.
        self.engine = create_engine(self.config.database_url, **engine_kwargs)

        # Create session factory
        # RU: Создаём фабрику сессий без автокоммита и автофлаша.
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Add event listeners for better connection handling
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Enable foreign-key enforcement for each new SQLite connection.

            Args:
                dbapi_conn: Raw DBAPI connection object provided by SQLAlchemy.
                connection_record: Internal pool connection record (unused).

            Returns:
                None
            """
            # RU: Включаем поддержку внешних ключей для каждого нового соединения SQLite.
            if is_sqlite:
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Yield a transactional database session, committing or rolling back automatically.

        Opens a new ``Session``, yields it to the caller, commits on clean exit,
        and rolls back then re-raises on any exception.  The session is always
        closed in the ``finally`` block.

        Yields:
            session: A bound ``sqlalchemy.orm.Session`` ready for queries and writes.

        Raises:
            Exception: Any exception raised inside the ``with`` block is re-raised
                after the session has been rolled back.

        Example::

            with db.get_session() as session:
                users = session.query(User).all()
        """
        # RU: Открываем сессию, коммитим при успехе, откатываем при ошибке.
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
        """Yield a bare session suitable for FastAPI dependency injection.

        Unlike ``get_session``, this generator does **not** commit or roll back —
        the caller is responsible for transaction management.  The session is
        always closed after the generator is exhausted or abandoned.

        Yields:
            session: A bound ``sqlalchemy.orm.Session``.

        Raises:
            Nothing; exceptions inside the dependent route are propagated normally.

        Example::

            from fastapi import Depends

            @app.get("/users")
            def list_users(session: Session = Depends(db.get_session_dependency)):
                return session.query(User).all()
        """
        # RU: Генератор сессии для FastAPI Depends — без автокоммита.
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def create_all(self) -> None:
        """Create all ORM-mapped tables in the database.

        Imports ``Base`` from ``base_model`` to ensure all mapped models are
        registered before calling ``metadata.create_all``.

        Returns:
            None

        Raises:
            RuntimeError: If the engine has not been initialised.
            sqlalchemy.exc.OperationalError: If the database cannot be reached.
        """
        # RU: Создаём все таблицы, определённые через Base.
        if self.engine is None:
            raise RuntimeError("Engine not initialized")
        # Import Base from base_model to get all models
        from .base_model import Base

        Base.metadata.create_all(bind=self.engine)

    def drop_all(self) -> None:
        """Drop all ORM-mapped tables from the database — destructive, use with caution.

        Imports ``Base`` from ``base_model`` to resolve all mapped model metadata
        before issuing ``DROP TABLE`` statements.

        Returns:
            None

        Raises:
            RuntimeError: If the engine has not been initialised.
            sqlalchemy.exc.OperationalError: If the database cannot be reached.
        """
        # RU: Удаляем все таблицы из базы данных (необратимая операция!).
        if self.engine is None:
            raise RuntimeError("Engine not initialized")
        # Import Base to get all models
        from .base_model import Base

        Base.metadata.drop_all(bind=self.engine)

    def close(self) -> None:
        """Dispose of the engine and close all pooled connections.

        Calls ``Engine.dispose()`` which checks all connections back into the pool
        and then closes them.  Safe to call multiple times.

        Returns:
            None
        """
        # RU: Закрываем все соединения и освобождаем пул.
        if self.engine:
            self.engine.dispose()

    def __enter__(self):
        """Return self to support using ``DatabaseSession`` as a context manager.

        Returns:
            DatabaseSession: This instance.
        """
        # RU: Возвращаем себя для использования в блоке with.
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the engine when leaving the ``with`` block.

        Args:
            exc_type: Exception type, or ``None`` if no exception occurred.
            exc_val: Exception value, or ``None``.
            exc_tb: Traceback, or ``None``.

        Returns:
            None — exceptions are not suppressed.
        """
        # RU: При выходе из блока with закрываем соединения.
        self.close()


# Global instance (can be overridden)
_db_instance: Optional[DatabaseSession] = None


def init_db(config: ORMConfig) -> DatabaseSession:
    """Initialise the module-level singleton ``DatabaseSession``.

    Must be called once at application startup before any call to ``get_db()``.
    Subsequent calls replace the existing global instance (the old engine is
    **not** automatically disposed — call ``get_db().close()`` first if needed).

    Args:
        config: An ``ORMConfig`` instance with all engine and pool settings.

    Returns:
        The newly created ``DatabaseSession`` singleton.

    Raises:
        sqlalchemy.exc.ArgumentError: If ``config.database_url`` is malformed.

    Example::

        from zsys.core.db import init_db, ORMConfig

        db = init_db(ORMConfig(
            database_url="sqlite:///db.sqlite3",
            echo=True
        ))
    """
    # RU: Создаём глобальный синглтон DatabaseSession и сохраняем в _db_instance.
    global _db_instance
    _db_instance = DatabaseSession(config)
    return _db_instance


def get_db() -> Optional[DatabaseSession]:
    """Return the module-level ``DatabaseSession`` singleton.

    Returns ``None`` if ``init_db()`` has not yet been called.  Callers that
    require a live instance should assert the return value or call ``init_db``
    first.

    Returns:
        The global ``DatabaseSession`` instance, or ``None`` if uninitialised.
    """
    # RU: Возвращаем глобальный синглтон или None, если init_db ещё не вызывался.
    return _db_instance


__all__ = [
    "ORMConfig",
    "DatabaseSession",
    "init_db",
    "get_db",
]
