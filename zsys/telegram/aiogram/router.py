"""Aiogram router attachment — bridges zsys Router commands to aiogram handlers.

Iterates over all commands registered in a zsys ``Router`` and registers each
one as an ``aiogram`` message handler on the provided aiogram ``Router`` or
``Dispatcher``, handling argument parsing, chat-type guards, and error replies.

Note:
    Import and call ``attach_router`` once during bot setup, before starting
    polling.

Example::

    from aiogram import Dispatcher
    from zsys.modules.router import Router
    from zsys.telegram.aiogram.router import attach_router

    dp = Dispatcher()
    router = Router()
    attach_router(router, dp)
"""
# RU: Мост между zsys Router и aiogram: регистрирует команды как обработчики aiogram.

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
    """Register all zsys router commands as aiogram message handlers.

    Iterates over every command stored in ``router.commands``, wraps each in
    an async aiogram handler that builds an ``AiogramContext``, enforces
    private/group-only restrictions, invokes the zsys handler, and replies
    with an error message on unhandled exceptions.

    Args:
        router: zsys ``Router`` instance whose ``.commands`` dict will be
            iterated.
        aiogram_router: An aiogram ``Router`` or ``Dispatcher`` to register
            handlers on.
        prefix: Command prefix used to strip the leading character from
            incoming text. Defaults to ``"/"``.

    Raises:
        ImportError: If ``aiogram`` is not installed when the handler is first
            invoked (deferred import).

    Example::

        from aiogram import Dispatcher
        from zsys.modules.router import Router
        from zsys.telegram.aiogram.router import attach_router

        dp = Dispatcher()
        my_router = Router()
        attach_router(my_router, dp)
        await bot.start()
    """
    # RU: Регистрирует команды zsys Router как обработчики сообщений aiogram.
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
