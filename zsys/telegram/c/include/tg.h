/*
 * tg.h  —  libtg: high-level Telegram C API built on top of TDLib.
 *
 * Single public header. Zero Python / C++ dependencies.
 * Usable from: Python (ctypes/cffi), Go (cgo), Rust (bindgen), Node (ffi-napi).
 *
 * Thread model:
 *   - One global polling thread drives all clients via td_receive().
 *   - Handler callbacks are invoked from the polling thread.
 *     If you need asyncio / event loop integration — post to a queue in your cb.
 *   - tg_message_t* passed to handlers is stack-allocated and valid ONLY
 *     inside the callback. Do not store the pointer.
 *
 * Memory:
 *   - Functions returning char* → free with tg_free().
 *   - Config strings are deep-copied by tg_client_new().
 *   - tg_config_free() frees config; tg_client_free() frees client.
 */

#ifndef TG_H
#define TG_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ── version ────────────────────────────────────────────────────────────── */

#define TG_VERSION_MAJOR  0
#define TG_VERSION_MINOR  2
#define TG_VERSION_PATCH  0

/* ── opaque types ────────────────────────────────────────────────────────── */

typedef struct tg_client      tg_client_t;
typedef struct tg_message     tg_message_t;
typedef struct tg_user        tg_user_t;
typedef struct tg_chat        tg_chat_t;
typedef struct tg_chat_member tg_chat_member_t;
typedef struct tg_file        tg_file_t;
typedef int32_t               tg_handler_id_t;

/* ── enums ───────────────────────────────────────────────────────────────── */

typedef enum {
    TG_CHAT_PRIVATE = 0,
    TG_CHAT_GROUP,
    TG_CHAT_SUPERGROUP,
    TG_CHAT_CHANNEL,
} tg_chat_type_t;

typedef enum {
    TG_MEDIA_NONE = 0,
    TG_MEDIA_PHOTO,
    TG_MEDIA_VIDEO,
    TG_MEDIA_AUDIO,
    TG_MEDIA_DOCUMENT,
    TG_MEDIA_STICKER,
    TG_MEDIA_VOICE,
    TG_MEDIA_ANIMATION,
    TG_MEDIA_VIDEO_NOTE,
    TG_MEDIA_LOCATION,
    TG_MEDIA_CONTACT,
    TG_MEDIA_POLL,
    TG_MEDIA_DICE,
    TG_MEDIA_VENUE,
} tg_media_type_t;

/* ── config ──────────────────────────────────────────────────────────────── */

typedef struct tg_config {
    int32_t     api_id;           /* required */
    const char *api_hash;         /* required */
    const char *session_dir;      /* default: "." */
    const char *session_name;     /* default: "session" */
    const char *bot_token;        /* NULL → userbot mode */
    const char *phone;            /* NULL → bot mode */
    const char *device_model;     /* default: "Desktop" */
    const char *system_version;   /* default: "Linux" */
    const char *app_version;      /* default: "1.0.0" */
    const char *lang_code;        /* default: "en" */
    int         use_test_dc;      /* 0 = production */
    int         log_verbosity;    /* 0=errors, 3=info, 5=debug */
} tg_config_t;

tg_config_t *tg_config_new(int32_t api_id, const char *api_hash);
void         tg_config_free(tg_config_t *cfg);

/* ── auth callbacks ──────────────────────────────────────────────────────── */

typedef void (*tg_ask_phone_fn)(tg_client_t *c, void *ud);
typedef void (*tg_ask_code_fn) (tg_client_t *c, void *ud);
typedef void (*tg_ask_pass_fn) (tg_client_t *c, void *ud);
typedef void (*tg_ready_fn)    (tg_client_t *c, void *ud);
typedef void (*tg_error_fn)    (tg_client_t *c, int code, const char *msg, void *ud);
typedef void (*tg_progress_fn) (int32_t file_id, int64_t done, int64_t total, void *ud);

/* ── result / async callbacks ────────────────────────────────────────────── */

typedef void (*tg_result_fn)     (tg_client_t *c, const char *json, void *ud);
typedef void (*tg_user_cb_fn)    (tg_client_t *c, const tg_user_t *user, void *ud);
typedef void (*tg_chat_cb_fn)    (tg_client_t *c, const tg_chat_t *chat, void *ud);
typedef void (*tg_member_cb_fn)  (tg_client_t *c, const tg_chat_member_t *m, void *ud);
typedef void (*tg_members_cb_fn) (tg_client_t *c, const tg_chat_member_t *members,
                                   int count, void *ud);
