"""
Unified command routing system.

Provides decorators and router for registering commands that work across platforms.
"""
# RU: Единая система маршрутизации команд.

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

try:
    from zsys.bindings.python.zsys_cffi import Router as _CRouter
    _C_LIB = True
except ImportError:
    _C_LIB = False
    _CRouter = None

@dataclass
class Command:
    """Command definition.

    Attributes:
        name: Primary command name.
        handler: Async callable that processes the command.
        aliases: Alternative names for the command.
        description: Human-readable description for help output.
        usage: Usage example string.
        category: Grouping category for help display.
        owner_only: Restrict to bot/userbot owner only.
        admin_only: Restrict to chat admins only.
        private_only: Allow only in private chats.
        group_only: Allow only in group chats.
        reply_only: Require the message to be a reply.
        media_only: Require media content in message or reply.
        text_only: Require a text argument.
        extra_filters: Additional custom Pyrogram filter.
        prefix: Per-command prefix override.
    """
    # RU: Определение команды.
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
    # RU: Параметры фильтрации
    reply_only: bool = False  # Requires reply
    # RU: Требует ответа на сообщение
    media_only: bool = False  # Requires media in message/reply
    # RU: Требует медиафайл в сообщении или ответе
    text_only: bool = False   # Requires text
    # RU: Требует текстовый аргумент
    extra_filters: Any = None  # Custom Pyrogram filter
    # RU: Пользовательский фильтр Pyrogram
    prefix: Optional[Union[str, List[str]]] = None  # Per-command prefix override
    # RU: Переопределение префикса для конкретной команды

    @property
    def all_triggers(self) -> List[str]:
        """Get all command triggers including name and aliases.

        Returns:
            List of all trigger strings for this command.
        """
        # RU: Получить все триггеры команды (имя + псевдонимы).
        return [self.name] + self.aliases

    @property
    def help_text(self) -> str:
        """Generate formatted help text for the command.

        Returns:
            Markdown-formatted help string with name, usage, and description.
        """
        # RU: Сгенерировать отформатированный текст справки для команды.
        usage = f" {self.usage}" if self.usage else ""
        desc = self.description or "No description"
        return f"**{self.name}**{usage} - {desc}"


