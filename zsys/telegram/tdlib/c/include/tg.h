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
#define TG_VERSION_MINOR  1
#define TG_VERSION_PATCH  0

/* ── opaque types ────────────────────────────────────────────────────────── */

typedef struct tg_client   tg_client_t;
typedef struct tg_message  tg_message_t;
typedef struct tg_user     tg_user_t;
typedef struct tg_chat     tg_chat_t;
typedef int32_t            tg_handler_id_t;

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

/* Allocate config with sensible defaults. Fill api_id / api_hash then pass to tg_client_new(). */
tg_config_t *tg_config_new(int32_t api_id, const char *api_hash);
void         tg_config_free(tg_config_t *cfg);

/* ── auth callbacks ──────────────────────────────────────────────────────── */

typedef void (*tg_ask_phone_fn)(tg_client_t *c, void *ud);
typedef void (*tg_ask_code_fn) (tg_client_t *c, void *ud);
typedef void (*tg_ask_pass_fn) (tg_client_t *c, void *ud);
typedef void (*tg_ready_fn)    (tg_client_t *c, void *ud);
typedef void (*tg_error_fn)    (tg_client_t *c, int code, const char *msg, void *ud);
typedef void (*tg_progress_fn) (int32_t file_id, int64_t done, int64_t total, void *ud);

/* ── lifecycle ───────────────────────────────────────────────────────────── */

/* Create a new client. Deep-copies cfg. Returns NULL on OOM. */
tg_client_t *tg_client_new(const tg_config_t *cfg);

/* Free client and all its resources. Must call tg_client_stop() first. */
void         tg_client_free(tg_client_t *c);

/* Register auth callbacks before tg_client_start(). All may be NULL. */
void tg_client_set_auth_handlers(
    tg_client_t    *c,
    tg_ask_phone_fn ask_phone,
    tg_ask_code_fn  ask_code,
    tg_ask_pass_fn  ask_pass,
    tg_ready_fn     on_ready,
    tg_error_fn     on_error,
    void           *userdata
);

/* Start the client (non-blocking). Spawns polling + auth threads.
 * Returns 0 on success, -1 on error. */
int  tg_client_start(tg_client_t *c);

/* Stop the client gracefully. Safe to call from any thread. */
void tg_client_stop(tg_client_t *c);

/* Block the calling thread until the client stops (use in main). */
void tg_client_run(tg_client_t *c);

/* Block until authorized or timeout_sec elapsed. Returns 0=ready, -1=timeout/error. */
int  tg_client_wait_ready(tg_client_t *c, int timeout_sec);

/* Supply auth data in response to ask_phone / ask_code / ask_pass callbacks. */
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

/* ── event handlers ──────────────────────────────────────────────────────── */

typedef void (*tg_message_fn)(tg_client_t *c, const tg_message_t *msg, void *ud);
typedef void (*tg_raw_fn)    (tg_client_t *c, const char *json,         void *ud);

/* Register handler for new messages matching filters. Returns handler ID. */
tg_handler_id_t tg_on_message(tg_client_t *c, uint32_t filters,
                               tg_message_fn fn, void *ud);

/* Register handler for edited messages matching filters. */
tg_handler_id_t tg_on_edited (tg_client_t *c, uint32_t filters,
                               tg_message_fn fn, void *ud);

/* Register handler for raw TDLib update_type (e.g. "updateDeleteMessages").
 * update_type may be NULL to receive every raw update. */
tg_handler_id_t tg_on_raw    (tg_client_t *c, const char *update_type,
                               tg_raw_fn fn, void *ud);

/* Unregister a handler by its ID. */
void tg_remove_handler(tg_client_t *c, tg_handler_id_t hid);

/* ── message accessors ───────────────────────────────────────────────────── */
/* Valid ONLY inside the handler callback. Do not store the pointer. */

int64_t     tg_msg_id         (const tg_message_t *m);
int64_t     tg_msg_chat_id    (const tg_message_t *m);
int64_t     tg_msg_sender_id  (const tg_message_t *m);
const char *tg_msg_text       (const tg_message_t *m);  /* NULL if not text */
int         tg_msg_is_out     (const tg_message_t *m);
int64_t     tg_msg_reply_to   (const tg_message_t *m);
int         tg_msg_is_private (const tg_message_t *m);
int         tg_msg_is_group   (const tg_message_t *m);
int         tg_msg_is_channel (const tg_message_t *m);

/* ── actions ─────────────────────────────────────────────────────────────── */
/* parse_mode: "html" | "md" | NULL (plain text). */

int tg_send_text  (tg_client_t *c, int64_t chat_id,
                   const char *text,       const char *parse_mode);
int tg_send_photo (tg_client_t *c, int64_t chat_id,
                   const char *path,       const char *caption);
int tg_send_video (tg_client_t *c, int64_t chat_id,
                   const char *path,       const char *caption);
int tg_send_audio (tg_client_t *c, int64_t chat_id,
                   const char *path,       const char *caption);
int tg_send_doc   (tg_client_t *c, int64_t chat_id,
                   const char *path,       const char *caption);

int tg_reply_text (tg_client_t *c, const tg_message_t *orig,
                   const char *text,       const char *parse_mode);
int tg_edit_text  (tg_client_t *c, int64_t chat_id, int64_t msg_id,
                   const char *text,       const char *parse_mode);
int tg_delete_msg (tg_client_t *c, int64_t chat_id, int64_t msg_id);
int tg_forward    (tg_client_t *c, int64_t to_chat, int64_t from_chat, int64_t msg_id);
int tg_react      (tg_client_t *c, int64_t chat_id, int64_t msg_id, const char *emoji);

/* Async file download. cb may be NULL. Returns 0 on success. */
int tg_download_file(tg_client_t *c, int32_t file_id,
                     const char *dest_path,
                     tg_progress_fn cb, void *ud);

/* ── self info ───────────────────────────────────────────────────────────── */

int64_t     tg_me_id         (tg_client_t *c);
const char *tg_me_username   (tg_client_t *c);  /* internal ptr, don't free */
const char *tg_me_first_name (tg_client_t *c);  /* internal ptr, don't free */

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