typedef void (*tg_messages_cb_fn)(tg_client_t *c, const tg_message_t *msgs,
                                   int count, void *ud);
typedef void (*tg_file_cb_fn)    (tg_client_t *c, const tg_file_t *file, void *ud);
typedef void (*tg_dialogs_cb_fn) (tg_client_t *c, const int64_t *chat_ids,
                                   int count, void *ud);

/* ── bot event callbacks ─────────────────────────────────────────────────── */

typedef void (*tg_callback_query_fn)(tg_client_t *c, int64_t query_id,
                                      int64_t from_id, const char *data, void *ud);
typedef void (*tg_inline_query_fn)  (tg_client_t *c, int64_t query_id,
                                      int64_t from_id, const char *query,
                                      const char *offset, void *ud);
typedef void (*tg_member_event_fn)  (tg_client_t *c, int64_t chat_id,
                                      const tg_user_t *user, void *ud);

/* ── lifecycle ───────────────────────────────────────────────────────────── */

tg_client_t *tg_client_new(const tg_config_t *cfg);
void         tg_client_free(tg_client_t *c);

void tg_client_set_auth_handlers(
    tg_client_t    *c,
    tg_ask_phone_fn ask_phone,
    tg_ask_code_fn  ask_code,
    tg_ask_pass_fn  ask_pass,
    tg_ready_fn     on_ready,
    tg_error_fn     on_error,
    void           *userdata
);

int  tg_client_start(tg_client_t *c);
void tg_client_stop(tg_client_t *c);
void tg_client_run(tg_client_t *c);
int  tg_client_wait_ready(tg_client_t *c, int timeout_sec);

void tg_client_provide_phone(tg_client_t *c, const char *phone);
void tg_client_provide_code (tg_client_t *c, const char *code);
void tg_client_provide_pass (tg_client_t *c, const char *password);

/* ── filters (bitmask, combinable with |) ────────────────────────────────── */

#define TG_FILTER_NONE      0x0000u
#define TG_FILTER_OUTGOING  0x0001u
#define TG_FILTER_INCOMING  0x0002u
#define TG_FILTER_PRIVATE   0x0004u
#define TG_FILTER_GROUP     0x0008u
#define TG_FILTER_CHANNEL   0x0010u
#define TG_FILTER_TEXT      0x0020u
#define TG_FILTER_PHOTO     0x0040u
#define TG_FILTER_VIDEO     0x0080u
#define TG_FILTER_DOCUMENT  0x0100u
#define TG_FILTER_AUDIO     0x0200u
#define TG_FILTER_STICKER   0x0400u
#define TG_FILTER_BOT_CMD   0x0800u  /* text starts with '/' */
#define TG_FILTER_ALL       0xFFFFu

/* ── permission flags (TG_PERM_* for chat/member permissions) ────────────── */

#define TG_PERM_SEND_MESSAGES  0x001u
#define TG_PERM_SEND_MEDIA     0x002u
#define TG_PERM_SEND_POLLS     0x004u
#define TG_PERM_SEND_OTHER     0x008u   /* stickers, gifs */
#define TG_PERM_ADD_PREVIEWS   0x010u
#define TG_PERM_CHANGE_INFO    0x020u
#define TG_PERM_INVITE_USERS   0x040u
#define TG_PERM_PIN_MESSAGES   0x080u
#define TG_PERM_ALL            0x0FFu

/* ── admin rights flags ──────────────────────────────────────────────────── */

#define TG_ADMIN_MANAGE_CHAT      0x001u
#define TG_ADMIN_POST_MESSAGES    0x002u
#define TG_ADMIN_EDIT_MESSAGES    0x004u
#define TG_ADMIN_DELETE_MESSAGES  0x008u
#define TG_ADMIN_BAN_USERS        0x010u
#define TG_ADMIN_INVITE_USERS     0x020u
#define TG_ADMIN_PIN_MESSAGES     0x040u
#define TG_ADMIN_PROMOTE_MEMBERS  0x080u
#define TG_ADMIN_CHANGE_INFO      0x100u
#define TG_ADMIN_MANAGE_VIDEO     0x200u
#define TG_ADMIN_ANONYMOUS        0x400u
#define TG_ADMIN_ALL              0x7FFu

/* ── event handlers ──────────────────────────────────────────────────────── */

