"""zsys.modules - Unified module system."""

from .loader import ModuleLoader, ModuleInfo
from .registry import ModuleRegistry, modules_help, registry
from .router import Router, Command, command, get_default_router, get_modules_help
from .context import Context, User, Chat

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
