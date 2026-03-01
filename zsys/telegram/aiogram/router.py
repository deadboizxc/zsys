"""
aiogram-specific router attachment.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram import Router as AiogramRouter
    from zsys.modules.router import Router


def attach_router(
    router: "Router",
    aiogram_router: "AiogramRouter",
    prefix: str = "/",
) -> None:
    """
    Attach a zsys Router to an aiogram Router/Dispatcher.

    Args:
        router: zsys Router instance
        aiogram_router: aiogram Router or Dispatcher
        prefix: Command prefix (usually "/")
    """
    from aiogram.filters import Command as AiogramCommand
    from zsys.telegram.aiogram.context import AiogramContext

    for cmd in router.commands.values():
        triggers = cmd.all_triggers

        @aiogram_router.message(AiogramCommand(*triggers))
        async def _aiogram_handler(message, cmd=cmd):
            text = message.text or ""
            parts = text.split(maxsplit=1)
            args = parts[1].split() if len(parts) > 1 else []

            ctx = AiogramContext(message, message.bot, command=cmd.name, args=args)

            if cmd.private_only and not ctx.chat.is_private:
                return
            if cmd.group_only and ctx.chat.is_private:
                return

            try:
                await cmd.handler(ctx)
            except Exception as e:
                await ctx.reply(f"❌ Error: {e}")


__all__ = ["attach_router"]
