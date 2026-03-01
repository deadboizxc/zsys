"""
Base ORM models for SQLAlchemy.

This is the CANONICAL source for SQLAlchemy DeclarativeBase and BaseModel.
All ORM models must inherit from BaseModel.

Example:
    from zsys.models.base import BaseModel
    from sqlalchemy import Column, String

    class User(BaseModel):
        __tablename__ = "users"
        username = Column(String(50))
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0 declarative base.
    
    All ORM models must inherit from BaseModel (which inherits from this).
    This is the single source of truth for SQLAlchemy metadata.
    """
    pass


class BaseModel(Base):
    """
    Base SQLAlchemy ORM model with common fields.
    
    Provides:
    - id (Primary Key, auto-increment)
    - created_at (UTC timestamp)
    - updated_at (Auto-update UTC timestamp)
    
    Usage:
        class User(BaseModel):
            __tablename__ = "users"
            username = Column(String(50))
    """
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Auto-generate table name from class name."""
        return cls.__name__.lower() + "s"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update(self, **kwargs) -> "BaseModel":
        """Update model attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"


__all__ = ["Base", "BaseModel"]
