"""
Bot interaction utilities for Pyrogram userbots.

Provides helpers for interacting with bots and tracking messages.
"""

import asyncio
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogram.types import Message

__all__ = [
    'interact_with',
    'interact_with_to_delete',
    'clear_interaction_messages',
    'wait_for_reply',
]

# List of message IDs to delete after interaction
interact_with_to_delete: List[int] = []


def clear_interaction_messages() -> None:
    """Clear the list of messages to delete."""
    global interact_with_to_delete
    interact_with_to_delete.clear()


async def interact_with(
    message: "Message",
    timeout: int = 5,
    check_self: bool = True
) -> "Message":
    """
    Wait for bot response to a sent message.
    
    Monitors chat history waiting for bot to reply to the sent message.
    Automatically tracks message IDs for later deletion.
    
    Args:
        message: Message object sent to bot (must contain chat.id and _client)
        timeout: Maximum seconds to wait for response
        check_self: If True, wait for message not from self
        
    Returns:
        Response message from bot
        
    Raises:
        RuntimeError: If bot doesn't respond within timeout
        
    Examples:
        >>> sent = await client.send_message(bot_id, "/start")
        >>> response = await interact_with(sent)
        >>> print(response.text)
        
    Notes:
        - Uses interact_with_to_delete to track message IDs for cleanup
        - Initial 1 second delay to ensure message delivery
    """
    await asyncio.sleep(1)  # Initial delay for message delivery
    
    client = message._client
    chat_id = message.chat.id
    
    for _ in range(timeout):
        # Get latest message in chat
        async for response in client.get_chat_history(chat_id=chat_id, limit=1):
            if check_self and hasattr(response, 'from_user'):
                if response.from_user and not response.from_user.is_self:
                    # Found response from bot
                    interact_with_to_delete.extend([message.id, response.id])
                    return response
            elif not check_self:
                if response.id != message.id:
                    interact_with_to_delete.extend([message.id, response.id])
                    return response
        
        await asyncio.sleep(1)
    
    raise RuntimeError(f"Bot didn't respond within {timeout} seconds")


async def wait_for_reply(
    client,
    chat_id: int,
    message_id: int,
    timeout: int = 30,
    poll_interval: float = 0.5
) -> Optional["Message"]:
    """
    Wait for a reply to specific message.
    
    Args:
        client: Pyrogram client
        chat_id: Chat ID to monitor
        message_id: ID of message to wait reply to
        timeout: Maximum seconds to wait
        poll_interval: Seconds between checks
        
    Returns:
        Reply message or None if timeout
    """
    elapsed = 0
    
    while elapsed < timeout:
        async for msg in client.get_chat_history(chat_id=chat_id, limit=10):
            if (hasattr(msg, 'reply_to_message_id') and 
                msg.reply_to_message_id == message_id):
                return msg
        
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
    
    return None
