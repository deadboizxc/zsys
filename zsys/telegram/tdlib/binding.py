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

# New async / bot callback types
TG_RESULT_FN      = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_char_p,
                                      ctypes.c_void_p)
TG_USER_CB_FN     = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p,
                                      ctypes.c_void_p)
TG_CHAT_CB_FN     = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p,
                                      ctypes.c_void_p)
TG_MEMBER_CB_FN   = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p,
                                      ctypes.c_void_p)
TG_MEMBERS_CB_FN  = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p,
                                      ctypes.c_int, ctypes.c_void_p)
TG_MESSAGES_CB_FN = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p,
                                      ctypes.c_int, ctypes.c_void_p)
TG_FILE_CB_FN     = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p,
                                      ctypes.c_void_p)
TG_DIALOGS_CB_FN  = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p,
                                      ctypes.c_int, ctypes.c_void_p)
TG_CALLBACK_QUERY_FN = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int64,
                                          ctypes.c_int64, ctypes.c_char_p,
                                          ctypes.c_void_p)
TG_INLINE_QUERY_FN   = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int64,
                                          ctypes.c_int64, ctypes.c_char_p,
                                          ctypes.c_char_p, ctypes.c_void_p)
TG_MEMBER_EVENT_FN   = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int64,
                                          ctypes.c_void_p, ctypes.c_void_p)

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

# Permission flags (TG_PERM_*)
TG_PERM_SEND_MESSAGES = 0x001
TG_PERM_SEND_MEDIA    = 0x002
TG_PERM_SEND_POLLS    = 0x004
TG_PERM_SEND_OTHER    = 0x008
TG_PERM_ADD_PREVIEWS  = 0x010
TG_PERM_CHANGE_INFO   = 0x020
TG_PERM_INVITE_USERS  = 0x040
TG_PERM_PIN_MESSAGES  = 0x080
TG_PERM_ALL           = 0x0FF

