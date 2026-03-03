"""Aiogram bot implementation — wraps aiogram 3.x under the IBot interface.

Provides ``AiogramConfig`` for token-based configuration and ``AiogramBot``
for running a polling bot with command and message handler registration.

Note:
    Requires the ``aiogram`` extra: ``pip install zsys[telegram-aiogram]``.

Example::

    from zsys.telegram.aiogram import AiogramBot, AiogramConfig
    config = AiogramConfig(token="BOT_TOKEN")
    bot = AiogramBot(config)
    await bot.start()
"""
# RU: Реализация бота на aiogram 3.x через интерфейс IBot.
# RU: Содержит конфигурацию AiogramConfig и основной класс AiogramBot.

from typing import Any, Callable, Optional
from zsys.core.interfaces import IBot
from zsys.core.config import BaseConfig
from zsys.core.logging import get_logger
from zsys.core.exceptions import ClientError

try:
    from aiogram import Bot, Dispatcher
    from aiogram.types import Message

    AIOGRAM_AVAILABLE = True
except ImportError:
    AIOGRAM_AVAILABLE = False
    Bot = None
    Dispatcher = None
    Message = None


logger = get_logger(__name__)


class AiogramConfig(BaseConfig):
    """Pydantic configuration model for the Aiogram bot.

    Reads settings from environment variables with the ``BOT_`` prefix.

    Attributes:
        token: Telegram bot token issued by @BotFather.
        parse_mode: Default parse mode for outgoing messages. Defaults to ``"HTML"``.

    Example::

        config = AiogramConfig(token="123456:ABC-DEF")
    """

    # RU: Конфигурация бота; переменные окружения читаются с префиксом BOT_.

    token: str
    parse_mode: str = "HTML"

    class Config:
        env_prefix = "BOT_"