class Router:
    """Unified command router with hot reload support.

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
    # RU: Унифицированный маршрутизатор команд с поддержкой горячей перезагрузки.

    # Default filter error messages (can be overridden for i18n)
    # RU: Сообщения об ошибках фильтров по умолчанию (можно переопределить для i18n)
    DEFAULT_MESSAGES = {
        "reply_required": "❌ Reply to a message",
        "media_required": "❌ Media required",
        "text_required": "❌ Specify text\nUsage: `.{cmd} {usage}`",
        "error": "❌ Error: {error}",
    }

    def __init__(self, name: str = "default", messages: Dict[str, str] = None):
        """Initialize the router with a name and optional message overrides.

        Args:
            name: Identifier for this router instance.
            messages: Optional dict to override default filter error messages.
        """
        # RU: Инициализировать маршрутизатор с именем и опциональными сообщениями.
        self.name = name
        self.commands: Dict[str, Command] = {}
        self._trigger_map: Dict[str, Command] = {}
        self._attached_clients: list = []  # Track attached clients
        # RU: Отслеживаем подключённые клиенты
        self._prefixes: List[str] = ["."]
        self._module_commands: Dict[str, List[str]] = {}  # module_name -> [cmd_names]
        # RU: имя_модуля -> [имена_команд]
        self._messages: Dict[str, str] = {**self.DEFAULT_MESSAGES, **(messages or {})}
        # C-backed fast trigger lookup (optional optimisation via libzsys)
        # RU: Быстрый поиск триггеров через C-бэкенд (опциональная оптимизация через libzsys)
        self._c_router = None
        self._c_handler_counter = 0
        self._c_id_to_trigger: Dict[int, str] = {}
        if _C_LIB:
            try:
                self._c_router = _CRouter()
            except Exception:
                self._c_router = None

    def set_messages(self, messages: Dict[str, str]) -> None:
        """Override filter error messages for i18n support.

        Args:
            messages: Dict mapping message keys to translated strings.
        """
        # RU: Переопределить сообщения об ошибках фильтров (для поддержки i18n).
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
        """Register a command via decorator.

        Args:
            name: Primary command name.
            aliases: Alternative command names.
            description: Command description for help.
            usage: Usage example (e.g., "<city>").
            category: Category for grouping in help.
            owner_only: Only bot/userbot owner can use.
            admin_only: Only chat admins can use.
            private_only: Only works in private chats.
            group_only: Only works in groups.
            reply_only: Command requires reply to a message.
            media_only: Command requires media (photo/video/document).
            text_only: Command requires text input.
            extra_filters: Custom Pyrogram filter to add.
            prefix: Per-command prefix override.
            module: Module name that registers this command (auto-detected).

        Returns:
            Decorator function that wraps the command handler.

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
        # RU: Декоратор для регистрации команды.
        aliases = aliases or []

        # Auto-detect module name from caller
        # RU: Автоматически определяем имя модуля из стека вызовов
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
            # RU: Сохраняем ссылку для горячей перезагрузки
            wrapper._command = cmd
            wrapper._module = module

            return wrapper

        return decorator

    def _register_command(self, cmd: Command, module: str = None) -> None:
        """Register a command internally and update all lookup structures.

        Args:
            cmd: Command instance to register.
            module: Module name for tracking, enables per-module unload.
        """
        # RU: Внутренний метод: регистрирует команду и обновляет все структуры поиска.
        self.commands[cmd.name] = cmd

        # Map all triggers to command
        # RU: Сопоставляем все триггеры с командой
        for trigger in cmd.all_triggers:
            self._trigger_map[trigger.lower()] = cmd

        # Register triggers in C router for fast lookup
        # RU: Регистрируем триггеры в C-маршрутизаторе для быстрого поиска
        if self._c_router is not None:
            for trigger in cmd.all_triggers:
                hid = self._c_handler_counter
                self._c_handler_counter += 1
                self._c_id_to_trigger[hid] = trigger.lower()
                self._c_router.add(trigger, hid)

        # Track module -> commands
        # RU: Отслеживаем соответствие модуль -> команды
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
        """Programmatically register a command without using a decorator.

        Args:
            name: Primary command name.
            handler: Async callable to handle the command.
            aliases: Alternative names.
            description: Help description.
            usage: Usage example.
            category: Category for help grouping.
            prefix: Per-command prefix override.
            module: Module name for tracking.
            **kwargs: Additional Command field values.

        Returns:
            The registered Command instance.
        """
        # RU: Программно зарегистрировать команду без использования декоратора.
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
        """Unregister a command by name, removing all its triggers.

        Args:
            name: The primary name of the command to remove.

        Returns:
            True if the command was found and removed, False otherwise.
        """
        # RU: Отменить регистрацию команды по имени, удалив все её триггеры.
        cmd = self.commands.get(name)
        if not cmd:
            return False

        # Remove from commands dict
        # RU: Удаляем из словаря команд
        del self.commands[name]

        # Remove all triggers
        # RU: Удаляем все триггеры
        for trigger in cmd.all_triggers:
            self._trigger_map.pop(trigger.lower(), None)
            if self._c_router is not None:
                self._c_router.remove(trigger)

        # Remove from module tracking
        # RU: Удаляем из отслеживания модулей
        for mod, cmds in self._module_commands.items():
            if name in cmds:
                cmds.remove(name)

        return True

    def unload_module(self, module_name: str) -> int:
        """Unload all commands registered by a specific module.

        Args:
            module_name: The module whose commands should be removed.

        Returns:
            Count of successfully unloaded commands.
        """
        # RU: Выгрузить все команды, зарегистрированные указанным модулем.
        cmds = self._module_commands.get(module_name, [])
        count = 0
        for cmd_name in cmds[:]:  # Copy list to avoid mutation during iteration
            # RU: Копируем список, чтобы избежать изменения во время итерации
            if self.unregister(cmd_name):
                count += 1
        self._module_commands.pop(module_name, None)
        return count

    def reload_module(self, module_path: str) -> tuple:
        """Hot reload a module by unloading its commands and re-importing it.

        Args:
            module_path: Dotted import path of the module to reload.

        Returns:
            Tuple of (unloaded_count, loaded_count).

        Example:
            router.reload_module("core.modules.commands.weather")
        """
        # RU: Горячая перезагрузка модуля: выгрузить команды и повторно импортировать.
        import importlib
        import sys

        # Unload existing commands from this module
        # RU: Выгружаем существующие команды этого модуля
        unloaded = self.unload_module(module_path)

        # Reload the module
        # RU: Перезагружаем модуль
        if module_path in sys.modules:
            module = sys.modules[module_path]
            importlib.reload(module)
        else:
            module = importlib.import_module(module_path)

        # Count newly registered commands
        # RU: Подсчитываем заново зарегистрированные команды
        loaded = len(self._module_commands.get(module_path, []))

        return unloaded, loaded

    def get_command(self, trigger: str) -> Optional[Command]:
        """Get a command by its trigger string (name or alias).

        Args:
            trigger: The command trigger to look up.

        Returns:
            Matching Command instance, or None if not found.
        """
        # RU: Получить команду по строке триггера (имени или псевдониму).
        # Fast path: use libzsys C router if available
        # RU: Быстрый путь: используем C-маршрутизатор libzsys, если доступен
        if self._c_router is not None:
            hid = self._c_router.lookup(trigger)
            if hid >= 0:
                trig = self._c_id_to_trigger.get(hid)
                if trig:
                    return self._trigger_map.get(trig)
            return None
        # Legacy Python C extension path
        # RU: Устаревший путь через Python C-расширение
        if _C:
            return _c_router_lookup(self._trigger_map, trigger)
        return self._trigger_map.get(trigger.lower())

    def get_help(self, category: Optional[str] = None) -> Dict[str, List[Command]]:
        """Get commands grouped by category, optionally filtered.

        Args:
            category: If provided, return only commands in this category.

        Returns:
            Dict mapping category names to lists of Command instances.
        """
        # RU: Получить команды, сгруппированные по категориям, с опциональной фильтрацией.
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
# RU: ГЛОБАЛЬНЫЙ МАРШРУТИЗАТОР (для удобства)

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
    """Global command decorator using the default router.

    Args:
        name: Primary command name.
        aliases: Alternative names.
        description: Help description.
        usage: Usage example.
        category: Category for help grouping.
        owner_only: Restrict to bot owner.
        admin_only: Restrict to chat admins.
        private_only: Allow only in private chats.
        group_only: Allow only in groups.
        reply_only: Requires reply to a message.
        media_only: Requires media content.
        text_only: Requires text argument.
        extra_filters: Custom Pyrogram filter.
        prefix: Per-command prefix override.

    Returns:
        Decorator that registers the command on the default router.

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
    # RU: Глобальный декоратор команд, использующий маршрутизатор по умолчанию.
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
    """Get the default global router instance.

    Returns:
        The shared default Router instance.
    """
    # RU: Получить экземпляр глобального маршрутизатора по умолчанию.
    return _default_router


def get_modules_help() -> Dict[str, List[Command]]:
    """Get help information for all registered commands.

    Returns:
        Dict mapping category names to lists of Command instances.
    """
    # RU: Получить справочную информацию по всем зарегистрированным командам.
    return _default_router.get_help()
