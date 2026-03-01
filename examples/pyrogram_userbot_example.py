"""
Example: Simple Pyrogram Userbot with SQLite Storage

This example demonstrates how to create a Pyrogram userbot
that tracks message statistics using SQLite storage.

Install:
    pip install zsys[telegram-pyrogram]

Run:
    python examples/pyrogram_userbot_example.py
"""

import asyncio
from zsys.telegram.pyrogram.client import PyrogramClient, PyrogramConfig
from zsys.storage.sqlite import SQLiteStorage
from zsys.core.logging import get_logger

logger = get_logger(__name__)


async def main():
    """Main function."""
    
    # Configure Pyrogram client
    config = PyrogramConfig(
        api_id=12345,  # Replace with your API ID
        api_hash="your_api_hash",  # Replace with your API Hash
        session_name="my_userbot"
    )
    
    # Initialize client and storage
    client = PyrogramClient(config)
    storage = SQLiteStorage("userbot_data.db")
    
    # Connect storage
    await storage.connect()
    logger.info("Storage connected")
    
    # Message counter handler
    @client.on_message()
    async def message_handler(client_obj, message):
        """Track message statistics."""
        if not message.from_user:
            return
        
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Update user message count
        user_key = f"user:{user_id}:messages"
        count = await storage.get(user_key) or 0
        count += 1
        await storage.set(user_key, count)
        
        # Update chat message count
        chat_key = f"chat:{chat_id}:messages"
        chat_count = await storage.get(chat_key) or 0
        chat_count += 1
        await storage.set(chat_key, chat_count)
        
        logger.info(
            f"Message from {message.from_user.username or user_id} "
            f"in chat {chat_id}: total {count} messages"
        )
        
        # Send notification every 100 messages
        if count % 100 == 0:
            await message.reply(
                f"🎉 Congratulations! You've sent {count} messages!"
            )
    
    # Stats command
    @client.on_message()
    async def stats_command(client_obj, message):
        """Show statistics."""
        if not message.text or not message.text.startswith("/stats"):
            return
        
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        user_count = await storage.get(f"user:{user_id}:messages") or 0
        chat_count = await storage.get(f"chat:{chat_id}:messages") or 0
        
        stats_text = (
            f"📊 **Statistics**\n\n"
            f"Your messages: {user_count}\n"
            f"Chat messages: {chat_count}"
        )
        
        await message.reply(stats_text)
    
    # Start client
    logger.info("Starting Pyrogram client...")
    await client.start()
    logger.info("Client started! Press Ctrl+C to stop")
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping client...")
        await client.stop()
        await storage.disconnect()
        logger.info("Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())
