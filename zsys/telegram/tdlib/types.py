"""Python wrappers for tg_message_t and related C types.

These objects wrap a raw C pointer (valid ONLY inside a handler callback).
Use them to read message fields without dealing with ctypes directly.

Note:
    Message, EditedMessage objects must NOT be stored outside the callback.
    The underlying C memory is stack-allocated and freed after the callback returns.
    If you need to keep message data, copy the fields explicitly.
"""
# RU: Python обёртки для типов из tg.h. Валидны только внутри хендлера.

from __future__ import annotations

import ctypes
from typing import Optional


class Message:
    """Wrapper around tg_message_t* — valid only inside a handler callback.

    Provides Pyrogram-style attribute access over the C struct accessors.

    Attributes:
        id: Message ID.
        chat_id: Chat ID.
        sender_id: Sender user/chat ID.
        text: Message text, or None if not a text message.
        is_out: True if the message was sent by the current user.
        reply_to_id: ID of the replied-to message, or 0.
        is_private: True if sent in a private chat.
        is_group: True if sent in a group or supergroup.
        is_channel: True if sent in a channel.

    Example::

        @client.on_message(TG_FILTER_INCOMING | TG_FILTER_TEXT)
        def handler(client, msg, _):
            print(msg.text, msg.chat_id)
    """

    __slots__ = (
        "_lib", "_ptr",
        "id", "chat_id", "sender_id", "text",
        "is_out", "reply_to_id",
        "is_private", "is_group", "is_channel",
    )

    def __init__(self, lib, ptr: ctypes.c_void_p) -> None:
        # RU: Сразу считываем все поля пока указатель валиден.
        self._lib = lib
        self._ptr = ptr

        self.id         = lib.tg_msg_id(ptr)
        self.chat_id    = lib.tg_msg_chat_id(ptr)
        self.sender_id  = lib.tg_msg_sender_id(ptr)
        self.is_out     = bool(lib.tg_msg_is_out(ptr))
        self.reply_to_id = lib.tg_msg_reply_to(ptr)
        self.is_private = bool(lib.tg_msg_is_private(ptr))
        self.is_group   = bool(lib.tg_msg_is_group(ptr))
        self.is_channel = bool(lib.tg_msg_is_channel(ptr))

        raw = lib.tg_msg_text(ptr)
        self.text: Optional[str] = raw.decode("utf-8", errors="replace") if raw else None

    def __repr__(self) -> str:
        return (f"<Message id={self.id} chat_id={self.chat_id} "
                f"text={self.text!r:.40}>")


__all__ = ["Message"]
