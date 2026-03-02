"""ZSYS Python ctypes bindings — Router, Registry, and I18n wrappers.

Re-exports the high-level Python wrapper classes from ``zsys_cffi`` that
wrap the libzsys C shared library via ``ctypes``.  Gracefully degrades
when the library is not compiled — import succeeds but instantiation
raises ``RuntimeError``.
"""
# RU: Пакет ctypes-привязок Python для ZSYS.
# RU: Экспортирует Router, Registry, I18n из zsys_cffi.

from .zsys_cffi import Router, Registry, I18n

__all__ = ["Router", "Registry", "I18n"]
