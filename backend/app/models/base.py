"""
Base model classes and common fields
"""

from sqlalchemy import Column, DateTime, func, String, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.ext.declarative import declared_attr
import uuid
from datetime import datetime

from app.core.database import Base, settings


class UUID(TypeDecorator):
    """Database-agnostic UUID type"""
    
    impl = String
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, str):
                return uuid.UUID(value)
            return value


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class UUIDMixin:
    """Mixin for UUID primary key"""
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4, index=True)


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """Base model with UUID primary key and timestamps"""
    
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()