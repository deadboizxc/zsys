"""
zsys build script — auto-compiles the C extension during pip install.

When the C extension builds successfully, all hot-path functions run
~20-40x faster. If the build fails (missing compiler, headers), the
package falls back to pure-Python implementations transparently.
"""

import os
import sys
import warnings
from pathlib import Path

from setuptools import setup, find_packages
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


# ── Setup ─────────────────────────────────────────────────────────────────────

ext = _make_extension()

setup(
    packages=find_packages(exclude=["tests*", "examples*", "docs*"]),
    package_data={
        "zsys": [
            "include/*.h",
            "src/*.c",
            "_core/*.so",
            "_core/*.pyd",
            "resources/locales/*.json",
            "resources/locales/*.cbor",
            "resources/fonts/**/*",
            "resources/images/*",
            "resources/templates/*",
            "resources/static/**/*",
        ],
    },
    ext_modules=[ext] if ext else [],
    cmdclass={"build_ext": OptionalBuildExt},
    zip_safe=False,
)
