# -*- coding: utf-8 -*-
"""Module registry for zsys core.

Provides a centralized registry for managing modules across the ecosystem.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field

try:
    from zsys._core import build_help_text as _c_build_help_text, build_modules_list as _c_build_modules_list, C_AVAILABLE as _C
except ImportError:
    _C = False


@dataclass
class ModuleCommand:
    """Information about a module command."""
    name: str
    handler: Callable
    description: str = ""
    usage: str = ""
    aliases: List[str] = field(default_factory=list)
    admin_only: bool = False


@dataclass
class ModuleHelp:
    """Help information for a module."""
    name: str
    description: str = ""
    commands: Dict[str, ModuleCommand] = field(default_factory=dict)
    version: str = "1.0.0"
    author: str = ""


class ModuleRegistry:
    """Centralized registry for module commands and help.
    
    Example:
        registry = ModuleRegistry()
        registry.register_command("ping", ping_handler, "Check bot status")
        registry.get_command("ping")
    """
    
    _instance: Optional['ModuleRegistry'] = None
    
    def __new__(cls) -> 'ModuleRegistry':
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._commands: Dict[str, ModuleCommand] = {}
        self._modules: Dict[str, ModuleHelp] = {}
        self._aliases: Dict[str, str] = {}
        self._initialized = True
    
    def register_command(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        usage: str = "",
        aliases: Optional[List[str]] = None,
        admin_only: bool = False,
        module_name: str = "unknown"
    ) -> ModuleCommand:
        """Register a command handler.
        
        Args:
            name: Command name.
            handler: Command handler function.
            description: Command description.
            usage: Usage example.
            aliases: Alternative command names.
            admin_only: Require admin privileges.
            module_name: Parent module name.
        
        Returns:
            ModuleCommand instance.
        """
        aliases = aliases or []
        
        cmd = ModuleCommand(
            name=name,
            handler=handler,
            description=description,
            usage=usage,
            aliases=aliases,
            admin_only=admin_only
        )
        
        self._commands[name] = cmd
        
        # Register aliases
        for alias in aliases:
            self._aliases[alias] = name
        
        # Add to module help
        if module_name not in self._modules:
            self._modules[module_name] = ModuleHelp(name=module_name)
        self._modules[module_name].commands[name] = cmd
        
        return cmd
    
    def unregister_command(self, name: str) -> bool:
        """Unregister a command.
        
        Args:
            name: Command name.
        
        Returns:
            True if command was unregistered.
        """
        if name in self._commands:
            cmd = self._commands.pop(name)
            
            # Remove aliases
            for alias in cmd.aliases:
                self._aliases.pop(alias, None)
            
            return True
        return False
    
    def get_command(self, name: str) -> Optional[ModuleCommand]:
        """Get command by name or alias.
        
        Args:
            name: Command name or alias.
        
        Returns:
            ModuleCommand or None.
        """
        # Check direct command
        if name in self._commands:
            return self._commands[name]
        
        # Check aliases
        if name in self._aliases:
            return self._commands.get(self._aliases[name])
        
        return None
    
    def get_all_commands(self) -> Dict[str, ModuleCommand]:
        """Get all registered commands.
        
        Returns:
            Dictionary of command names to ModuleCommand.
        """
        return self._commands.copy()
    
    def register_module(
        self,
        name: str,
        description: str = "",
        version: str = "1.0.0",
        author: str = ""
    ) -> ModuleHelp:
        """Register a module.
        
        Args:
            name: Module name.
            description: Module description.
            version: Module version.
            author: Module author.
        
        Returns:
            ModuleHelp instance.
        """
        if name not in self._modules:
            self._modules[name] = ModuleHelp(
                name=name,
                description=description,
                version=version,
                author=author
            )
        else:
            self._modules[name].description = description
            self._modules[name].version = version
            self._modules[name].author = author
        
        return self._modules[name]
    
    def get_module(self, name: str) -> Optional[ModuleHelp]:
        """Get module help info.
        
        Args:
            name: Module name.
        
        Returns:
            ModuleHelp or None.
        """
        return self._modules.get(name)
    
    def get_all_modules(self) -> Dict[str, ModuleHelp]:
        """Get all registered modules.
        
        Returns:
            Dictionary of module names to ModuleHelp.
        """
        return self._modules.copy()
    
    def get_help_text(self, module_name: Optional[str] = None) -> str:
        """Generate help text for all or specific module.
        
        Args:
            module_name: Optional module name to filter.
        
        Returns:
            Formatted help text.
        """
        lines = []
        
        if _C and module_name and module_name in self._modules:
            mod = self._modules[module_name]
            cmds = {cmd_name: cmd.description for cmd_name, cmd in mod.commands.items()}
            return _c_build_help_text(module_name, cmds, ".")

        modules = (
            {module_name: self._modules[module_name]}
            if module_name and module_name in self._modules
            else self._modules
        )
        
        for name, module in modules.items():
            lines.append(f"📦 <b>{name}</b>")
            if module.description:
                lines.append(f"   {module.description}")
            
            for cmd_name, cmd in module.commands.items():
                prefix = "🔐" if cmd.admin_only else "▸"
                lines.append(f"   {prefix} <code>{cmd_name}</code> — {cmd.description}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def clear(self):
        """Clear all registered commands and modules."""
        self._commands.clear()
        self._modules.clear()
        self._aliases.clear()


# Global registry instance
registry = ModuleRegistry()


class ModulesHelpDict(dict):
    """
    Словарь для хранения справки по модулям.
    
    Поддерживает формат zxc_userbot:
        modules_help["dice"] = {
            "dice [1-6]*": "Generate dice with specified value"
        }
    
    А также доступ к registry для расширенных возможностей.
    
    Example:
        from zsys.modules import modules_help
        
        modules_help["mymodule"] = {
            "cmd1 [arg]": "Description 1",
            "cmd2": "Description 2"
        }
        
        # Получить справку
        modules_help.get_help("mymodule")
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._registry = registry
    
    def __setitem__(self, module_name: str, commands: Dict[str, str]):
        """
        Добавить/обновить справку по модулю.
        
        Args:
            module_name: Название модуля
            commands: Словарь {команда: описание}
        """
        super().__setitem__(module_name, commands)
        
        # Синхронизация с registry
        self._registry.register_module(module_name)
        for cmd, desc in commands.items():
            # Разбираем команду и аргументы
            parts = cmd.split(maxsplit=1)
            cmd_name = parts[0]
            usage = parts[1] if len(parts) > 1 else ""
            
            self._registry.register_command(
                name=cmd_name,
                handler=lambda: None,  # Placeholder
                description=desc,
                usage=usage,
                module_name=module_name
            )
    
    def __delitem__(self, module_name: str):
        """Удалить модуль из справки."""
        if module_name in self:
            # Удаляем команды из registry
            commands = self[module_name]
            for cmd in commands:
                cmd_name = cmd.split(maxsplit=1)[0]
                self._registry.unregister_command(cmd_name)
        
        super().__delitem__(module_name)
    
    def get_help(self, module_name: str, prefix: str = ".") -> str:
        """
        Получить форматированную справку по модулю.
        
        Args:
            module_name: Название модуля
            prefix: Префикс команд (. или /)
        
        Returns:
            HTML-форматированная строка справки
        """
        if module_name not in self:
            return f"<b>Модуль {module_name} не найден</b>"
        
        if _C:
            return _c_build_help_text(module_name, self[module_name], prefix)

        commands = self[module_name]
        lines = [f"<b>Help for |{module_name}|</b>\n<b>Usage:</b>"]
        
        for cmd, desc in commands.items():
            parts = cmd.split(maxsplit=1)
            cmd_name = parts[0]
            args = f" <code>{parts[1]}</code>" if len(parts) > 1 else ""
            lines.append(f"<code>{prefix}{cmd_name}</code>{args} — <i>{desc}</i>")
        
        return "\n".join(lines)
    
    def get_all_help(self, prefix: str = ".") -> str:
        """Получить справку по всем модулям."""
        lines = []
        for module_name in sorted(self.keys()):
            lines.append(self.get_help(module_name, prefix))
            lines.append("")
        return "\n".join(lines)
    
    def get_modules_list(self) -> str:
        """Получить список всех модулей."""
        if not self:
            return "<b>Нет загруженных модулей</b>"
        
        if _C:
            return _c_build_modules_list(dict(self))

        lines = ["<b>Загруженные модули:</b>"]
        for name in sorted(self.keys()):
            cmd_count = len(self[name])
            lines.append(f"• <code>{name}</code> ({cmd_count} команд)")
        return "\n".join(lines)


# Global modules_help dictionary
modules_help: ModulesHelpDict = ModulesHelpDict()
