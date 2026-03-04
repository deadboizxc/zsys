"""IBot — abstract contract for bot client implementations.

Defines the structural Protocol interface that all bot backends
(aiogram, pyTelegramBotAPI, discord.py, etc.) must satisfy.
"""
# RU: Интерфейс IBot — контракт для реализаций бот-клиентов.
# RU: Структурная типизация (Protocol): явное наследование не требуется.

from typing import Any, Callable, Protocol, runtime_checkable


@runtime_checkable
class IBot(Protocol):
    """Abstract contract for regular bot clients (not userbots).

    All bot backends must expose lifecycle management (start/stop),
    basic messaging (send_message, delete_message), and handler
    registration (command, message_handler).

    Note:
        This is a Protocol-based interface using structural subtyping.
        Implementations do not need to explicitly inherit from IBot.

    Supported platforms:
        - Telegram Bot API (aiogram, pyTelegramBotAPI)
        - Discord (discord.py)
        - Other bot platforms
    """

    # RU: Абстрактный контракт для бот-клиентов (не юзерботов).

    # ===== Lifecycle Management =====

    async def start(self) -> None:
        """Connect to the platform and begin polling or webhook.

        Implementations must establish the underlying connection and
        set ``is_running`` to True on success.
        """
        # RU: Запустить бот и установить соединение с платформой.
        ...

    async def stop(self) -> None:
        """Disconnect from the platform and release all resources.

        Implementations must gracefully stop polling/webhook handlers
        and set ``is_running`` to False.
        """
        # RU: Остановить бот, разорвать соединение и освободить ресурсы.
        ...

    @property
    def is_running(self) -> bool:
        """Whether the bot is currently connected and polling.

        Returns:
            True if the bot is active, False otherwise.
        """
        # RU: True, если бот активен и принимает обновления.
        ...

    # ===== Basic Messaging =====

    async def send_message(self, chat_id: int | str, text: str, **kwargs: Any) -> Any:
        """Send a text message to a chat.

        Args:
            chat_id: Target chat identifier — integer ID or string username.
            text: UTF-8 text content of the message.
            **kwargs: Platform-specific parameters (parse_mode, reply_markup, etc.).

        Returns:
            Platform-specific message object representing the sent message.
        """
        # RU: Отправить текстовое сообщение в чат.
        ...

    async def delete_message(self, chat_id: int | str, message_id: int) -> bool:
        """Delete a message from a chat.

        Args:
            chat_id: Chat identifier where the message lives.
            message_id: Unique identifier of the message to delete.

        Returns:
            True if the message was deleted successfully, False otherwise.
        """
        # RU: Удалить сообщение из чата.
        ...

    # ===== Bot-Specific Features =====

    def command(self, commands: str | list[str]) -> Callable:
        """Return a decorator that registers a command handler.

        Implementations must bind the decorated coroutine to the given
        command trigger(s) so it fires when users send the command.

        Args:
            commands: Command name or list of names (without leading slash).

        Returns:
            Decorator that registers the wrapped function as a handler.

        Example:
            @bot.command("start")
            async def handle_start(message):
                await message.reply("Hello!")
        """
        # RU: Вернуть декоратор регистрации обработчика команды.
        ...

    def message_handler(self, **filters: Any) -> Callable:
        """Return a decorator that registers a message handler with filters.

        Args:
            **filters: Platform-specific message filters
                (content_types, func, regexp, etc.).

        Returns:
            Decorator that registers the wrapped function as a handler.
        """
        # RU: Вернуть декоратор регистрации обработчика сообщений с фильтрами.
        ...


__all__ = [
    "IBot",
]


# Alias for userbot clients — same contract as IBot
IUserBot = IBot
