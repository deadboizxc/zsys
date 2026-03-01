"""
telebot-specific router attachment.
"""

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
    """
    Attach a zsys Router to a telebot instance.

    Args:
        router: zsys Router instance
        bot: TeleBot instance
        prefix: Command prefix
    """
    from zsys.telegram.telebot.context import TelebotContext

    for cmd in router.commands.values():
        triggers = cmd.all_triggers

        def make_handler(cmd):
            def _telebot_handler(message):
                text = message.text or ""
                parts = text.split(maxsplit=1)

                cmd_part = parts[0]
                if cmd_part.startswith(prefix):
                    cmd_part = cmd_part[len(prefix):]

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
