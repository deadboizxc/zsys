"""
Core Userbot Decorators - Message handler decorators for Pyrogram.

Based on zxc_userbot helpers but made universal.
"""

from typing import Callable, TypeVar, Any, Awaitable
from functools import wraps

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def with_reply(func: F) -> F:
    """Decorator that requires message to be a reply.

    Usage:
        @with_reply
        async def delete_command(client, message):
            await message.reply_to_message.delete()
    """

    @wraps(func)
    async def wrapped(client: Any, message: Any) -> Any:
        if not hasattr(message, "reply_to_message") or not message.reply_to_message:
            await message.edit("<b>Reply to message is required</b>")
            return None
        return await func(client, message)

    return wrapped  # type: ignore


def with_args(text: str = "<b>Arguments required</b>") -> Callable[[F], F]:
    """Decorator that requires command to have arguments.

    Usage:
        @with_args("Usage: .echo <text>")
        async def echo_command(client, message):
            args = message.text.split(maxsplit=1)[1]
            await message.edit(args)
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapped(client: Any, message: Any) -> Any:
            if not hasattr(message, "text") or not message.text:
                await message.edit(text)
                return None

            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                await message.edit(text)
                return None

            return await func(client, message)

        return wrapped  # type: ignore

    return decorator


__all__ = ["with_reply", "with_args"]
