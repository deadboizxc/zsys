"""IClient — abstract contract for messaging platform client implementations.

Defines the base structural Protocol interface that all bot and userbot
clients must satisfy: lifecycle management and basic messaging.
"""
# RU: Интерфейс IClient — базовый контракт для клиентов платформ обмена сообщениями.
# RU: Все бот- и юзербот-клиенты должны соответствовать этому протоколу.

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IClient(Protocol):
    """Abstract contract for all messaging platform clients.

    Both bot clients (IBot) and userbot clients share this base interface.
    Provides lifecycle management and a minimal messaging capability that
    every implementation must guarantee.

    Concrete implementations include:
        - ``zsys.telegram.TdlibClient``: TDLib-based userbot/bot client
    """

    # RU: Базовый контракт для всех клиентов платформ обмена сообщениями.

    async def start(self) -> None:
        """Connect to the messaging platform and begin processing updates.

        Implementations must establish the underlying network connection
        and set ``is_running`` to True upon success.

        Raises:
            ClientError: If the connection cannot be established.
            AuthenticationError: If credentials are invalid.
        """
        # RU: Подключиться к платформе и начать обработку обновлений.
        ...

    async def stop(self) -> None:
        """Gracefully disconnect and release all held resources.

        Implementations must finish in-flight handlers, close the
        connection, and set ``is_running`` to False.
        """
        # RU: Отключиться от платформы и освободить все ресурсы.
        ...

    async def send_message(self, chat_id: int | str, text: str, **kwargs: Any) -> Any:
        """Send a text message to the specified chat.

        Args:
            chat_id: Target chat — integer ID or string username (e.g. ``"@channel"``).
            text: UTF-8 message content.
            **kwargs: Platform-specific parameters (parse_mode, reply_to, etc.).

        Returns:
            Platform-specific message object for the sent message.

        Raises:
            ClientError: If the message cannot be delivered.
        """
        # RU: Отправить текстовое сообщение в указанный чат.
        ...

    @property
    def is_running(self) -> bool:
        """Whether the client is currently connected and active.

        Returns:
            True if the client is running, False if stopped or not yet started.
        """
        # RU: True, если клиент активен и обрабатывает обновления.
        ...


__all__ = [
    "IClient",
]
