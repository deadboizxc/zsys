"""
Quick setup helpers for attaching unified modules to clients.

Usage:
    from implementations.plugins.setup import setup_pyrogram, setup_aiogram, setup_telebot

    # For Pyrogram userbot
    setup_pyrogram(client, prefix=".")

    # For aiogram bot
    setup_aiogram(dp, prefix="/")

    # For telebot
    setup_telebot(bot, prefix="/")
"""

from typing import TYPE_CHECKING, List, Union

from .router import get_default_router

if TYPE_CHECKING:
    from aiogram import Dispatcher
    from aiogram import Router as AiogramRouter
    from pyrogram import Client as PyrogramClient
    from telebot import TeleBot


def setup_pyrogram(
    client: "PyrogramClient",
    prefix: Union[str, List[str]] = ".",
    owner_only: bool = True,
    load_modules: List[str] = None,
) -> None:
    """
    Setup unified modules for Pyrogram client.

    Args:
        client: Pyrogram Client instance
        prefix: Command prefix(es)
        owner_only: Only handle messages from self
        load_modules: List of module paths to import (optional)

    Example:
        from pyrogram import Client
        from implementations.plugins.setup import setup_pyrogram

        client = Client("my_userbot")

        # Load modules and attach to client
        setup_pyrogram(client, prefix=".", load_modules=[
            "core.modules.examples.weather_unified",
            "modules.my_module",
        ])
    """
    # Import modules if specified
    if load_modules:
        import importlib

        for module_path in load_modules:
            importlib.import_module(module_path)

    # Attach router to client
    router = get_default_router()
    router.attach_pyrogram(client, prefix=prefix, owner_only=owner_only)


def setup_aiogram(
    router_or_dp: Union["AiogramRouter", "Dispatcher"],
    prefix: str = "/",
    load_modules: List[str] = None,
) -> None:
    """
    Setup unified modules for aiogram 3.x.

    Args:
        router_or_dp: aiogram Router or Dispatcher
        prefix: Command prefix
        load_modules: List of module paths to import

    Example:
        from aiogram import Dispatcher
        from implementations.plugins.setup import setup_aiogram

        dp = Dispatcher()
        setup_aiogram(dp, prefix="/", load_modules=[
            "core.modules.examples.weather_unified",
        ])
    """
    if load_modules:
        import importlib

        for module_path in load_modules:
            importlib.import_module(module_path)

    router = get_default_router()
    router.attach_aiogram(router_or_dp, prefix=prefix)


def setup_telebot(
    bot: "TeleBot",
    prefix: str = "/",
    load_modules: List[str] = None,
) -> None:
    """
    Setup unified modules for pyTelegramBotAPI (telebot).

    Args:
        bot: TeleBot instance
        prefix: Command prefix
        load_modules: List of module paths to import

    Example:
        from telebot import TeleBot
        from implementations.plugins.setup import setup_telebot

        bot = TeleBot("TOKEN")
        setup_telebot(bot, prefix="/", load_modules=[
            "core.modules.examples.weather_unified",
        ])
        bot.polling()
    """
    if load_modules:
        import importlib

        for module_path in load_modules:
            importlib.import_module(module_path)

    router = get_default_router()
    router.attach_telebot(bot, prefix=prefix)


def load_modules_from_dir(
    path: str,
    recursive: bool = False,
) -> List[str]:
    """
    Load all Python modules from a directory.

    Args:
        path: Path to modules directory
        recursive: Also load from subdirectories

    Returns:
        List of loaded module names

    Example:
        from implementations.plugins.setup import load_modules_from_dir, setup_pyrogram

        # Load all modules from custom_modules folder
        loaded = load_modules_from_dir("core/custom_modules")
        print(f"Loaded {len(loaded)} modules")

        setup_pyrogram(client, prefix=".")
    """
    import importlib.util
    import os

    loaded = []
    base_path = os.path.abspath(path)

    def load_file(filepath: str):
        # Convert path to module name
        rel_path = os.path.relpath(filepath, os.getcwd())
        module_name = rel_path.replace(os.sep, ".").replace(".py", "")

        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                loaded.append(module_name)
        except Exception as e:
            print(f"Failed to load {filepath}: {e}")

    for root, dirs, files in os.walk(base_path):
        if not recursive and root != base_path:
            continue

        # Skip __pycache__ and hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith("_") and not d.startswith(".")]

        for file in files:
            if file.endswith(".py") and not file.startswith("_"):
                load_file(os.path.join(root, file))

    return loaded