typedef void (*tg_message_fn)(tg_client_t *c, const tg_message_t *msg, void *ud);
typedef void (*tg_raw_fn)    (tg_client_t *c, const char *json,         void *ud);

tg_handler_id_t tg_on_message(tg_client_t *c, uint32_t filters,
                               tg_message_fn fn, void *ud);
tg_handler_id_t tg_on_edited (tg_client_t *c, uint32_t filters,
                               tg_message_fn fn, void *ud);
tg_handler_id_t tg_on_raw    (tg_client_t *c, const char *update_type,
                               tg_raw_fn fn, void *ud);
void tg_remove_handler(tg_client_t *c, tg_handler_id_t hid);

/* ── message accessors ───────────────────────────────────────────────────── */

int64_t          tg_msg_id               (const tg_message_t *m);
int64_t          tg_msg_chat_id          (const tg_message_t *m);
int64_t          tg_msg_sender_id        (const tg_message_t *m);
const char      *tg_msg_text             (const tg_message_t *m);
int              tg_msg_is_out           (const tg_message_t *m);
int64_t          tg_msg_reply_to         (const tg_message_t *m);
int              tg_msg_is_private       (const tg_message_t *m);
int              tg_msg_is_group         (const tg_message_t *m);
int              tg_msg_is_channel       (const tg_message_t *m);
/* new accessors */
int64_t          tg_msg_date             (const tg_message_t *m);
int              tg_msg_has_photo        (const tg_message_t *m);
int              tg_msg_has_video        (const tg_message_t *m);
int              tg_msg_has_audio        (const tg_message_t *m);
int              tg_msg_has_document     (const tg_message_t *m);
int              tg_msg_has_sticker      (const tg_message_t *m);
int              tg_msg_has_voice        (const tg_message_t *m);
int              tg_msg_has_animation    (const tg_message_t *m);
int              tg_msg_has_location     (const tg_message_t *m);
int              tg_msg_has_contact      (const tg_message_t *m);
tg_media_type_t  tg_msg_media_type       (const tg_message_t *m);
int32_t          tg_msg_file_id          (const tg_message_t *m);
int32_t          tg_msg_views            (const tg_message_t *m);
const char      *tg_msg_caption          (const tg_message_t *m);
int64_t          tg_msg_sender_chat_id   (const tg_message_t *m);
const tg_user_t    *tg_msg_from_user        (const tg_message_t *m);
const tg_message_t *tg_msg_reply_to_message (const tg_message_t *m);

/* Array traversal helpers (hide struct size from Python) */
const tg_message_t     *tg_message_at(const tg_message_t *arr, int index);
const tg_chat_member_t *tg_member_at (const tg_chat_member_t *arr, int index);

/* ── actions ─────────────────────────────────────────────────────────────── */

int tg_send_text  (tg_client_t *c, int64_t chat_id,
                   const char *text,  const char *parse_mode);
int tg_send_photo (tg_client_t *c, int64_t chat_id,
                   const char *path,  const char *caption);
int tg_send_video (tg_client_t *c, int64_t chat_id,
                   const char *path,  const char *caption);
int tg_send_audio (tg_client_t *c, int64_t chat_id,
                   const char *path,  const char *caption);
int tg_send_doc   (tg_client_t *c, int64_t chat_id,
                   const char *path,  const char *caption);
int tg_reply_text (tg_client_t *c, const tg_message_t *orig,
                   const char *text,  const char *parse_mode);
int tg_edit_text  (tg_client_t *c, int64_t chat_id, int64_t msg_id,
                   const char *text,  const char *parse_mode);
int tg_delete_msg (tg_client_t *c, int64_t chat_id, int64_t msg_id);
int tg_forward    (tg_client_t *c, int64_t to_chat, int64_t from_chat, int64_t msg_id);
int tg_react      (tg_client_t *c, int64_t chat_id, int64_t msg_id, const char *emoji);
int tg_download_file(tg_client_t *c, int32_t file_id, const char *dest_path,
                     tg_progress_fn cb, void *ud);

/* new send variants */
int tg_send_animation  (tg_client_t *c, int64_t chat_id,
                         const char *path, const char *caption);
int tg_send_sticker    (tg_client_t *c, int64_t chat_id,
                         const char *file_id_or_path);
int tg_send_voice      (tg_client_t *c, int64_t chat_id,
                         const char *path, const char *caption);
