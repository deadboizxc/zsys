"""Build script for _zsys_core C extension."""
from setuptools import setup, Extension
from pathlib import Path
import sys

src = Path(__file__).parent / "zsys" / "src" / "_zsys_core.c"

ext = Extension(
    "zsys._core._zsys_core",
    sources=[str(src)],
    extra_compile_args=["-O3", "-std=c11"],
)

setup(
    name="zsys-core-ext",
    version="1.0.0",
    ext_modules=[ext],
)
