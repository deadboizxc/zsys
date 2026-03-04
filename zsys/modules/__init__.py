"""zsys.modules - Unified module system."""

from .context import Chat, Context, User
from .loader import ModuleInfo, ModuleLoader
from .registry import ModuleRegistry, modules_help, registry
from .router import Command, Router, command, get_default_router, get_modules_help

router = get_default_router()

__all__ = [
    "command",
    "Context",
    "User",
    "Chat",
    "Router",
    "Command",
    "router",
    "get_default_router",
    "modules_help",
    "get_modules_help",
    "ModuleRegistry",
    "registry",
    "ModuleLoader",
    "ModuleInfo",
]
