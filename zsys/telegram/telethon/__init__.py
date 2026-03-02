"""zsys Telegram Telethon subsystem — MTProto client for userbots and bot-mode.

Wraps the ``telethon`` MTProto library under the zsys ``IBot`` interface,
providing ``TelethonClient`` for userbot and bot-mode operation and
``TelethonConfig`` for credential configuration via environment variables.

Note:
    Requires the ``telethon`` extra: ``pip install zsys[telegram-telethon]``.

Example::

    from zsys.telegram.telethon import TelethonClient, TelethonConfig

    config = TelethonConfig(api_id=12345, api_hash="abc123", session_name="my_session")
    client = TelethonClient(config)
    await client.start()
"""
# RU: Подсистема Telethon для zsys — MTProto-клиент для юзерботов и бот-режима.
# RU: Содержит TelethonClient и TelethonConfig.

__all__ = []
