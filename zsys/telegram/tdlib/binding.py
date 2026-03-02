"""ctypes bindings for libtg.so (the zsys TDLib C wrapper).

Loads libtg.so and exposes the full tg.h C API as Python callables.
Gracefully degrades: import succeeds even without the library, but
instantiating LibTg will raise RuntimeError with a helpful message.

Usage (internal, not public API)::

    from zsys.telegram.tdlib.binding import libtg, TG_FILTER_ALL
    libtg.tg_send_text(client_ptr, chat_id, b"hello", b"html")
"""
# RU: ctypes обёртка над libtg.so. Все типы из tg.h.

from __future__ import annotations

import ctypes
import os
from pathlib import Path
from typing import Optional

# ── callback function types (match tg.h typedefs) ────────────────────────── #

TG_ASK_PHONE_FN  = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)
TG_ASK_CODE_FN   = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)
TG_ASK_PASS_FN   = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)
TG_READY_FN      = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)
TG_ERROR_FN      = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int,
                                     ctypes.c_char_p, ctypes.c_void_p)
TG_MESSAGE_FN    = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p,
                                     ctypes.c_void_p)
TG_RAW_FN        = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_char_p,
                                     ctypes.c_void_p)
TG_PROGRESS_FN   = ctypes.CFUNCTYPE(None, ctypes.c_int32, ctypes.c_int64,
                                     ctypes.c_int64, ctypes.c_void_p)

# ── filter constants (from tg.h) ─────────────────────────────────────────── #

TG_FILTER_NONE     = 0x0000
TG_FILTER_OUTGOING = 0x0001
TG_FILTER_INCOMING = 0x0002
TG_FILTER_PRIVATE  = 0x0004
TG_FILTER_GROUP    = 0x0008
TG_FILTER_CHANNEL  = 0x0010
TG_FILTER_TEXT     = 0x0020
TG_FILTER_PHOTO    = 0x0040
TG_FILTER_VIDEO    = 0x0080
TG_FILTER_DOCUMENT = 0x0100
TG_FILTER_AUDIO    = 0x0200
TG_FILTER_STICKER  = 0x0400
TG_FILTER_BOT_CMD  = 0x0800
TG_FILTER_ALL      = 0xFFFF


# ── library loader ────────────────────────────────────────────────────────── #

