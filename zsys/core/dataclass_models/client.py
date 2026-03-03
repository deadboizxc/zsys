"""BaseClient dataclass — platform-agnostic client configuration model.

Represents the configuration and runtime state of a bot or userbot client
without ORM or platform-specific dependencies.
"""
# RU: Датакласс BaseClient — платформо-независимая модель конфигурации клиента.
# RU: Хранит конфигурацию и состояние бот- или юзербот-клиента.

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class ClientStatus(str, Enum):
    """Enumeration of possible client lifecycle states.

    Values are lowercase strings for easy serialisation and logging.
    """

    # RU: Перечисление состояний жизненного цикла клиента.
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class BaseClient:
    """Platform-agnostic bot/userbot client model.

    Represents the configuration and runtime state of a messaging client.
    Used for in-memory state tracking and serialisation; not an ORM model.

    Attributes:
        name: Unique client name or identifier string.
        status: Current lifecycle state of the client.
        api_id: Platform API ID (required for Telegram MTProto clients).
        api_hash: Platform API hash (required for Telegram MTProto clients).
        token: Bot API token for bot-mode clients; None for userbots.
        session_name: Session file name for userbot clients; None for bots.
        phone_number: Phone number for userbot clients; None for bots.
        started_at: Timestamp when the client last transitioned to RUNNING.
        stopped_at: Timestamp when the client last stopped or errored.
        error_message: Last error message when status is ERROR; None otherwise.
        created_at: Timestamp when this client record was created.
    """

    # RU: Платформо-независимая модель бот- или юзербот-клиента.

    name: str
    """Client name/identifier"""

    status: ClientStatus = ClientStatus.IDLE
    """Current client status"""

    api_id: Optional[int] = None
    """API ID (for Telegram, etc.)"""

    api_hash: Optional[str] = None
    """API hash"""

    token: Optional[str] = None
    """Bot token (for bot clients)"""

    session_name: Optional[str] = None
    """Session name (for userbots)"""

    phone_number: Optional[str] = None
    """Phone number (for userbots)"""

    started_at: Optional[datetime] = None
    """When client was started"""

    stopped_at: Optional[datetime] = None
    """When client was stopped"""

    error_message: Optional[str] = None
    """Last error message (if status is ERROR)"""

    created_at: datetime = field(default_factory=datetime.now)
    """When this client was created"""

    @property
    def is_running(self) -> bool:
        """True if the client is currently in RUNNING state.

        Returns:
            True when status equals ``ClientStatus.RUNNING``.
        """
        # RU: True, если клиент находится в состоянии RUNNING.
        return self.status == ClientStatus.RUNNING

    @property
    def is_bot(self) -> bool:
        """True if this is a bot client (authenticated with a token).

        Returns:
            True when ``token`` is not None.
        """
        # RU: True, если клиент является ботом (аутентифицирован токеном).
        return self.token is not None

    @property
    def is_userbot(self) -> bool:
        """True if this is a userbot client (authenticated via phone/session).

        Returns:
            True when either ``phone_number`` or ``session_name`` is set.
        """
        # RU: True, если клиент является юзерботом (phone или session заданы).
        return self.phone_number is not None or self.session_name is not None

    @property
    def uptime(self) -> Optional[int]:
        """Seconds elapsed since the client started running.

        Returns:
            Uptime in seconds as an integer, or None if the client is not
            currently running.
        """
        # RU: Количество секунд с момента запуска; None если клиент не работает.
        if self.started_at and self.status == ClientStatus.RUNNING:
            return int((datetime.now() - self.started_at).total_seconds())
        return None

    def to_dict(self) -> dict:
        """Serialise the client to a plain dictionary.

        Returns:
            Dictionary with all fields; timestamps as ISO-8601 strings.
        """
        # RU: Сериализовать клиент в словарь; временные метки в ISO-8601.
        return {
            "name": self.name,
            "status": self.status.value,
            "is_bot": self.is_bot,
            "is_userbot": self.is_userbot,
            "is_running": self.is_running,
            "uptime": self.uptime,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
        }
