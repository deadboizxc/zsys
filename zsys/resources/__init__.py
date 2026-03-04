"""ZSYS static resources — fonts, images, locales, templates."""

from pathlib import Path

_RESOURCES_DIR = Path(__file__).parent

FONTS_DIR = _RESOURCES_DIR / "fonts"
IMAGES_DIR = _RESOURCES_DIR / "images"
LOCALES_DIR = _RESOURCES_DIR / "locales"
STATIC_DIR = _RESOURCES_DIR / "static"
TEMPLATES_DIR = _RESOURCES_DIR / "templates"

__all__ = ["FONTS_DIR", "IMAGES_DIR", "LOCALES_DIR", "STATIC_DIR", "TEMPLATES_DIR"]
