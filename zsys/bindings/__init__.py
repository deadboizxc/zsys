"""ZSYS language bindings — native extensions and ctypes wrappers.

Exposes the libzsys C library to Python via two complementary paths:

- ``zsys.bindings.python``: pure ctypes wrappers (portable, no compilation
  required, works on CPython and PyPy).
- ``zsys._core``: compiled CPython C extension (fast path, requires build).
- ``zsys._ctypes``: ctypes wrappers for libzsys_core.so (portable fast path).
"""
# RU: Языковые привязки ZSYS — нативные расширения и ctypes-обёртки.
# RU: bindings.python — ctypes (портабельно), _core — скомпилированное расширение.
