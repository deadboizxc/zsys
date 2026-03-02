"""
zsys build script — auto-compiles the C extension and Cython hot-paths.

Compilation tiers (each is optional; pure Python always works as fallback):
  Tier 1 — C extension   ``zsys/_core/_zsys_core.so``   (~20-40x vs Python)
  Tier 2 — Cython exts   ``zsys/i18n/_i18n_fast.so``    (~10-30x vs Python)
              and         ``zsys/modules/_router_dispatch.so``
  Tier 3 — Pure Python   (no compiler required, always available)
"""
# RU: Скрипт сборки zsys: компилирует C-расширение и Cython горячие пути.
# RU: Каждый уровень опционален; чистый Python доступен как резерв всегда.

import os
import sys
import warnings
from pathlib import Path

from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext
from setuptools.command.install import install

# ── C extension definition ────────────────────────────────────────────────────

SRC_DIR     = Path(__file__).parent / "zsys" / "src"
INCLUDE_DIR = Path(__file__).parent / "zsys" / "include"
TARGET_DIR  = Path(__file__).parent / "zsys" / "_core"


def _make_extension():
    """Build the _zsys_core C extension if compiler is available."""
    try:
        from setuptools import Extension
    except ImportError:
        return None

    extra_compile_args = []
    if sys.platform == "win32":
        extra_compile_args = ["/O2", "/W3"]
    else:
        extra_compile_args = ["-O3", "-Wall", "-Wextra"]
        # -march=native only for local builds, not in CI/cross-compile
        if not os.environ.get("ZSYS_NO_NATIVE"):
            extra_compile_args.append("-march=native")

    return Extension(
        name="zsys._core._zsys_core",
        sources=["zsys/src/_zsys_core.c"],
        include_dirs=["zsys/include"],
        extra_compile_args=extra_compile_args,
        optional=True,  # build failure does NOT abort pip install
    )


# ── Optional build — never fails pip install ─────────────────────────────────

class OptionalBuildExt(build_ext):
    """Build C extension but swallow errors — falls back to pure Python."""

    def run(self):
        try:
            super().run()
        except Exception as e:
            warnings.warn(
                f"\nzsys: C extension build failed ({e}).\n"
                "Falling back to pure Python — all features still work.\n"
                "To build manually: python setup_core.py build_ext --inplace\n",
                RuntimeWarning,
                stacklevel=2,
            )

    def build_extension(self, ext):
        try:
            super().build_extension(ext)
        except Exception as e:
            warnings.warn(
                f"\nzsys: Could not compile {ext.name}: {e}\n"
                "Pure Python fallback will be used.\n",
                RuntimeWarning,
                stacklevel=2,
            )


# ── Cython hot-path extensions ────────────────────────────────────────────────

def _make_cython_extensions():
    """Return Cython Extension objects for hot-path modules.

    Returns an empty list if Cython is not installed — pip install still
    succeeds and pure-Python fallbacks remain functional.

    # RU: Возвращает Cython Extension для горячих путей или [] если Cython не установлен.
    """
    try:
        from Cython.Build import cythonize
    except ImportError:
        return []

    _cy_compile_args = ["-O3"]
    if sys.platform != "win32" and not os.environ.get("ZSYS_NO_NATIVE"):
        _cy_compile_args.append("-march=native")

    _cy_exts = [
        Extension(
            "zsys.i18n._i18n_fast",
            sources=["zsys/i18n/_i18n_fast.pyx"],
            extra_compile_args=_cy_compile_args,
            optional=True,
        ),
        Extension(
            "zsys.modules._router_dispatch",
            sources=["zsys/modules/_router_dispatch.pyx"],
            extra_compile_args=_cy_compile_args,
            optional=True,
        ),
    ]

    try:
        return cythonize(
            _cy_exts,
            compiler_directives={
                "language_level": "3",
                "boundscheck": False,
                "wraparound": False,
                "cdivision": True,
            },
            quiet=True,
        )
    except Exception as exc:
        warnings.warn(
            f"\nzsys: Cython cythonize() failed ({exc}).\n"
            "Hot-path Cython extensions will not be built.\n",
            RuntimeWarning,
            stacklevel=2,
        )
        return []


# ── Setup ─────────────────────────────────────────────────────────────────────

ext = _make_extension()
cython_exts = _make_cython_extensions()

setup(
    packages=find_packages(exclude=["tests*", "examples*", "docs*"]),
    package_data={
        "zsys": [
            "include/*.h",
            "src/*.c",
            "_core/*.so",
            "_core/*.pyd",
            "i18n/_i18n_fast*.so",
            "i18n/_i18n_fast*.pyd",
            "modules/_router_dispatch*.so",
            "modules/_router_dispatch*.pyd",
            "resources/locales/*.json",
            "resources/locales/*.cbor",
            "resources/fonts/**/*",
            "resources/images/*",
            "resources/templates/*",
            "resources/static/**/*",
        ],
    },
    ext_modules=([ext] if ext else []) + cython_exts,
    cmdclass={"build_ext": OptionalBuildExt},
    zip_safe=False,
)
