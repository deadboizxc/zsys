"""Telethon client implementation — wraps TelegramClient under the IBot interface.

Provides ``TelethonConfig`` for MTProto credential configuration and
``TelethonClient`` for userbot and bot-mode operation, including message
sending, editing, forwarding, and media download.

Note:
    Requires the ``telethon`` extra: ``pip install zsys[telegram-telethon]``.

Example::

    from zsys.telegram.telethon import TelethonClient, TelethonConfig

    config = TelethonConfig(api_id=12345, api_hash="abc123")
    client = TelethonClient(config)
    await client.start()
"""
# RU: Реализация клиента Telethon через интерфейс IBot.
# RU: Содержит конфигурацию TelethonConfig и основной класс TelethonClient.

from typing import Any, Callable, Optional
from zsys.core.interfaces import IBot
from zsys.core.config import BaseConfig
from zsys.core.logging import get_logger
from zsys.core.exceptions import ClientError

try:
    from telethon import TelegramClient, events
    from telethon.tl.types import Message
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    TelegramClient = None
    events = None
    Message = None


logger = get_logger(__name__)


class TelethonConfig(BaseConfig):
    """Pydantic configuration model for the Telethon MTProto client.

    Reads settings from environment variables with the ``TELETHON_`` prefix.
    Supports both bot-token mode and interactive user-account mode.

    Attributes:
        api_id: Telegram application ID from my.telegram.org.
        api_hash: Telegram application hash from my.telegram.org.
        session_name: Session file name (without extension). Defaults to
            ``"my_account"``.
        phone_number: Phone number for user-account login (optional).
        bot_token: Bot token for bot-mode login (optional). Takes precedence
            over ``phone_number`` when set.

    Example::

        config = TelethonConfig(api_id=12345, api_hash="abc123", session_name="my_session")
    """
    # RU: Конфигурация Telethon; переменные окружения читаются с префиксом TELETHON_.

    api_id: int
    api_hash: str
    session_name: str = "my_account"
    phone_number: Optional[str] = None
    bot_token: Optional[str] = None
    
    class Config:
        env_prefix = "TELETHON_"