int tg_send_video_note (tg_client_t *c, int64_t chat_id, const char *path);
int tg_send_location   (tg_client_t *c, int64_t chat_id, double lat, double lon);
int tg_send_contact    (tg_client_t *c, int64_t chat_id,
                         const char *phone, const char *first_name, const char *last_name);
int tg_send_poll       (tg_client_t *c, int64_t chat_id, const char *question,
                         const char **options, int option_count, int is_anonymous);
int tg_send_dice       (tg_client_t *c, int64_t chat_id, const char *emoji);
int tg_send_chat_action(tg_client_t *c, int64_t chat_id, const char *action);
int tg_copy_message    (tg_client_t *c, int64_t to_chat_id,
                         int64_t from_chat_id, int64_t msg_id);
int tg_send_text_ex    (tg_client_t *c, int64_t chat_id, const char *text,
                         const char *parse_mode, int64_t reply_to_msg_id,
                         const char *json_markup);
int tg_edit_text_ex    (tg_client_t *c, int64_t chat_id, int64_t msg_id,
                         const char *text, const char *parse_mode,
                         const char *json_markup);
int tg_delete_messages (tg_client_t *c, int64_t chat_id,
                         const int64_t *msg_ids, int count, int revoke);
int tg_pin_message     (tg_client_t *c, int64_t chat_id, int64_t msg_id,
                         int disable_notification);
int tg_unpin_message   (tg_client_t *c, int64_t chat_id, int64_t msg_id);
int tg_unpin_all       (tg_client_t *c, int64_t chat_id);
int tg_read_chat       (tg_client_t *c, int64_t chat_id);
int tg_read_mentions   (tg_client_t *c, int64_t chat_id);

/* ── async getters ───────────────────────────────────────────────────────── */

int tg_get_user      (tg_client_t *c, int64_t user_id,
                       tg_user_cb_fn cb, void *ud);
int tg_get_chat      (tg_client_t *c, int64_t chat_id,
                       tg_chat_cb_fn cb, void *ud);
int tg_get_member    (tg_client_t *c, int64_t chat_id, int64_t user_id,
                       tg_member_cb_fn cb, void *ud);
int tg_get_members   (tg_client_t *c, int64_t chat_id, int offset, int limit,
                       tg_members_cb_fn cb, void *ud);
int tg_get_admins    (tg_client_t *c, int64_t chat_id,
                       tg_members_cb_fn cb, void *ud);
int tg_get_messages  (tg_client_t *c, int64_t chat_id,
                       const int64_t *msg_ids, int count,
                       tg_messages_cb_fn cb, void *ud);
int tg_get_history   (tg_client_t *c, int64_t chat_id,
                       int64_t from_msg_id, int limit,
                       tg_messages_cb_fn cb, void *ud);
int tg_get_dialogs   (tg_client_t *c, int limit,
                       tg_dialogs_cb_fn cb, void *ud);
int tg_get_file      (tg_client_t *c, int32_t file_id,
                       tg_file_cb_fn cb, void *ud);
int tg_search_public_chat(tg_client_t *c, const char *username,
                           tg_chat_cb_fn cb, void *ud);

/* ── chat management ─────────────────────────────────────────────────────── */

int tg_join_chat           (tg_client_t *c, int64_t chat_id);
int tg_join_by_link        (tg_client_t *c, const char *invite_link);
int tg_leave_chat          (tg_client_t *c, int64_t chat_id);
int tg_set_chat_title      (tg_client_t *c, int64_t chat_id, const char *title);
int tg_set_chat_description(tg_client_t *c, int64_t chat_id, const char *desc);
int tg_set_chat_photo      (tg_client_t *c, int64_t chat_id, const char *path);
int tg_delete_chat_photo   (tg_client_t *c, int64_t chat_id);
int tg_archive_chat        (tg_client_t *c, int64_t chat_id);
int tg_unarchive_chat      (tg_client_t *c, int64_t chat_id);
int tg_mute_chat           (tg_client_t *c, int64_t chat_id, int mute_for_seconds);
int tg_get_invite_link     (tg_client_t *c, int64_t chat_id,
                             tg_raw_fn cb, void *ud);

/* ── chat accessors ──────────────────────────────────────────────────────── */

