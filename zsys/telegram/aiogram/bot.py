"""
Aiogram Bot Implementation

Implements IBot interface for Telegram using Aiogram.
"""

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
    """Aiogram bot configuration."""
    
    token: str
    parse_mode: str = "HTML"
    
    class Config:
        env_prefix = "BOT_"


class AiogramBot(IBot):
    """
    Aiogram implementation of IBot interface.
    
    Usage:
        config = AiogramConfig(token="YOUR_BOT_TOKEN")
        bot = AiogramBot(config)
        
        @bot.command("start")
        async def start_handler(message: Message):
            await message.reply("Hello!")
        
        await bot.start()
    """
    
    def __init__(self, config: AiogramConfig):
        """
        Initialize Aiogram bot.
        
        Args:
            config: Aiogram configuration
        """
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
        """Get underlying Aiogram bot."""
        if self._bot is None:
            self._bot = Bot(
                token=self.config.token,
                parse_mode=self.config.parse_mode
            )
        return self._bot
    
    @property
    def dp(self) -> Dispatcher:
        """Get dispatcher."""
        if self._dp is None:
            self._dp = Dispatcher(self.bot)
        return self._dp
    
    async def start(self) -> None:
        """Start the bot."""
        logger.info("Starting Aiogram bot")
        self._running = True
        await self.dp.start_polling(self.bot)
    
    async def stop(self) -> None:
        """Stop the bot."""
        logger.info("Stopping Aiogram bot")
        await self.dp.stop_polling()
        await self.bot.session.close()
        self._running = False
        logger.info("Aiogram bot stopped")
    
    @property
    def is_running(self) -> bool:
        """Check if bot is running."""
        return self._running
    
    def command(self, commands: str | list[str]) -> Callable:
        """Decorator for command handlers."""
        if isinstance(commands, str):
            commands = [commands]
        return self.dp.message.register(commands=commands)
    
    def message_handler(self, **filters: Any) -> Callable:
        """Decorator for message handlers."""
        return self.dp.message.register(**filters)
    
    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        **kwargs: Any
    ) -> Message:
        """Send a message."""
        return await self.bot.send_message(chat_id, text, **kwargs)
    
    async def delete_message(
        self,
        chat_id: int | str,
        message_id: int
    ) -> bool:
        """Delete a message."""
        return await self.bot.delete_message(chat_id, message_id)


__all__ = ["AiogramBot", "AiogramConfig"]
