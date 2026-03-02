"""zsys Telegram telebot subsystem — public API for the pyTelegramBotAPI integration.

Re-exports the primary building blocks of the telebot backend so that callers
only need a single import path: ``from zsys.telegram.telebot import ...``.
The subsystem covers an async-wrapped message context and a router attachment
helper that bridges zsys commands to the synchronous telebot API.

Note:
    Requires the ``telebot`` extra: ``pip install zsys[telegram-telebot]``.

Example::

    from zsys.telegram.telebot import TelebotContext, attach_router
    from telebot import TeleBot
    from zsys.modules.router import Router

    bot = TeleBot("BOT_TOKEN")
    router = Router()
    attach_router(router, bot)
    bot.polling()
"""
# RU: Публичный API telebot-подсистемы zsys.
# RU: Реэкспортирует TelebotContext и attach_router.
