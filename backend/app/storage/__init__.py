"""Storage abstraction layer for file and image management."""

from .base import Storage, StorageError
from .local import LocalStorage

__all__ = ["Storage", "StorageError", "LocalStorage"]