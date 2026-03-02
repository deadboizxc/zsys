"""zsys Telegram aiogram subsystem — public API for the aiogram 3.x integration.

Re-exports the primary building blocks of the aiogram backend so that callers
only need a single import path: ``from zsys.telegram.aiogram import ...``.
The subsystem covers bot lifecycle management, a full-featured message context,
and a router attachment helper.

Note:
    Requires the ``aiogram`` extra: ``pip install zsys[telegram-aiogram]``.

Example::

    from zsys.telegram.aiogram import AiogramBot, AiogramConfig, AiogramContext, attach_router

    config = AiogramConfig(token="BOT_TOKEN")
    bot = AiogramBot(config)
    await bot.start()
"""
# RU: Публичный API aiogram-подсистемы zsys.
# RU: Реэкспортирует AiogramBot, AiogramConfig, AiogramContext и attach_router.