# Admin rights flags (TG_ADMIN_*)
TG_ADMIN_MANAGE_CHAT      = 0x001
TG_ADMIN_POST_MESSAGES    = 0x002
TG_ADMIN_EDIT_MESSAGES    = 0x004
TG_ADMIN_DELETE_MESSAGES  = 0x008
TG_ADMIN_BAN_USERS        = 0x010
TG_ADMIN_INVITE_USERS     = 0x020
TG_ADMIN_PIN_MESSAGES     = 0x040
TG_ADMIN_PROMOTE_MEMBERS  = 0x080
TG_ADMIN_CHANGE_INFO      = 0x100
TG_ADMIN_MANAGE_VIDEO     = 0x200
TG_ADMIN_ANONYMOUS        = 0x400
TG_ADMIN_ALL              = 0x7FF


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

        # bot handlers
        lib.tg_on_callback_query.restype  = ctypes.c_int32
        lib.tg_on_callback_query.argtypes = [ctypes.c_void_p,
                                              TG_CALLBACK_QUERY_FN, ctypes.c_void_p]
        lib.tg_on_inline_query.restype    = ctypes.c_int32
        lib.tg_on_inline_query.argtypes   = [ctypes.c_void_p,
                                              TG_INLINE_QUERY_FN, ctypes.c_void_p]
        lib.tg_on_new_chat_member.restype  = ctypes.c_int32
        lib.tg_on_new_chat_member.argtypes = [ctypes.c_void_p,
                                               TG_MEMBER_EVENT_FN, ctypes.c_void_p]
        lib.tg_on_left_chat_member.restype  = ctypes.c_int32
        lib.tg_on_left_chat_member.argtypes = [ctypes.c_void_p,
                                                TG_MEMBER_EVENT_FN, ctypes.c_void_p]
        lib.tg_answer_callback_query.restype  = ctypes.c_int
        lib.tg_answer_callback_query.argtypes = [ctypes.c_void_p, ctypes.c_int64,
                                                  ctypes.c_char_p, ctypes.c_int,
                                                  ctypes.c_int]

        # message accessors
        lib.tg_msg_id.restype              = ctypes.c_int64
        lib.tg_msg_id.argtypes             = [ctypes.c_void_p]
        lib.tg_msg_chat_id.restype         = ctypes.c_int64
        lib.tg_msg_chat_id.argtypes        = [ctypes.c_void_p]
        lib.tg_msg_sender_id.restype       = ctypes.c_int64
        lib.tg_msg_sender_id.argtypes      = [ctypes.c_void_p]
        lib.tg_msg_text.restype            = ctypes.c_char_p
        lib.tg_msg_text.argtypes           = [ctypes.c_void_p]
        lib.tg_msg_is_out.restype          = ctypes.c_int
        lib.tg_msg_is_out.argtypes         = [ctypes.c_void_p]
        lib.tg_msg_reply_to.restype        = ctypes.c_int64
        lib.tg_msg_reply_to.argtypes       = [ctypes.c_void_p]
        lib.tg_msg_is_private.restype      = ctypes.c_int
        lib.tg_msg_is_private.argtypes     = [ctypes.c_void_p]
        lib.tg_msg_is_group.restype        = ctypes.c_int
        lib.tg_msg_is_group.argtypes       = [ctypes.c_void_p]
        lib.tg_msg_is_channel.restype      = ctypes.c_int
        lib.tg_msg_is_channel.argtypes     = [ctypes.c_void_p]
        # new message accessors
        lib.tg_msg_date.restype            = ctypes.c_int64
        lib.tg_msg_date.argtypes           = [ctypes.c_void_p]
        lib.tg_msg_has_photo.restype       = ctypes.c_int
        lib.tg_msg_has_photo.argtypes      = [ctypes.c_void_p]
        lib.tg_msg_has_video.restype       = ctypes.c_int
        lib.tg_msg_has_video.argtypes      = [ctypes.c_void_p]
        lib.tg_msg_has_audio.restype       = ctypes.c_int
        lib.tg_msg_has_audio.argtypes      = [ctypes.c_void_p]
        lib.tg_msg_has_document.restype    = ctypes.c_int
        lib.tg_msg_has_document.argtypes   = [ctypes.c_void_p]
        lib.tg_msg_has_sticker.restype     = ctypes.c_int
        lib.tg_msg_has_sticker.argtypes    = [ctypes.c_void_p]
        lib.tg_msg_has_voice.restype       = ctypes.c_int
        lib.tg_msg_has_voice.argtypes      = [ctypes.c_void_p]
        lib.tg_msg_has_animation.restype   = ctypes.c_int
        lib.tg_msg_has_animation.argtypes  = [ctypes.c_void_p]
        lib.tg_msg_has_location.restype    = ctypes.c_int
        lib.tg_msg_has_location.argtypes   = [ctypes.c_void_p]
        lib.tg_msg_has_contact.restype     = ctypes.c_int
        lib.tg_msg_has_contact.argtypes    = [ctypes.c_void_p]
        lib.tg_msg_media_type.restype      = ctypes.c_int
        lib.tg_msg_media_type.argtypes     = [ctypes.c_void_p]
        lib.tg_msg_file_id.restype         = ctypes.c_int32
        lib.tg_msg_file_id.argtypes        = [ctypes.c_void_p]
        lib.tg_msg_views.restype           = ctypes.c_int32
        lib.tg_msg_views.argtypes          = [ctypes.c_void_p]
        lib.tg_msg_caption.restype         = ctypes.c_char_p
        lib.tg_msg_caption.argtypes        = [ctypes.c_void_p]
        lib.tg_msg_sender_chat_id.restype  = ctypes.c_int64
        lib.tg_msg_sender_chat_id.argtypes = [ctypes.c_void_p]
        lib.tg_msg_from_user.restype       = ctypes.c_void_p
        lib.tg_msg_from_user.argtypes      = [ctypes.c_void_p]
        lib.tg_msg_reply_to_message.restype  = ctypes.c_void_p
        lib.tg_msg_reply_to_message.argtypes = [ctypes.c_void_p]
        # array helpers
        lib.tg_message_at.restype  = ctypes.c_void_p
        lib.tg_message_at.argtypes = [ctypes.c_void_p, ctypes.c_int]
        lib.tg_member_at.restype   = ctypes.c_void_p
        lib.tg_member_at.argtypes  = [ctypes.c_void_p, ctypes.c_int]

        # actions — existing
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

        # new send actions
        lib.tg_send_animation.restype   = ctypes.c_int
        lib.tg_send_animation.argtypes  = [ctypes.c_void_p, ctypes.c_int64,
                                            ctypes.c_char_p, ctypes.c_char_p]
        lib.tg_send_sticker.restype     = ctypes.c_int
        lib.tg_send_sticker.argtypes    = [ctypes.c_void_p, ctypes.c_int64,
                                            ctypes.c_char_p]
        lib.tg_send_voice.restype       = ctypes.c_int
        lib.tg_send_voice.argtypes      = [ctypes.c_void_p, ctypes.c_int64,
                                            ctypes.c_char_p, ctypes.c_char_p]
        lib.tg_send_video_note.restype  = ctypes.c_int
        lib.tg_send_video_note.argtypes = [ctypes.c_void_p, ctypes.c_int64,
                                            ctypes.c_char_p]
        lib.tg_send_location.restype    = ctypes.c_int
        lib.tg_send_location.argtypes   = [ctypes.c_void_p, ctypes.c_int64,
                                            ctypes.c_double, ctypes.c_double]
        lib.tg_send_contact.restype     = ctypes.c_int
        lib.tg_send_contact.argtypes    = [ctypes.c_void_p, ctypes.c_int64,
                                            ctypes.c_char_p, ctypes.c_char_p,
                                            ctypes.c_char_p]
        lib.tg_send_dice.restype        = ctypes.c_int
        lib.tg_send_dice.argtypes       = [ctypes.c_void_p, ctypes.c_int64,
                                            ctypes.c_char_p]
        lib.tg_send_chat_action.restype  = ctypes.c_int
        lib.tg_send_chat_action.argtypes = [ctypes.c_void_p, ctypes.c_int64,
                                             ctypes.c_char_p]
        lib.tg_copy_message.restype     = ctypes.c_int
        lib.tg_copy_message.argtypes    = [ctypes.c_void_p, ctypes.c_int64,
                                            ctypes.c_int64, ctypes.c_int64]
        lib.tg_send_text_ex.restype     = ctypes.c_int
        lib.tg_send_text_ex.argtypes    = [ctypes.c_void_p, ctypes.c_int64,
                                            ctypes.c_char_p, ctypes.c_char_p,
                                            ctypes.c_int64, ctypes.c_char_p]
        lib.tg_edit_text_ex.restype     = ctypes.c_int
        lib.tg_edit_text_ex.argtypes    = [ctypes.c_void_p, ctypes.c_int64,
                                            ctypes.c_int64, ctypes.c_char_p,
                                            ctypes.c_char_p, ctypes.c_char_p]
        lib.tg_delete_messages.restype  = ctypes.c_int
        lib.tg_delete_messages.argtypes = [ctypes.c_void_p, ctypes.c_int64,
                                            ctypes.c_void_p, ctypes.c_int,
                                            ctypes.c_int]
        lib.tg_pin_message.restype      = ctypes.c_int
        lib.tg_pin_message.argtypes     = [ctypes.c_void_p, ctypes.c_int64,
                                            ctypes.c_int64, ctypes.c_int]
        lib.tg_unpin_message.restype    = ctypes.c_int
        lib.tg_unpin_message.argtypes   = [ctypes.c_void_p, ctypes.c_int64,
                                            ctypes.c_int64]
        lib.tg_unpin_all.restype        = ctypes.c_int
        lib.tg_unpin_all.argtypes       = [ctypes.c_void_p, ctypes.c_int64]
        lib.tg_read_chat.restype        = ctypes.c_int
        lib.tg_read_chat.argtypes       = [ctypes.c_void_p, ctypes.c_int64]
        lib.tg_read_mentions.restype    = ctypes.c_int
        lib.tg_read_mentions.argtypes   = [ctypes.c_void_p, ctypes.c_int64]

        # async getters
        lib.tg_get_user.restype      = ctypes.c_int
        lib.tg_get_user.argtypes     = [ctypes.c_void_p, ctypes.c_int64,
                                         TG_USER_CB_FN, ctypes.c_void_p]
        lib.tg_get_chat.restype      = ctypes.c_int
        lib.tg_get_chat.argtypes     = [ctypes.c_void_p, ctypes.c_int64,
                                         TG_CHAT_CB_FN, ctypes.c_void_p]
        lib.tg_get_member.restype    = ctypes.c_int
        lib.tg_get_member.argtypes   = [ctypes.c_void_p, ctypes.c_int64,
                                         ctypes.c_int64,
                                         TG_MEMBER_CB_FN, ctypes.c_void_p]
        lib.tg_get_members.restype   = ctypes.c_int
        lib.tg_get_members.argtypes  = [ctypes.c_void_p, ctypes.c_int64,
                                         ctypes.c_int, ctypes.c_int,
                                         TG_MEMBERS_CB_FN, ctypes.c_void_p]
        lib.tg_get_admins.restype    = ctypes.c_int
        lib.tg_get_admins.argtypes   = [ctypes.c_void_p, ctypes.c_int64,
                                         TG_MEMBERS_CB_FN, ctypes.c_void_p]
        lib.tg_get_messages.restype  = ctypes.c_int
        lib.tg_get_messages.argtypes = [ctypes.c_void_p, ctypes.c_int64,
                                         ctypes.c_void_p, ctypes.c_int,
                                         TG_MESSAGES_CB_FN, ctypes.c_void_p]
        lib.tg_get_history.restype   = ctypes.c_int
        lib.tg_get_history.argtypes  = [ctypes.c_void_p, ctypes.c_int64,
                                         ctypes.c_int64, ctypes.c_int,
                                         TG_MESSAGES_CB_FN, ctypes.c_void_p]
        lib.tg_get_dialogs.restype   = ctypes.c_int
        lib.tg_get_dialogs.argtypes  = [ctypes.c_void_p, ctypes.c_int,
                                         TG_DIALOGS_CB_FN, ctypes.c_void_p]
        lib.tg_get_file.restype      = ctypes.c_int
        lib.tg_get_file.argtypes     = [ctypes.c_void_p, ctypes.c_int32,
                                         TG_FILE_CB_FN, ctypes.c_void_p]
        lib.tg_search_public_chat.restype  = ctypes.c_int
        lib.tg_search_public_chat.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                               TG_CHAT_CB_FN, ctypes.c_void_p]

        # chat management
        lib.tg_join_chat.restype           = ctypes.c_int
        lib.tg_join_chat.argtypes          = [ctypes.c_void_p, ctypes.c_int64]
        lib.tg_join_by_link.restype        = ctypes.c_int
        lib.tg_join_by_link.argtypes       = [ctypes.c_void_p, ctypes.c_char_p]
        lib.tg_leave_chat.restype          = ctypes.c_int
        lib.tg_leave_chat.argtypes         = [ctypes.c_void_p, ctypes.c_int64]
        lib.tg_set_chat_title.restype      = ctypes.c_int
        lib.tg_set_chat_title.argtypes     = [ctypes.c_void_p, ctypes.c_int64,
                                               ctypes.c_char_p]
        lib.tg_set_chat_description.restype  = ctypes.c_int
        lib.tg_set_chat_description.argtypes = [ctypes.c_void_p, ctypes.c_int64,
                                                 ctypes.c_char_p]
        lib.tg_set_chat_photo.restype      = ctypes.c_int
        lib.tg_set_chat_photo.argtypes     = [ctypes.c_void_p, ctypes.c_int64,
                                               ctypes.c_char_p]
        lib.tg_delete_chat_photo.restype   = ctypes.c_int
        lib.tg_delete_chat_photo.argtypes  = [ctypes.c_void_p, ctypes.c_int64]
        lib.tg_archive_chat.restype        = ctypes.c_int
        lib.tg_archive_chat.argtypes       = [ctypes.c_void_p, ctypes.c_int64]
        lib.tg_unarchive_chat.restype      = ctypes.c_int
        lib.tg_unarchive_chat.argtypes     = [ctypes.c_void_p, ctypes.c_int64]
        lib.tg_mute_chat.restype           = ctypes.c_int
        lib.tg_mute_chat.argtypes          = [ctypes.c_void_p, ctypes.c_int64,
                                               ctypes.c_int]
        lib.tg_get_invite_link.restype     = ctypes.c_int
        lib.tg_get_invite_link.argtypes    = [ctypes.c_void_p, ctypes.c_int64,
                                               TG_RAW_FN, ctypes.c_void_p]

        # chat accessors
        lib.tg_chat_id.restype             = ctypes.c_int64
        lib.tg_chat_id.argtypes            = [ctypes.c_void_p]
        lib.tg_chat_title.restype          = ctypes.c_char_p
        lib.tg_chat_title.argtypes         = [ctypes.c_void_p]
        lib.tg_chat_username.restype       = ctypes.c_char_p
        lib.tg_chat_username.argtypes      = [ctypes.c_void_p]
        lib.tg_chat_type.restype           = ctypes.c_int
        lib.tg_chat_type.argtypes          = [ctypes.c_void_p]
        lib.tg_chat_members_count.restype  = ctypes.c_int32
        lib.tg_chat_members_count.argtypes = [ctypes.c_void_p]
        lib.tg_chat_linked_chat_id.restype = ctypes.c_int64
        lib.tg_chat_linked_chat_id.argtypes= [ctypes.c_void_p]
        lib.tg_chat_permissions.restype    = ctypes.c_uint32
        lib.tg_chat_permissions.argtypes   = [ctypes.c_void_p]

        # member accessors
        lib.tg_member_user.restype          = ctypes.c_void_p
        lib.tg_member_user.argtypes         = [ctypes.c_void_p]
        lib.tg_member_status.restype        = ctypes.c_char_p
        lib.tg_member_status.argtypes       = [ctypes.c_void_p]
        lib.tg_member_is_admin.restype      = ctypes.c_int
        lib.tg_member_is_admin.argtypes     = [ctypes.c_void_p]
        lib.tg_member_is_creator.restype    = ctypes.c_int
        lib.tg_member_is_creator.argtypes   = [ctypes.c_void_p]
        lib.tg_member_until_date.restype    = ctypes.c_int32
        lib.tg_member_until_date.argtypes   = [ctypes.c_void_p]
        lib.tg_member_can_ban.restype       = ctypes.c_int
        lib.tg_member_can_ban.argtypes      = [ctypes.c_void_p]
        lib.tg_member_can_delete_msgs.restype  = ctypes.c_int
        lib.tg_member_can_delete_msgs.argtypes = [ctypes.c_void_p]
        lib.tg_member_can_invite.restype    = ctypes.c_int
        lib.tg_member_can_invite.argtypes   = [ctypes.c_void_p]
        lib.tg_member_can_pin.restype       = ctypes.c_int
        lib.tg_member_can_pin.argtypes      = [ctypes.c_void_p]

        # file accessors
        lib.tg_file_id.restype           = ctypes.c_int32
        lib.tg_file_id.argtypes          = [ctypes.c_void_p]
        lib.tg_file_size.restype         = ctypes.c_int64
        lib.tg_file_size.argtypes        = [ctypes.c_void_p]
        lib.tg_file_local_path.restype   = ctypes.c_char_p
        lib.tg_file_local_path.argtypes  = [ctypes.c_void_p]
        lib.tg_file_is_downloaded.restype  = ctypes.c_int
        lib.tg_file_is_downloaded.argtypes = [ctypes.c_void_p]
        lib.tg_file_mime_type.restype    = ctypes.c_char_p
        lib.tg_file_mime_type.argtypes   = [ctypes.c_void_p]
        lib.tg_file_name.restype         = ctypes.c_char_p
        lib.tg_file_name.argtypes        = [ctypes.c_void_p]

        # admin
        lib.tg_ban_member.restype           = ctypes.c_int
        lib.tg_ban_member.argtypes          = [ctypes.c_void_p, ctypes.c_int64,
                                               ctypes.c_int64, ctypes.c_int32]
        lib.tg_unban_member.restype         = ctypes.c_int
        lib.tg_unban_member.argtypes        = [ctypes.c_void_p, ctypes.c_int64,
                                               ctypes.c_int64]
        lib.tg_restrict_member.restype      = ctypes.c_int
        lib.tg_restrict_member.argtypes     = [ctypes.c_void_p, ctypes.c_int64,
                                               ctypes.c_int64, ctypes.c_uint32,
                                               ctypes.c_int32]
        lib.tg_promote_member.restype       = ctypes.c_int
        lib.tg_promote_member.argtypes      = [ctypes.c_void_p, ctypes.c_int64,
                                               ctypes.c_int64, ctypes.c_uint32,
                                               ctypes.c_char_p]
        lib.tg_set_chat_permissions.restype  = ctypes.c_int
        lib.tg_set_chat_permissions.argtypes = [ctypes.c_void_p, ctypes.c_int64,
                                                ctypes.c_uint32]
        lib.tg_kick_member.restype          = ctypes.c_int
        lib.tg_kick_member.argtypes         = [ctypes.c_void_p, ctypes.c_int64,
                                               ctypes.c_int64]

        # user management
        lib.tg_block_user.restype    = ctypes.c_int
        lib.tg_block_user.argtypes   = [ctypes.c_void_p, ctypes.c_int64]
        lib.tg_unblock_user.restype  = ctypes.c_int
        lib.tg_unblock_user.argtypes = [ctypes.c_void_p, ctypes.c_int64]

        # account
        lib.tg_set_username.restype      = ctypes.c_int
        lib.tg_set_username.argtypes     = [ctypes.c_void_p, ctypes.c_char_p]
        lib.tg_update_profile.restype    = ctypes.c_int
        lib.tg_update_profile.argtypes   = [ctypes.c_void_p, ctypes.c_char_p,
                                             ctypes.c_char_p, ctypes.c_char_p]
        lib.tg_set_profile_photo.restype  = ctypes.c_int
        lib.tg_set_profile_photo.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        lib.tg_set_online.restype         = ctypes.c_int
        lib.tg_set_online.argtypes        = [ctypes.c_void_p, ctypes.c_int]

        # raw invoke
        lib.tg_invoke.restype  = ctypes.c_int64
        lib.tg_invoke.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                   TG_RESULT_FN, ctypes.c_void_p]

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
    "TG_RESULT_FN", "TG_USER_CB_FN", "TG_CHAT_CB_FN",
    "TG_MEMBER_CB_FN", "TG_MEMBERS_CB_FN", "TG_MESSAGES_CB_FN",
    "TG_FILE_CB_FN", "TG_DIALOGS_CB_FN",
    "TG_CALLBACK_QUERY_FN", "TG_INLINE_QUERY_FN", "TG_MEMBER_EVENT_FN",
    "TG_FILTER_NONE", "TG_FILTER_OUTGOING", "TG_FILTER_INCOMING",
    "TG_FILTER_PRIVATE", "TG_FILTER_GROUP", "TG_FILTER_CHANNEL",
    "TG_FILTER_TEXT", "TG_FILTER_PHOTO", "TG_FILTER_VIDEO",
    "TG_FILTER_DOCUMENT", "TG_FILTER_AUDIO", "TG_FILTER_STICKER",
    "TG_FILTER_BOT_CMD", "TG_FILTER_ALL",
]
