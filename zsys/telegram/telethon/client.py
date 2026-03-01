"""
Telethon Client Implementation

Implements IUserBot interface for Telegram using Telethon.
"""

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
    """Telethon client configuration."""
    
    api_id: int
    api_hash: str
    session_name: str = "my_account"
    phone_number: Optional[str] = None
    bot_token: Optional[str] = None
    
    class Config:
        env_prefix = "TELETHON_"


class TelethonClient(IBot):
    """
    Telethon implementation of IUserBot interface.
    
    Usage:
        config = TelethonConfig(
            api_id=12345,
            api_hash="abc123",
            session_name="my_session"
        )
        
        client = TelethonClient(config)
        
        @client.on_message()
        async def handler(event):
            await event.reply("Hello!")
        
        await client.start()
    """
    
    def __init__(self, config: TelethonConfig):
        """
        Initialize Telethon client.
        
        Args:
            config: Telethon configuration
        """
        if not TELETHON_AVAILABLE:
            raise ClientError(
                "Telethon is not installed. Install with: pip install zsys[telegram-telethon]"
            )
        
        self.config = config
        self._client: Optional[TelegramClient] = None
        self._running = False
    
    @property
    def client(self) -> TelegramClient:
        """Get underlying Telethon client."""
        if self._client is None:
            self._client = TelegramClient(
                self.config.session_name,
                self.config.api_id,
                self.config.api_hash
            )
        return self._client
    
    async def start(self) -> None:
        """Start the client."""
        logger.info(f"Starting Telethon client: {self.config.session_name}")
        
        if self.config.bot_token:
            await self.client.start(bot_token=self.config.bot_token)
        else:
            await self.client.start(phone=self.config.phone_number)
        
        self._running = True
        logger.info("Telethon client started")
    
    async def stop(self) -> None:
        """Stop the client."""
        logger.info("Stopping Telethon client")
        await self.client.disconnect()
        self._running = False
        logger.info("Telethon client stopped")
    
    @property
    def is_running(self) -> bool:
        """Check if client is running."""
        return self._running
    
    def on_message(self, filters_obj: Any = None) -> Callable:
        """Decorator for message handlers."""
        if filters_obj:
            return self.client.on(events.NewMessage(**filters_obj))
        return self.client.on(events.NewMessage())
    
    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        **kwargs: Any
    ) -> Message:
        """Send a message."""
        return await self.client.send_message(chat_id, text, **kwargs)
    
    async def edit_message_text(
        self,
        chat_id: int | str,
        message_id: int,
        text: str,
        **kwargs: Any
    ) -> Message:
        """Edit a message."""
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
        """Forward messages."""
        return await self.client.forward_messages(
            chat_id, message_ids, from_chat_id, **kwargs
        )
    
    async def download_media(
        self,
        message: Message,
        file_name: str | None = None,
        **kwargs: Any
    ) -> str:
        """Download media from message."""
        return await self.client.download_media(message, file=file_name, **kwargs)


__all__ = ["TelethonClient", "TelethonConfig"]
