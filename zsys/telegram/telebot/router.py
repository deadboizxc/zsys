"""Telebot router attachment — bridges zsys Router commands to telebot handlers.

Iterates over all commands registered in a zsys ``Router`` and registers each
one as a telebot ``message_handler``, handling argument parsing, chat-type
guards, and synchronous error replies via ``asyncio.run``.

Note:
    Import and call ``attach_router`` once during bot setup, before starting
    the telebot polling loop.

Example::

    from telebot import TeleBot
    from zsys.modules.router import Router
    from zsys.telegram.telebot.router import attach_router

    bot = TeleBot("BOT_TOKEN")
    router = Router()
    attach_router(router, bot)
    bot.polling()
"""
# RU: Мост между zsys Router и telebot: регистрирует команды как обработчики telebot.

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telebot import TeleBot
    from zsys.modules.router import Router


def attach_router(
    router: "Router",
    bot: "TeleBot",
    prefix: str = "/",
) -> None:
    """Register all zsys router commands as telebot message handlers.

    For each command in ``router.commands`` a closure handler is created via
    ``make_handler`` and bound with ``bot.message_handler(commands=triggers)``.
    The handler strips the prefix, parses arguments, enforces private/group-only
    restrictions, runs the async zsys handler with ``asyncio.run``, and replies
    with an error on unhandled exceptions.

    Args:
        router: zsys ``Router`` instance whose ``.commands`` dict will be
            iterated.
        bot: Synchronous ``TeleBot`` instance to register handlers on.
        prefix: Command prefix character used to strip the leading character
            from the parsed command name. Defaults to ``"/"``.

    Raises:
        ImportError: If ``telebot`` is not installed when the handler is first
            invoked (deferred import).

    Example::

        from telebot import TeleBot
        from zsys.modules.router import Router
        from zsys.telegram.telebot.router import attach_router

        bot = TeleBot("BOT_TOKEN")
        my_router = Router()
        attach_router(my_router, bot)
        bot.polling()
    """
    # RU: Регистрирует команды zsys Router как обработчики сообщений telebot.
    from zsys.telegram.telebot.context import TelebotContext

    for cmd in router.commands.values():
        triggers = cmd.all_triggers

        def make_handler(cmd):
            def _telebot_handler(message):
                text = message.text or ""
                parts = text.split(maxsplit=1)

                cmd_part = parts[0]
                if cmd_part.startswith(prefix):
                    cmd_part = cmd_part[len(prefix) :]

                args = parts[1].split() if len(parts) > 1 else []

                ctx = TelebotContext(bot, message, command=cmd.name, args=args)

                if cmd.private_only and not ctx.chat.is_private:
                    return
                if cmd.group_only and ctx.chat.is_private:
                    return

                try:
                    asyncio.run(cmd.handler(ctx))
                except Exception as e:
                    bot.reply_to(message, f"❌ Error: {e}")

            return _telebot_handler

        bot.message_handler(commands=triggers)(make_handler(cmd))


__all__ = ["attach_router"]
