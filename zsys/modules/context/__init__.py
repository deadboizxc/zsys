"""zsys.modules.context - Unified context classes for Telegram.

Single TelegramContext implementation based on zsys.telegram (TDLib).
Legacy adapters (PyrogramContext, AiogramContext, TelebotContext) are
provided as aliases for backwards compatibility but all use TDLib.

Usage:
    from zsys.modules.context import TelegramContext

    @client.on_message(filters.command("start"))
    async def handler(message):
        ctx = TelegramContext(client, message)
        await ctx.reply("Hello!")
"""
from .base import Chat, Context, User
from .tdlib import TelegramContext

# Backwards compatibility aliases — all point to TelegramContext
PyrogramContext = TelegramContext
AiogramContext = TelegramContext
TelebotContext = TelegramContext

__all__ = [
    # Base
    "Context",
    "User",
    "Chat",
    # Main implementation
    "TelegramContext",
    # Backwards compatibility
    "PyrogramContext",
    "AiogramContext",
    "TelebotContext",
]