int64_t     tg_chat_id            (const tg_chat_t *ch);
const char *tg_chat_title         (const tg_chat_t *ch);
const char *tg_chat_username      (const tg_chat_t *ch);
int         tg_chat_type          (const tg_chat_t *ch);
int32_t     tg_chat_members_count (const tg_chat_t *ch);
int64_t     tg_chat_linked_chat_id(const tg_chat_t *ch);
uint32_t    tg_chat_permissions   (const tg_chat_t *ch);

/* ── chat member accessors ───────────────────────────────────────────────── */

const tg_user_t *tg_member_user           (const tg_chat_member_t *m);
const char      *tg_member_status         (const tg_chat_member_t *m);
int              tg_member_is_admin       (const tg_chat_member_t *m);
int              tg_member_is_creator     (const tg_chat_member_t *m);
int32_t          tg_member_until_date     (const tg_chat_member_t *m);
int              tg_member_can_ban        (const tg_chat_member_t *m);
int              tg_member_can_delete_msgs(const tg_chat_member_t *m);
int              tg_member_can_invite     (const tg_chat_member_t *m);
int              tg_member_can_pin        (const tg_chat_member_t *m);

/* ── file accessors ──────────────────────────────────────────────────────── */

int32_t     tg_file_id          (const tg_file_t *f);
int64_t     tg_file_size        (const tg_file_t *f);
const char *tg_file_local_path  (const tg_file_t *f);
int         tg_file_is_downloaded(const tg_file_t *f);
const char *tg_file_mime_type   (const tg_file_t *f);
const char *tg_file_name        (const tg_file_t *f);

/* ── admin ───────────────────────────────────────────────────────────────── */

int tg_ban_member          (tg_client_t *c, int64_t chat_id, int64_t user_id,
                             int32_t until_date);
int tg_unban_member        (tg_client_t *c, int64_t chat_id, int64_t user_id);
int tg_restrict_member     (tg_client_t *c, int64_t chat_id, int64_t user_id,
                             uint32_t perms, int32_t until_date);
int tg_promote_member      (tg_client_t *c, int64_t chat_id, int64_t user_id,
                             uint32_t admin_rights, const char *custom_title);
int tg_set_chat_permissions(tg_client_t *c, int64_t chat_id, uint32_t perms);
int tg_kick_member         (tg_client_t *c, int64_t chat_id, int64_t user_id);

/* ── user management ─────────────────────────────────────────────────────── */

int tg_block_user  (tg_client_t *c, int64_t user_id);
int tg_unblock_user(tg_client_t *c, int64_t user_id);

/* ── account ─────────────────────────────────────────────────────────────── */

int tg_set_username     (tg_client_t *c, const char *username);
int tg_update_profile   (tg_client_t *c, const char *first_name,
                          const char *last_name, const char *bio);
int tg_set_profile_photo(tg_client_t *c, const char *path);
int tg_set_online       (tg_client_t *c, int is_online);

/* ── bot ─────────────────────────────────────────────────────────────────── */

tg_handler_id_t tg_on_callback_query (tg_client_t *c,
                                       tg_callback_query_fn fn, void *ud);
tg_handler_id_t tg_on_inline_query   (tg_client_t *c,
                                       tg_inline_query_fn fn, void *ud);
tg_handler_id_t tg_on_new_chat_member(tg_client_t *c,
                                       tg_member_event_fn fn, void *ud);
tg_handler_id_t tg_on_left_chat_member(tg_client_t *c,
                                        tg_member_event_fn fn, void *ud);
int tg_answer_callback_query(tg_client_t *c, int64_t query_id,
                              const char *text, int show_alert, int cache_time);

/* ── raw invoke ──────────────────────────────────────────────────────────── */

/* Send any raw TDLib JSON request. Result delivered via pending callback. */
int64_t tg_invoke(tg_client_t *c, const char *json, tg_result_fn cb, void *ud);

/* ── self info ───────────────────────────────────────────────────────────── */

int64_t     tg_me_id         (tg_client_t *c);
const char *tg_me_username   (tg_client_t *c);
const char *tg_me_first_name (tg_client_t *c);

/* ── user accessors ──────────────────────────────────────────────────────── */

int64_t     tg_user_id        (const tg_user_t *u);
const char *tg_user_first_name(const tg_user_t *u);
const char *tg_user_last_name (const tg_user_t *u);
const char *tg_user_username  (const tg_user_t *u);
int         tg_user_is_bot    (const tg_user_t *u);

/* ── memory ──────────────────────────────────────────────────────────────── */

void tg_free(char *ptr);

#ifdef __cplusplus
}
#endif

#endif /* TG_H */
