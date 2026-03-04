"""Composable message filters — mirrors Pyrogram's ``filters`` module.

Filters can be combined with ``&``, ``|``, ``~``::

    from zsys.telegram.filters import text, private, bot_command

    @client.on_message(text & private)
    async def handler(client, msg):
        ...

    @client.on_message(~bot_command)
    async def handler2(client, msg):
        ...
"""
# RU: Компонуемые фильтры сообщений. Аналог Pyrogram filters.

from __future__ import annotations

from typing import Any, Callable, Optional

from zsys.telegram.binding import (
    TG_FILTER_ALL,
    TG_FILTER_AUDIO,
    TG_FILTER_BOT_CMD,
    TG_FILTER_CHANNEL,
    TG_FILTER_DOCUMENT,
    TG_FILTER_GROUP,
    TG_FILTER_INCOMING,
    TG_FILTER_OUTGOING,
    TG_FILTER_PHOTO,
    TG_FILTER_PRIVATE,
    TG_FILTER_STICKER,
    TG_FILTER_TEXT,
    TG_FILTER_VIDEO,
)


class Filter:
    """Composable message filter.

    Subclass this to create custom filters.  Supports ``&``, ``|``, ``~``.

    Example::

        loud = filters.create(lambda _, __, m: m.text and m.text.isupper())
    """

    def __call__(self, client: Any, message: Any) -> bool:
        return True

    def __and__(self, other: "Filter") -> "_CompositeFilter":
        return _CompositeFilter("and", self, other)

    def __or__(self, other: "Filter") -> "_CompositeFilter":
        return _CompositeFilter("or", self, other)

    def __invert__(self) -> "_CompositeFilter":
        return _CompositeFilter("not", self, None)

    # Convenience: let the filter be used directly as a bitmask for
    # tg_on_message when it wraps a single bitmask constant.
    @property
    def bitmask(self) -> int:
        return TG_FILTER_ALL

    def __int__(self) -> int:
        return self.bitmask


class _BitmaskFilter(Filter):
    """Filter backed by a C-level TG_FILTER_* bitmask.

    The C layer has already applied the filter before Python is called,
    so __call__ simply returns True.
    """

    def __init__(self, bitmask: int) -> None:
        self._bitmask = bitmask

    def __call__(self, client: Any, message: Any) -> bool:
        return True  # C already filtered

    @property
    def bitmask(self) -> int:
        return self._bitmask

    def __int__(self) -> int:
        return self._bitmask


class _LambdaFilter(Filter):
    """Filter backed by a Python callable(client, _, message) -> bool."""

    def __init__(self, fn: Callable) -> None:
        self._fn = fn

    def __call__(self, client: Any, message: Any) -> bool:
        try:
            return bool(self._fn(client, None, message))
        except Exception:
            return False

    @property
    def bitmask(self) -> int:
        # Lambda filters need all messages; C-level filtering disabled.
        return TG_FILTER_ALL


class _CompositeFilter(Filter):
    """Logical composition of two filters."""

    def __init__(self, op: str, left: Filter, right: Optional[Filter]) -> None:
        self._op = op
        self._left = left
        self._right = right

    def __call__(self, client: Any, message: Any) -> bool:
        if self._op == "and":
            return self._left(client, message) and self._right(client, message)  # type: ignore[arg-type]
        if self._op == "or":
            return self._left(client, message) or self._right(client, message)  # type: ignore[arg-type]
        if self._op == "not":
            return not self._left(client, message)
        return True

    @property
    def bitmask(self) -> int:
        # Use the intersection of both bitmasks; fall back to ALL for lambdas.
        lb = self._left.bitmask
        rb = self._right.bitmask if self._right else TG_FILTER_ALL
        if self._op == "and":
            return (
                lb & rb
                if (lb != TG_FILTER_ALL and rb != TG_FILTER_ALL)
                else TG_FILTER_ALL
            )
        return TG_FILTER_ALL


def create(func: Callable) -> Filter:
    """Create a custom filter from a callable.

    The callable receives ``(client, _, message)`` and must return bool.

    Example::

        has_url = filters.create(lambda _, __, m: m.text and "http" in m.text)
    """
    return _LambdaFilter(func)


# ── Standard bitmask-based filters ───────────────────────────────────────── #

private = _BitmaskFilter(TG_FILTER_PRIVATE)
group = _BitmaskFilter(TG_FILTER_GROUP)
channel = _BitmaskFilter(TG_FILTER_CHANNEL)
text = _BitmaskFilter(TG_FILTER_TEXT)
photo = _BitmaskFilter(TG_FILTER_PHOTO)
video = _BitmaskFilter(TG_FILTER_VIDEO)
document = _BitmaskFilter(TG_FILTER_DOCUMENT)
audio = _BitmaskFilter(TG_FILTER_AUDIO)
sticker = _BitmaskFilter(TG_FILTER_STICKER)
incoming = _BitmaskFilter(TG_FILTER_INCOMING)
outgoing = _BitmaskFilter(TG_FILTER_OUTGOING)
bot_command = _BitmaskFilter(TG_FILTER_BOT_CMD)
all_ = _BitmaskFilter(TG_FILTER_ALL)

# ── Lambda-based filters (Python-level check required) ────────────────────── #

me = create(lambda _, __, m: getattr(m, "is_out", False))
bot = create(
    lambda _, __, m: m.from_user.is_bot if getattr(m, "from_user", None) else False
)
mentioned = create(lambda _, __, m: getattr(m, "is_mentioned", False))
reply = create(lambda _, __, m: m.reply_to_message is not None)
forwarded = create(lambda _, __, m: getattr(m, "forward_from", None) is not None)
contact = create(
    lambda _, __, m: (
        getattr(m.from_user, "is_contact", False)
        if getattr(m, "from_user", None)
        else False
    )
)

__all__ = [
    "Filter",
    "create",
    "private",
    "group",
    "channel",
    "text",
    "photo",
    "video",
    "document",
    "audio",
    "sticker",
    "incoming",
    "outgoing",
    "bot_command",
    "all_",
    "me",
    "bot",
    "mentioned",
    "reply",
    "forwarded",
    "contact",
]
