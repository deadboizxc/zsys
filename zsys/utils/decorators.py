"""
Decorators for bot command handlers.

Provides reusable decorators for:
- Reply validation
- Argument checking
- Admin access control
- Error handling
"""

from typing import Callable, TypeVar, Any, Awaitable, Optional, List
from functools import wraps

# TypeVar for preserving function signatures
F = TypeVar('F', bound=Callable[..., Awaitable[Any]])


def with_reply(func: F) -> F:
    """Decorator that requires message to be a reply.
    
    Args:
        func: Async handler function
        
    Returns:
        Wrapped function that checks for reply_to_message
        
    Example:
        @with_reply
        async def delete_command(client, message):
            await message.reply_to_message.delete()
    """
    @wraps(func)
    async def wrapped(client: Any, message: Any) -> Any:
        if not hasattr(message, 'reply_to_message') or not message.reply_to_message:
            await message.edit("<b>⚠️ Reply to message is required</b>")
            return None
        return await func(client, message)
    
    return wrapped  # type: ignore


def with_args(error_text: str = "<b>⚠️ Arguments required</b>") -> Callable[[F], F]:
    """Decorator that requires command to have arguments.
    
    Args:
        error_text: Text to show if no arguments provided
        
    Returns:
        Decorator function
        
    Example:
        @with_args("Usage: .echo <text>")
        async def echo_command(client, message):
            text = message.text.split(maxsplit=1)[1]
            await message.edit(text)
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapped(client: Any, message: Any) -> Any:
            if not hasattr(message, 'text') or not message.text:
                await message.edit(error_text)
                return None
            
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                await message.edit(error_text)
                return None
            
            return await func(client, message)
        
        return wrapped  # type: ignore
    
    return decorator


def admin_only(admin_ids: Optional[List[int]] = None) -> Callable[[F], F]:
    """Decorator that restricts command to admin users.
    
    Args:
        admin_ids: List of allowed user IDs (None = owner only)
        
    Returns:
        Decorator function
        
    Example:
        @admin_only([123456789, 987654321])
        async def restart_command(client, message):
            await message.edit("Restarting...")
            restart_bot()
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapped(client: Any, message: Any) -> Any:
            user_id = message.from_user.id if hasattr(message, 'from_user') else None
            
            if not user_id:
                return None
            
            # If admin_ids provided, check against list
            if admin_ids and user_id not in admin_ids:
                await message.edit("<b>⛔️ Admin access required</b>")
                return None
            
            # If no admin_ids, check if user is owner (me)
            if not admin_ids:
                is_owner = getattr(message, 'outgoing', False) or getattr(message, 'from_user', None) == client.me
                if not is_owner:
                    await message.edit("<b>⛔️ Owner access required</b>")
                    return None
            
            return await func(client, message)
        
        return wrapped  # type: ignore
    
    return decorator


def error_handler(
    fallback_message: str = "<b>❌ An error occurred</b>",
    log_errors: bool = True
) -> Callable[[F], F]:
    """Decorator that handles exceptions in command handlers.
    
    Args:
        fallback_message: Message to show on error
        log_errors: Whether to log errors
        
    Returns:
        Decorator function
        
    Example:
        @error_handler("Failed to process command")
        async def risky_command(client, message):
            result = await some_risky_operation()
            await message.edit(result)
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapped(client: Any, message: Any) -> Any:
            try:
                return await func(client, message)
            except Exception as e:
                if log_errors:
                    # Try to log if logger available
                    try:
                        from core.log import get_logger
                        logger = get_logger(__name__)
                        logger.error(f"Error in {func.__name__}: {e}")
                    except ImportError:
                        pass
                
                # Show error to user
                error_msg = f"{fallback_message}\n\n<code>{str(e)}</code>"
                try:
                    await message.edit(error_msg)
                except Exception:
                    pass
                
                return None
        
        return wrapped  # type: ignore
    
    return decorator


def typing_action(func: F) -> F:
    """Decorator that shows typing action while processing.
    
    Args:
        func: Async handler function
        
    Returns:
        Wrapped function with typing action
        
    Example:
        @typing_action
        async def long_command(client, message):
            await asyncio.sleep(5)
            await message.edit("Done!")
    """
    @wraps(func)
    async def wrapped(client: Any, message: Any) -> Any:
        chat_id = message.chat.id if hasattr(message, 'chat') else None
        
        if chat_id:
            try:
                await client.send_chat_action(chat_id, "typing")
            except Exception:
                pass
        
        return await func(client, message)
    
    return wrapped  # type: ignore


def log_command(func: F) -> F:
    """Decorator that logs command execution.
    
    Args:
        func: Async handler function
        
    Returns:
        Wrapped function with logging
        
    Example:
        @log_command
        async def important_command(client, message):
            await message.edit("Executed!")
    """
    @wraps(func)
    async def wrapped(client: Any, message: Any) -> Any:
        try:
            from core.log import get_logger
            logger = get_logger(__name__)
            
            user = getattr(message.from_user, 'id', 'unknown') if hasattr(message, 'from_user') else 'unknown'
            command = message.text if hasattr(message, 'text') else 'no text'
            
            logger.info(f"Command executed by {user}: {command}")
        except ImportError:
            pass
        
        return await func(client, message)
    
    return wrapped  # type: ignore
