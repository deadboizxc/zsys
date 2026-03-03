"""
Help Formatter - Module help formatting utilities for userbot.

Provides functions to format module help messages in HTML.
"""

from typing import Dict, List, Optional

__all__ = [
    "format_module_help",
    "format_small_module_help",
    "format_all_modules_help",
]


def format_module_help(
    module_name: str, commands: Dict[str, str], prefix: str = ".", full: bool = True
) -> str:
    """
    Format full help for a module in HTML.

    Args:
        module_name: Module name
        commands: Dict of {command: description}
        prefix: Command prefix (e.g., ".", "/")
        full: Include module header

    Returns:
        HTML-formatted help string

    Example:
        >>> format_module_help("example", {"test": "Test command"}, ".")
        '<b>Help for |example|</b>\\n<b>Usage:</b>\\n<code>.test</code> — <i>Test command</i>'
    """
    help_text = (
        f"<b>Help for |{module_name}|\n\nUsage:</b>\n" if full else "<b>Usage:</b>\n"
    )

    for command, desc in commands.items():
        cmd_parts: List[str] = command.split(maxsplit=1)
        args: str = f" <code>{cmd_parts[1]}</code>" if len(cmd_parts) > 1 else ""
        help_text += f"<code>{prefix}{cmd_parts[0]}</code>{args} — <i>{desc}</i>\n"

    return help_text


def format_small_module_help(
    module_name: str, commands: Dict[str, str], prefix: str = ".", full: bool = True
) -> str:
    """
    Format brief help for a module (commands list only).

    Args:
        module_name: Module name
        commands: Dict of {command: description}
        prefix: Command prefix
        full: Include module header

    Returns:
        HTML-formatted help string
    """
    help_text = (
        f"<b>Help for |{module_name}|\n\nCommands list:\n"
        if full
        else "<b>Commands list:\n"
    )

    for command in commands:
        cmd_parts: List[str] = command.split(maxsplit=1)
        args: str = f" <code>{cmd_parts[1]}</code>" if len(cmd_parts) > 1 else ""
        help_text += f"<code>{prefix}{cmd_parts[0]}</code>{args}\n"

    help_text += f"\nGet full usage: <code>{prefix}help {module_name}</code></b>"
    return help_text


def format_all_modules_help(
    modules_help: Dict[str, Dict[str, str]], prefix: str = "."
) -> str:
    """
    Format help for all modules.

    Args:
        modules_help: Dict of {module_name: {command: description}}
        prefix: Command prefix

    Returns:
        HTML-formatted help string with all modules
    """
    if not modules_help:
        return "<b>No modules loaded.</b>"

    help_text = "<b>📚 Available Modules:</b>\n\n"

    for module_name, commands in sorted(modules_help.items()):
        cmd_count = len(commands)
        help_text += f"• <code>{module_name}</code> ({cmd_count} cmd{'s' if cmd_count != 1 else ''})\n"

    help_text += f"\n<i>Use <code>{prefix}help &lt;module&gt;</code> for details</i>"
    return help_text
