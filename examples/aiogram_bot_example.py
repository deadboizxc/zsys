"""
Example: Simple Aiogram Bot with Redis Storage

This example demonstrates how to create an Aiogram bot
that stores user sessions in Redis.

Install:
    pip install zsys[telegram-aiogram,storage-redis]

Run:
    python examples/aiogram_bot_example.py
"""

import asyncio
from zsys.telegram.aiogram.bot import AiogramBot, AiogramConfig
from zsys.storage.redis import RedisStorage
from zsys.core.logging import get_logger

logger = get_logger(__name__)


async def main():
    """Main function."""
    
    # Configure bot
    config = AiogramConfig(
        token="YOUR_BOT_TOKEN",  # Replace with your bot token
        parse_mode="HTML"
    )
    
    # Initialize bot and storage
    bot = AiogramBot(config)
    storage = RedisStorage("redis://localhost:6379/0")
    
    # Connect storage
    await storage.connect()
    logger.info("Redis storage connected")
    
    # Start command
    @bot.command("start")
    async def start_handler(message):
        """Handle /start command."""
        user_id = message.from_user.id
        username = message.from_user.username or "Anonymous"
        
        # Save user session
        await storage.set(
            f"session:{user_id}",
            {"username": username, "started": True},
            expire=3600  # 1 hour
        )
        
        await message.reply(
            f"👋 Hello, {username}!\n\n"
            "I'm a ZSYS bot. Use /help to see available commands."
        )
    
    # Help command
    @bot.command("help")
    async def help_handler(message):
        """Handle /help command."""
        help_text = (
            "🤖 <b>Available Commands</b>\n\n"
            "/start - Start the bot\n"
            "/help - Show this message\n"
            "/echo <text> - Echo your message\n"
            "/session - Show your session info"
        )
        await message.reply(help_text)
    
    # Echo command
    @bot.command("echo")
    async def echo_handler(message):
        """Handle /echo command."""
        text = message.text.replace("/echo ", "")
        await message.reply(f"📣 Echo: {text}")
    
    # Session command
    @bot.command("session")
    async def session_handler(message):
        """Handle /session command."""
        user_id = message.from_user.id
        session = await storage.get(f"session:{user_id}")
        
        if session:
            await message.reply(
                f"📝 <b>Your Session</b>\n\n"
                f"Username: {session.get('username')}\n"
                f"Started: {session.get('started')}"
            )
        else:
            await message.reply("❌ No active session. Use /start to begin.")
    
    # Message handler (for non-commands)
    @bot.message_handler(content_types=["text"])
    async def text_handler(message):
        """Handle text messages."""
        if not message.text.startswith("/"):
            await message.reply(
                "I received your message! Use /help to see available commands."
            )
    
    # Start bot
    logger.info("Starting Aiogram bot...")
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