class _LibTg:
    """Lazy-loaded wrapper around libtg.so with fully typed C signatures."""

    def __init__(self) -> None:
        self._lib: Optional[ctypes.CDLL] = None
        self._loaded = False

    def _load(self) -> ctypes.CDLL:
        if self._lib:
            return self._lib

        candidates = ["libtg.so", "libtg.so.0"]
        here = Path(__file__).resolve().parent  # zsys/telegram/tdlib/

        # Look next to this file (built in-place) or in c/build/
        for rel in (".", "c/build", "c/build/c"):
            candidate = here / rel / "libtg.so"
            if candidate.exists():
                candidates.insert(0, str(candidate))

        for name in candidates:
            try:
                lib = ctypes.CDLL(name)
                self._lib = lib
                self._setup_signatures(lib)
                self._loaded = True
                return lib
            except OSError:
                continue

        raise RuntimeError(
            "libtg.so not found. Build it with:\n"
            "  cmake -B build/c && cmake --build build/c --target tg\n"
            "  (requires TDLib installed or TDLIB_DIR set)"
        )

    def _setup_signatures(self, lib: ctypes.CDLL) -> None:
        # RU: Аннотируем все функции из tg.h для ctypes.

        # config
        lib.tg_config_new.restype  = ctypes.c_void_p
        lib.tg_config_new.argtypes = [ctypes.c_int32, ctypes.c_char_p]
        lib.tg_config_free.restype  = None
        lib.tg_config_free.argtypes = [ctypes.c_void_p]

        # client lifecycle
        lib.tg_client_new.restype  = ctypes.c_void_p
        lib.tg_client_new.argtypes = [ctypes.c_void_p]
        lib.tg_client_free.restype  = None
        lib.tg_client_free.argtypes = [ctypes.c_void_p]

        lib.tg_client_set_auth_handlers.restype  = None
        lib.tg_client_set_auth_handlers.argtypes = [
            ctypes.c_void_p,
            TG_ASK_PHONE_FN, TG_ASK_CODE_FN, TG_ASK_PASS_FN,
            TG_READY_FN, TG_ERROR_FN,
            ctypes.c_void_p,
        ]

        lib.tg_client_start.restype  = ctypes.c_int
        lib.tg_client_start.argtypes = [ctypes.c_void_p]
        lib.tg_client_stop.restype   = None
        lib.tg_client_stop.argtypes  = [ctypes.c_void_p]
        lib.tg_client_run.restype    = None
        lib.tg_client_run.argtypes   = [ctypes.c_void_p]
        lib.tg_client_wait_ready.restype  = ctypes.c_int
        lib.tg_client_wait_ready.argtypes = [ctypes.c_void_p, ctypes.c_int]

        lib.tg_client_provide_phone.restype  = None
        lib.tg_client_provide_phone.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        lib.tg_client_provide_code.restype   = None
        lib.tg_client_provide_code.argtypes  = [ctypes.c_void_p, ctypes.c_char_p]
        lib.tg_client_provide_pass.restype   = None
        lib.tg_client_provide_pass.argtypes  = [ctypes.c_void_p, ctypes.c_char_p]

        # handlers
        lib.tg_on_message.restype  = ctypes.c_int32
        lib.tg_on_message.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                                       TG_MESSAGE_FN, ctypes.c_void_p]
        lib.tg_on_edited.restype   = ctypes.c_int32
        lib.tg_on_edited.argtypes  = [ctypes.c_void_p, ctypes.c_uint32,
                                       TG_MESSAGE_FN, ctypes.c_void_p]
        lib.tg_on_raw.restype      = ctypes.c_int32
        lib.tg_on_raw.argtypes     = [ctypes.c_void_p, ctypes.c_char_p,
                                       TG_RAW_FN, ctypes.c_void_p]
        lib.tg_remove_handler.restype  = None
        lib.tg_remove_handler.argtypes = [ctypes.c_void_p, ctypes.c_int32]

        # message accessors
        lib.tg_msg_id.restype          = ctypes.c_int64
        lib.tg_msg_id.argtypes         = [ctypes.c_void_p]
        lib.tg_msg_chat_id.restype     = ctypes.c_int64
        lib.tg_msg_chat_id.argtypes    = [ctypes.c_void_p]
        lib.tg_msg_sender_id.restype   = ctypes.c_int64
        lib.tg_msg_sender_id.argtypes  = [ctypes.c_void_p]
        lib.tg_msg_text.restype        = ctypes.c_char_p
        lib.tg_msg_text.argtypes       = [ctypes.c_void_p]
        lib.tg_msg_is_out.restype      = ctypes.c_int
        lib.tg_msg_is_out.argtypes     = [ctypes.c_void_p]
        lib.tg_msg_reply_to.restype    = ctypes.c_int64
        lib.tg_msg_reply_to.argtypes   = [ctypes.c_void_p]
        lib.tg_msg_is_private.restype  = ctypes.c_int
        lib.tg_msg_is_private.argtypes = [ctypes.c_void_p]
        lib.tg_msg_is_group.restype    = ctypes.c_int
        lib.tg_msg_is_group.argtypes   = [ctypes.c_void_p]
        lib.tg_msg_is_channel.restype  = ctypes.c_int
        lib.tg_msg_is_channel.argtypes = [ctypes.c_void_p]

        # actions
        lib.tg_send_text.restype    = ctypes.c_int
        lib.tg_send_text.argtypes   = [ctypes.c_void_p, ctypes.c_int64,
                                        ctypes.c_char_p, ctypes.c_char_p]
        lib.tg_send_photo.restype   = ctypes.c_int
        lib.tg_send_photo.argtypes  = [ctypes.c_void_p, ctypes.c_int64,
                                        ctypes.c_char_p, ctypes.c_char_p]
        lib.tg_send_video.restype   = ctypes.c_int
        lib.tg_send_video.argtypes  = [ctypes.c_void_p, ctypes.c_int64,
                                        ctypes.c_char_p, ctypes.c_char_p]
        lib.tg_send_audio.restype   = ctypes.c_int
        lib.tg_send_audio.argtypes  = [ctypes.c_void_p, ctypes.c_int64,
                                        ctypes.c_char_p, ctypes.c_char_p]
        lib.tg_send_doc.restype     = ctypes.c_int
        lib.tg_send_doc.argtypes    = [ctypes.c_void_p, ctypes.c_int64,
                                        ctypes.c_char_p, ctypes.c_char_p]
        lib.tg_reply_text.restype   = ctypes.c_int
        lib.tg_reply_text.argtypes  = [ctypes.c_void_p, ctypes.c_void_p,
                                        ctypes.c_char_p, ctypes.c_char_p]
        lib.tg_edit_text.restype    = ctypes.c_int
        lib.tg_edit_text.argtypes   = [ctypes.c_void_p, ctypes.c_int64,
                                        ctypes.c_int64, ctypes.c_char_p,
                                        ctypes.c_char_p]
        lib.tg_delete_msg.restype   = ctypes.c_int
        lib.tg_delete_msg.argtypes  = [ctypes.c_void_p, ctypes.c_int64,
                                        ctypes.c_int64]
        lib.tg_forward.restype      = ctypes.c_int
        lib.tg_forward.argtypes     = [ctypes.c_void_p, ctypes.c_int64,
                                        ctypes.c_int64, ctypes.c_int64]
        lib.tg_react.restype        = ctypes.c_int
        lib.tg_react.argtypes       = [ctypes.c_void_p, ctypes.c_int64,
                                        ctypes.c_int64, ctypes.c_char_p]

        # self info
        lib.tg_me_id.restype          = ctypes.c_int64
        lib.tg_me_id.argtypes         = [ctypes.c_void_p]
        lib.tg_me_username.restype    = ctypes.c_char_p
        lib.tg_me_username.argtypes   = [ctypes.c_void_p]
        lib.tg_me_first_name.restype  = ctypes.c_char_p
        lib.tg_me_first_name.argtypes = [ctypes.c_void_p]

        # memory
        lib.tg_free.restype  = None
        lib.tg_free.argtypes = [ctypes.c_char_p]

    def __getattr__(self, name: str):
        return getattr(self._load(), name)

    @property
    def available(self) -> bool:
        try:
            self._load()
            return True
        except RuntimeError:
            return False


# Singleton — import this everywhere
libtg = _LibTg()

__all__ = [
    "libtg",
    "TG_ASK_PHONE_FN", "TG_ASK_CODE_FN", "TG_ASK_PASS_FN",
    "TG_READY_FN", "TG_ERROR_FN", "TG_MESSAGE_FN", "TG_RAW_FN",
    "TG_PROGRESS_FN",
    "TG_FILTER_NONE", "TG_FILTER_OUTGOING", "TG_FILTER_INCOMING",
    "TG_FILTER_PRIVATE", "TG_FILTER_GROUP", "TG_FILTER_CHANNEL",
    "TG_FILTER_TEXT", "TG_FILTER_PHOTO", "TG_FILTER_VIDEO",
    "TG_FILTER_DOCUMENT", "TG_FILTER_AUDIO", "TG_FILTER_STICKER",
    "TG_FILTER_BOT_CMD", "TG_FILTER_ALL",
]