class AiogramBot(IBot):
    """Aiogram 3.x implementation of the IBot interface.

    Manages the lifecycle of an aiogram ``Bot`` and ``Dispatcher``, exposes
    decorator-based handler registration, and provides async send/delete
    helpers that delegate to the underlying bot object.

    Attributes:
        config: Active ``AiogramConfig`` instance.
        _bot: Lazily-created ``aiogram.Bot`` instance (``None`` until first access).
        _dp: Lazily-created ``aiogram.Dispatcher`` instance (``None`` until first access).
        _running: Whether the polling loop is currently active.

    Example::

        config = AiogramConfig(token="BOT_TOKEN")
        bot = AiogramBot(config)

        @bot.command("start")
        async def start_handler(message):
            await message.reply("Hello!")

        await bot.start()
    """

    # RU: Реализация IBot на базе aiogram 3.x с поддержкой long-polling.

    def __init__(self, config: AiogramConfig):
        """Initialise the Aiogram bot with the provided configuration.

        Args:
            config: ``AiogramConfig`` instance containing at minimum the bot token.

        Raises:
            ClientError: If the ``aiogram`` package is not installed.

        Example::

            bot = AiogramBot(AiogramConfig(token="BOT_TOKEN"))
        """
        # RU: Инициализация бота; проверяет наличие библиотеки aiogram.
        if not AIOGRAM_AVAILABLE:
            raise ClientError(
                "Aiogram is not installed. Install with: pip install zsys[telegram-aiogram]"
            )

        self.config = config
        self._bot: Optional[Bot] = None
        self._dp: Optional[Dispatcher] = None
        self._running = False

    @property
    def bot(self) -> Bot:
        """Return the lazily-instantiated underlying ``aiogram.Bot`` object.

        Returns:
            Configured ``aiogram.Bot`` instance.

        Example::

            raw_bot = bot_instance.bot
        """
        # RU: Ленивое создание экземпляра aiogram.Bot.
        if self._bot is None:
            self._bot = Bot(token=self.config.token, parse_mode=self.config.parse_mode)
        return self._bot

    @property
    def dp(self) -> Dispatcher:
        """Return the lazily-instantiated ``aiogram.Dispatcher``.

        Returns:
            ``aiogram.Dispatcher`` bound to this bot.

        Example::

            dispatcher = bot_instance.dp
        """
        # RU: Ленивое создание диспетчера aiogram.
        if self._dp is None:
            self._dp = Dispatcher(self.bot)
        return self._dp

    async def start(self) -> None:
        """Start the bot in long-polling mode.

        Blocks until polling is stopped by calling :meth:`stop`.
        Sets :attr:`_running` to ``True`` before entering the polling loop.

        Example::

            await bot.start()
        """
        # RU: Запускает бота в режиме long-polling; блокирует до остановки.
        logger.info("Starting Aiogram bot")
        self._running = True
        await self.dp.start_polling(self.bot)

    async def stop(self) -> None:
        """Stop the polling loop and close the bot session.

        Stops the dispatcher, closes the underlying HTTP session, and sets
        :attr:`_running` to ``False``.

        Example::

            await bot.stop()
        """
        # RU: Останавливает polling и закрывает HTTP-сессию бота.
        logger.info("Stopping Aiogram bot")
        await self.dp.stop_polling()
        await self.bot.session.close()
        self._running = False
        logger.info("Aiogram bot stopped")

    @property
    def is_running(self) -> bool:
        """Indicate whether the polling loop is currently active.

        Returns:
            ``True`` if the bot is polling, ``False`` otherwise.

        Example::

            if bot.is_running:
                print("Bot is active")
        """
        # RU: Возвращает True, если бот запущен.
        return self._running

    def command(self, commands: str | list[str]) -> Callable:
        """Return a decorator that registers a command handler.

        Args:
            commands: A single command string or list of command strings
                (without the leading ``/``).

        Returns:
            aiogram message handler decorator.

        Example::

            @bot.command("start")
            async def on_start(message):
                await message.reply("Hello!")
        """
        # RU: Декоратор для регистрации обработчика одной или нескольких команд.
        if isinstance(commands, str):
            commands = [commands]
        return self.dp.message.register(commands=commands)

    def message_handler(self, **filters: Any) -> Callable:
        """Return a decorator that registers a message handler with filters.

        Args:
            **filters: Keyword filters forwarded to
                ``Dispatcher.message.register``.

        Returns:
            aiogram message handler decorator.

        Example::

            @bot.message_handler(content_types=["photo"])
            async def on_photo(message):
                await message.reply("Nice photo!")
        """
        # RU: Декоратор для регистрации обработчика сообщений с произвольными фильтрами.
        return self.dp.message.register(**filters)

    async def send_message(
        self, chat_id: int | str, text: str, **kwargs: Any
    ) -> Message:
        """Send a text message to the specified chat.

        Args:
            chat_id: Target chat identifier (integer ID or ``@username``).
            text: Message text.
            **kwargs: Additional keyword arguments forwarded to
                ``aiogram.Bot.send_message``.

        Returns:
            Sent ``aiogram.types.Message`` object.

        Example::

            msg = await bot.send_message(chat_id=123456, text="Hello!")
        """
        # RU: Отправляет текстовое сообщение в указанный чат.
        return await self.bot.send_message(chat_id, text, **kwargs)

    async def delete_message(self, chat_id: int | str, message_id: int) -> bool:
        """Delete a specific message from a chat.

        Args:
            chat_id: Chat identifier.
            message_id: ID of the message to delete.

        Returns:
            ``True`` on success as returned by aiogram.

        Raises:
            aiogram.exceptions.TelegramBadRequest: If the message cannot be
                deleted (e.g. too old or missing permissions).

        Example::

            await bot.delete_message(chat_id=123456, message_id=789)
        """
        # RU: Удаляет сообщение из указанного чата.
        return await self.bot.delete_message(chat_id, message_id)


__all__ = ["AiogramBot", "AiogramConfig"]
