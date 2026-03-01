"""
Unified command routing system.

Provides decorators and router for registering commands that work across platforms.
"""

from __future__ import annotations

import asyncio
import inspect
import re
from dataclasses import dataclass, field
from functools import wraps
from typing import (
    Any, Callable, Coroutine, Dict, List, Optional, Set, Union,
)

from .context import Context

try:
    from zsys._core import router_lookup as _c_router_lookup, C_AVAILABLE as _C
except ImportError:
    _C = False
    _c_router_lookup = None

@dataclass
class Command:
    """Command definition."""
    name: str
    handler: Callable[[Context], Coroutine[Any, Any, Any]]
    aliases: List[str] = field(default_factory=list)
    description: str = ""
    usage: str = ""
    category: str = "misc"
    owner_only: bool = False
    admin_only: bool = False
    private_only: bool = False
    group_only: bool = False
    # Filter options
    reply_only: bool = False  # Requires reply
    media_only: bool = False  # Requires media in message/reply
    text_only: bool = False   # Requires text
    extra_filters: Any = None  # Custom Pyrogram filter
    prefix: Optional[Union[str, List[str]]] = None  # Per-command prefix override
    
    @property
    def all_triggers(self) -> List[str]:
        """Get all command triggers (name + aliases)."""
        return [self.name] + self.aliases
    
    @property
    def help_text(self) -> str:
        """Generate help text for the command."""
        usage = f" {self.usage}" if self.usage else ""
        desc = self.description or "No description"
        return f"**{self.name}**{usage} - {desc}"


class Router:
    """
    Unified command router with hot reload support.
    
    Collects commands and can attach them to any supported client.
    Supports dynamic command registration/unregistration.
    
    Usage:
        router = Router()
        
        @router.command("hello", aliases=["hi"])
        async def hello(ctx: Context):
            await ctx.reply("Hello!")
        
        # Attach to Pyrogram client (dynamic - picks up new commands)
        router.attach_pyrogram(client, prefix=".")
        
        # Hot reload
        router.unregister("hello")
        router.reload_module("mymodule")
    """
    
    # Default filter error messages (can be overridden for i18n)
    DEFAULT_MESSAGES = {
        "reply_required": "❌ Reply to a message",
        "media_required": "❌ Media required",
        "text_required": "❌ Specify text\nUsage: `.{cmd} {usage}`",
        "error": "❌ Error: {error}",
    }
    
    def __init__(self, name: str = "default", messages: Dict[str, str] = None):
        self.name = name
        self.commands: Dict[str, Command] = {}
        self._trigger_map: Dict[str, Command] = {}
        self._attached_clients: list = []  # Track attached clients
        self._prefixes: List[str] = ["."]
        self._module_commands: Dict[str, List[str]] = {}  # module_name -> [cmd_names]
        self._messages: Dict[str, str] = {**self.DEFAULT_MESSAGES, **(messages or {})}
    
    def set_messages(self, messages: Dict[str, str]) -> None:
        """Override filter error messages (for i18n support)."""
        self._messages.update(messages)
    
    def command(
        self,
        name: str,
        aliases: List[str] = None,
        description: str = "",
        usage: str = "",
        category: str = "misc",
        owner_only: bool = False,
        admin_only: bool = False,
        private_only: bool = False,
        group_only: bool = False,
        reply_only: bool = False,
        media_only: bool = False,
        text_only: bool = False,
        extra_filters: Any = None,
        prefix: Optional[Union[str, List[str]]] = None,
        module: str = None,  # Track which module registered this
    ) -> Callable:
        """
        Decorator to register a command.
        
        Args:
            name: Primary command name
            aliases: Alternative command names
            description: Command description for help
            usage: Usage example (e.g., "<city>")
            category: Category for grouping in help
            owner_only: Only bot/userbot owner can use
            admin_only: Only chat admins can use
            private_only: Only works in private chats
            group_only: Only works in groups
            reply_only: Command requires reply to a message
            media_only: Command requires media (photo/video/document)
            text_only: Command requires text input
            extra_filters: Custom Pyrogram filter to add
        
        Example:
            @router.command("weather", aliases=["w"], description="Get weather")
            async def weather_cmd(ctx: Context):
                city = ctx.arg or "Kyiv"
                await ctx.reply(f"Weather in {city}...")
            
            @router.command("quote", reply_only=True)
            async def quote_cmd(ctx: Context):
                reply = await ctx.get_reply()
                ...
            
            # Per-command prefix override:
            @router.command("help", prefix="!")
            async def help_cmd(ctx: Context):
                await ctx.reply("Help!")
        """
        aliases = aliases or []
        
        # Auto-detect module name from caller
        if not module:
            import inspect
            frame = inspect.currentframe()
            if frame and frame.f_back and frame.f_back.f_back:
                module = frame.f_back.f_back.f_globals.get("__name__", "unknown")
        
        def decorator(func: Callable[[Context], Coroutine[Any, Any, Any]]) -> Callable:
            cmd = Command(
                name=name,
                handler=func,
                aliases=aliases,
                description=description,
                usage=usage,
                category=category,
                owner_only=owner_only,
                admin_only=admin_only,
                private_only=private_only,
                group_only=group_only,
                reply_only=reply_only,
                media_only=media_only,
                text_only=text_only,
                extra_filters=extra_filters,
                prefix=prefix,
            )
            
            self._register_command(cmd, module)
            
            @wraps(func)
            async def wrapper(ctx: Context) -> Any:
                return await func(ctx)
            
            # Store reference for hot reload
            wrapper._command = cmd
            wrapper._module = module
            
            return wrapper
        
        return decorator
    
    def _register_command(self, cmd: Command, module: str = None) -> None:
        """Internal: register a command."""
        self.commands[cmd.name] = cmd
        
        # Map all triggers to command
        for trigger in cmd.all_triggers:
            self._trigger_map[trigger.lower()] = cmd
        
        # Track module -> commands
        if module:
            if module not in self._module_commands:
                self._module_commands[module] = []
            self._module_commands[module].append(cmd.name)
    
    def register(
        self,
        name: str,
        handler: Callable,
        aliases: List[str] = None,
        description: str = "",
        usage: str = "",
        category: str = "misc",
        prefix: Optional[Union[str, List[str]]] = None,
        module: str = None,
        **kwargs
    ) -> Command:
        """Programmatically register a command."""
        cmd = Command(
            name=name,
            handler=handler,
            aliases=aliases or [],
            description=description,
            usage=usage,
            category=category,
            prefix=prefix,
            **kwargs
        )
        self._register_command(cmd, module)
        return cmd
    
    def unregister(self, name: str) -> bool:
        """Unregister a command by name."""
        cmd = self.commands.get(name)
        if not cmd:
            return False
        
        # Remove from commands dict
        del self.commands[name]
        
        # Remove all triggers
        for trigger in cmd.all_triggers:
            self._trigger_map.pop(trigger.lower(), None)
        
        # Remove from module tracking
        for mod, cmds in self._module_commands.items():
            if name in cmds:
                cmds.remove(name)
        
        return True
    
    def unload_module(self, module_name: str) -> int:
        """Unload all commands from a module. Returns count of unloaded commands."""
        cmds = self._module_commands.get(module_name, [])
        count = 0
        for cmd_name in cmds[:]:  # Copy list to avoid mutation during iteration
            if self.unregister(cmd_name):
                count += 1
        self._module_commands.pop(module_name, None)
        return count
    
    def reload_module(self, module_path: str) -> tuple:
        """
        Hot reload a module. Returns (unloaded_count, loaded_count).
        
        Usage:
            router.reload_module("core.modules.commands.weather")
        """
        import importlib
        import sys
        
        # Unload existing commands from this module
        unloaded = self.unload_module(module_path)
        
        # Reload the module
        if module_path in sys.modules:
            module = sys.modules[module_path]
            importlib.reload(module)
        else:
            module = importlib.import_module(module_path)
        
        # Count newly registered commands
        loaded = len(self._module_commands.get(module_path, []))
        
        return unloaded, loaded
    
    def get_command(self, trigger: str) -> Optional[Command]:
        """Get command by trigger (name or alias)."""
        if _C:
            return _c_router_lookup(self._trigger_map, trigger)
        return self._trigger_map.get(trigger.lower())
    
    def get_help(self, category: Optional[str] = None) -> Dict[str, List[Command]]:
        """Get commands grouped by category."""
        result: Dict[str, List[Command]] = {}
        for cmd in self.commands.values():
            if category and cmd.category != category:
                continue
            if cmd.category not in result:
                result[cmd.category] = []
            result[cmd.category].append(cmd)
        return result