class TelethonClient(IBot):
    """Telethon implementation of the IBot interface for userbot and bot-mode use.

    Manages the lifecycle of a ``TelegramClient``, supports both bot-token
    and phone-number login modes, exposes decorator-based event registration
    for incoming messages, and provides async helpers for sending, editing,
    forwarding, and downloading media.

    Attributes:
        config: Active ``TelethonConfig`` instance.
        _client: Lazily-created ``TelegramClient`` instance (``None`` until
            first access via the ``client`` property).
        _running: Whether the client session is currently connected.

    Example::

        config = TelethonConfig(api_id=12345, api_hash="abc123")
        client = TelethonClient(config)

        @client.on_message()
        async def handler(event):
            await event.reply("Hello!")

        await client.start()
    """
    # RU: Реализация IBot на базе Telethon с поддержкой userbot и bot-режима.

    def __init__(self, config: TelethonConfig):
        """Initialise the Telethon client with the provided configuration.

        Args:
            config: ``TelethonConfig`` instance with API credentials and
                session settings.

        Raises:
            ClientError: If the ``telethon`` package is not installed.

        Example::

            client = TelethonClient(TelethonConfig(api_id=12345, api_hash="abc"))
        """
        # RU: Инициализация клиента; проверяет наличие библиотеки telethon.
        if not TELETHON_AVAILABLE:
            raise ClientError(
                "Telethon is not installed. Install with: pip install zsys[telegram-telethon]"
            )
        
        self.config = config
        self._client: Optional[TelegramClient] = None
        self._running = False
    
    @property
    def client(self) -> TelegramClient:
        """Return the lazily-instantiated underlying ``TelegramClient`` object.

        Constructs a new ``TelegramClient`` from :attr:`config` on first access.

        Returns:
            Configured ``TelegramClient`` instance.

        Example::

            raw_client = telethon_client.client
        """
        # RU: Ленивое создание экземпляра TelegramClient.
        if self._client is None:
            self._client = TelegramClient(
                self.config.session_name,
                self.config.api_id,
                self.config.api_hash
            )
        return self._client
    
    async def start(self) -> None:
        """Connect and authenticate the Telethon client.

        Uses ``bot_token`` if set in config; otherwise uses ``phone_number``
        for interactive user-account login. Sets :attr:`_running` to ``True``
        on success.

        Raises:
            telethon.errors.AuthKeyError: If credentials are invalid.

        Example::

            await client.start()
        """
        # RU: Запускает и аутентифицирует клиент Telethon.
        logger.info(f"Starting Telethon client: {self.config.session_name}")
        
        if self.config.bot_token:
            await self.client.start(bot_token=self.config.bot_token)
        else:
            await self.client.start(phone=self.config.phone_number)
        
        self._running = True
        logger.info("Telethon client started")
    
    async def stop(self) -> None:
        """Disconnect the Telethon client and mark it as not running.

        Calls ``TelegramClient.disconnect()`` and sets :attr:`_running` to
        ``False``.

        Example::

            await client.stop()
        """
        # RU: Отключает клиент Telethon и сбрасывает флаг активности.
        logger.info("Stopping Telethon client")
        await self.client.disconnect()
        self._running = False
        logger.info("Telethon client stopped")
    
    @property
    def is_running(self) -> bool:
        """Indicate whether the client session is currently connected.

        Returns:
            ``True`` if the client has started and not yet stopped.

        Example::

            if client.is_running:
                print("Client is active")
        """
        # RU: Возвращает True, если клиент подключён.
        return self._running
    
    def on_message(self, filters_obj: Any = None) -> Callable:
        """Return a decorator that registers a new-message event handler.

        Args:
            filters_obj: Optional dict of keyword arguments forwarded to
                ``events.NewMessage`` (e.g. ``{"pattern": r"/start"}``).
                When ``None``, listens for all new messages.

        Returns:
            Telethon event handler decorator.

        Example::

            @client.on_message({"pattern": r"/start"})
            async def on_start(event):
                await event.reply("Hello!")
        """
        # RU: Декоратор для регистрации обработчика входящих сообщений Telethon.
        if filters_obj:
            return self.client.on(events.NewMessage(**filters_obj))
        return self.client.on(events.NewMessage())
    
    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        **kwargs: Any
    ) -> Message:
        """Send a text message to the specified chat or user.

        Args:
            chat_id: Target entity — integer ID, username, phone, or
                ``telethon`` peer object.
            text: Message text.
            **kwargs: Extra keyword arguments forwarded to
                ``TelegramClient.send_message``.

        Returns:
            Sent ``telethon.tl.types.Message`` object.

        Example::

            msg = await client.send_message(chat_id="@username", text="Hello!")
        """
        # RU: Отправляет текстовое сообщение указанному получателю.
        return await self.client.send_message(chat_id, text, **kwargs)
    
    async def edit_message_text(
        self,
        chat_id: int | str,
        message_id: int,
        text: str,
        **kwargs: Any
    ) -> Message:
        """Edit the text of an existing message.

        Args:
            chat_id: Chat or user entity containing the message.
            message_id: ID of the message to edit.
            text: New message text.
            **kwargs: Extra keyword arguments forwarded to
                ``TelegramClient.edit_message``.

        Returns:
            Updated ``telethon.tl.types.Message`` object.

        Example::

            await client.edit_message_text("@username", 42, "Updated text")
        """
        # RU: Редактирует текст существующего сообщения.
        return await self.client.edit_message(
            chat_id, message_id, text, **kwargs
        )
    
    async def forward_messages(
        self,
        chat_id: int | str,
        from_chat_id: int | str,
        message_ids: int | list[int],
        **kwargs: Any
    ) -> Message | list[Message]:
        """Forward one or more messages to a target chat.

        Args:
            chat_id: Target chat entity to forward messages into.
            from_chat_id: Source chat entity the messages are forwarded from.
            message_ids: Single message ID or list of message IDs to forward.
            **kwargs: Extra keyword arguments forwarded to
                ``TelegramClient.forward_messages``.

        Returns:
            A single ``Message`` if one ID was provided, or a list of
            ``Message`` objects for multiple IDs.

        Example::

            await client.forward_messages("@target", "@source", [1, 2, 3])
        """
        # RU: Пересылает одно или несколько сообщений в целевой чат.
        return await self.client.forward_messages(
            chat_id, message_ids, from_chat_id, **kwargs
        )
    
    async def download_media(
        self,
        message: Message,
        file_name: str | None = None,
        **kwargs: Any
    ) -> str:
        """Download the media from a Telethon message to disk.

        Args:
            message: ``telethon.tl.types.Message`` whose media will be
                downloaded.
            file_name: Destination file path or directory. When ``None``,
                Telethon chooses a path automatically.
            **kwargs: Extra keyword arguments forwarded to
                ``TelegramClient.download_media``.

        Returns:
            Path string of the downloaded file on success.

        Example::

            path = await client.download_media(msg, file_name="/tmp/file.jpg")
        """
        # RU: Скачивает медиавложение из сообщения Telethon на диск.
        return await self.client.download_media(message, file=file_name, **kwargs)


__all__ = ["TelethonClient", "TelethonConfig"]