# ==========================================================================
# GLOBAL ROUTER (convenience)
# ==========================================================================

_default_router = Router("main")


def command(
    name: str,
    aliases: List[str] = None,
    description: str = "",
    usage: str = "",
    category: str = "misc",
    owner_only: bool = False,
    admin_only: bool = False,
    private_only: bool = False,
    group_only: bool = False,
    reply_only: bool = False,
    media_only: bool = False,
    text_only: bool = False,
    extra_filters: Any = None,
    prefix: Optional[Union[str, List[str]]] = None,
) -> Callable:
    """
    Global command decorator using the default router.
    
    Args:
        name: Primary command name
        aliases: Alternative names
        description: Help description
        usage: Usage example
        category: Category for help grouping
        reply_only: Requires reply to a message
        media_only: Requires media content
        text_only: Requires text argument
        extra_filters: Custom Pyrogram filter
    
    Example:
        from core import command, Context
        
        @command("hello", aliases=["hi"], description="Say hello")
        async def hello(ctx: Context):
            await ctx.reply(f"Hello, {ctx.user.first_name}!")
        
        @command("quote", reply_only=True, description="Quote a message")
        async def quote(ctx: Context):
            reply = await ctx.get_reply()
            ...
        
        @command("dl", media_only=True, description="Download media")
        async def dl(ctx: Context):
            ...
        
        # Per-command prefix override:
        @command("stop", prefix="!", description="Stop the bot")
        async def stop(ctx: Context):
            ...
    """
    return _default_router.command(
        name=name,
        aliases=aliases,
        description=description,
        usage=usage,
        category=category,
        owner_only=owner_only,
        admin_only=admin_only,
        private_only=private_only,
        group_only=group_only,
        reply_only=reply_only,
        media_only=media_only,
        text_only=text_only,
        extra_filters=extra_filters,
        prefix=prefix,
    )


def get_default_router() -> Router:
    """Get the default global router."""
    return _default_router


def get_modules_help() -> Dict[str, List[Command]]:
    """Get help for all registered commands."""
    return _default_router.get_help()
