/*
 * tg_internal.h  —  private implementation types for libtg.
 * NOT part of the public API. Include only from tg_*.c files.
 */

#ifndef TG_INTERNAL_H
#define TG_INTERNAL_H

#include "../include/tg.h"
#include <pthread.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

/* TDLib C JSON API (from <td/telegram/td_json_client.h>) */
extern int          td_create_client_id(void);
extern void         td_send(int client_id, const char *request);
extern const char  *td_receive(double timeout);
extern const char  *td_execute(const char *request);

/* ── limits ──────────────────────────────────────────────────────────────── */

#define TG_MAX_CLIENTS     16
#define TG_MAX_HANDLERS   256
#define TG_TEXT_MAX      4096
#define TG_PATH_MAX       512
#define TG_NAME_MAX       256
#define TG_TYPE_MAX       128

/* ── auth state machine ──────────────────────────────────────────────────── */

typedef enum {
    TG_AUTH_INITIAL = 0,
    TG_AUTH_WAIT_PARAMS,
    TG_AUTH_WAIT_ENCRYPTION_KEY,
    TG_AUTH_WAIT_PHONE,
    TG_AUTH_WAIT_CODE,
    TG_AUTH_WAIT_PASS,
    TG_AUTH_WAIT_REGISTRATION,
    TG_AUTH_READY,
    TG_AUTH_CLOSING,
    TG_AUTH_CLOSED,
    TG_AUTH_ERROR,
} tg_auth_state_t;

/* ── handler ─────────────────────────────────────────────────────────────── */

typedef enum {
    TG_HTYPE_MESSAGE = 0,
    TG_HTYPE_EDITED,
    TG_HTYPE_RAW,
} tg_htype_t;

typedef struct {
    tg_handler_id_t id;
    tg_htype_t      type;
    uint32_t        filters;
    union {
        tg_message_fn msg_fn;
        tg_raw_fn     raw_fn;
    };
    char  raw_update_type[TG_TYPE_MAX];  /* empty = all updates */
    void *userdata;
    int   active;
} tg_handler_t;

/* ── struct tg_user (public, defined here) ───────────────────────────────── */

struct tg_user {
    int64_t id;
    char    first_name[TG_NAME_MAX];
    char    last_name[TG_NAME_MAX];
    char    username[TG_NAME_MAX];
    char    phone[64];
    int     is_bot;
    int     is_premium;
};

/* ── struct tg_message (public, defined here) ────────────────────────────── */

typedef enum {
    TG_CHAT_PRIVATE = 0,
    TG_CHAT_GROUP,
    TG_CHAT_SUPERGROUP,
    TG_CHAT_CHANNEL,
} tg_chat_type_t;

struct tg_message {
    int64_t        id;
    int64_t        chat_id;
    int64_t        sender_id;
    char           text[TG_TEXT_MAX];
    int            is_out;
    int64_t        reply_to_id;
    tg_chat_type_t chat_type;
    /* media */
    int            has_photo;
    int            has_video;
    int            has_audio;
    int            has_document;
    int            has_sticker;
    int32_t        file_id;
};

/* ── struct tg_client (public opaque, defined here) ─────────────────────── */

struct tg_client {
    int              td_id;
    tg_config_t     *config;
    tg_auth_state_t  auth_state;

    /* handlers */
    tg_handler_t     handlers[TG_MAX_HANDLERS];
    int              handler_count;
    int              next_handler_id;
    pthread_mutex_t  handlers_lock;

    /* auth callbacks */
    tg_ask_phone_fn  ask_phone;
    tg_ask_code_fn   ask_code;
    tg_ask_pass_fn   ask_pass;
    tg_ready_fn      on_ready;
    tg_error_fn      on_error;
    void            *auth_ud;

    /* auth sync: tg_client_wait_ready() blocks on auth_cond */
    pthread_mutex_t  auth_lock;
    pthread_cond_t   auth_cond;

    /* self info (filled after getMe response) */
    struct tg_user   me;
    int              me_loaded;

    /* run sync: tg_client_run() blocks here */
    pthread_mutex_t  run_lock;
    pthread_cond_t   run_cond;
    volatile int     running;

    /* monotonic request ID counter */
    volatile int64_t next_req_id;
};

/* ── global client registry ──────────────────────────────────────────────── */

extern tg_client_t     *_tg_clients[TG_MAX_CLIENTS];
extern int              _tg_client_count;
extern pthread_mutex_t  _tg_global_lock;

tg_client_t *_tg_find_client(int td_id);
void         _tg_register_client(tg_client_t *c);
void         _tg_unregister_client(tg_client_t *c);

/* ── internal dispatch ───────────────────────────────────────────────────── */

void _tg_dispatch(tg_client_t *c, const char *json);
void _tg_dispatch_auth(tg_client_t *c, const char *auth_state_json);
void _tg_dispatch_message(tg_client_t *c, const char *msg_json, int edited);

/* ── JSON helpers (no external deps) ────────────────────────────────────── */

/* Extract "@type" value into buf. Returns 1 on success. */
int         _json_type  (const char *json, char *buf, size_t sz);
/* Extract integer field. Returns 0 if not found. */
int64_t     _json_int   (const char *json, const char *key);
/* Extract string field into buf. Returns 1 on success. */
int         _json_str   (const char *json, const char *key, char *buf, size_t sz);
/* Extract boolean field (true/false). Returns 0 if not found. */
int         _json_bool  (const char *json, const char *key);
/* Locate nested object value for key. Returns pointer inside json or NULL. */
const char *_json_obj   (const char *json, const char *key);

/* ── request builder ─────────────────────────────────────────────────────── */

/* Returns new req_id, sends JSON to TDLib. */
int64_t _tg_send_raw(tg_client_t *c, const char *json);

/* Build and send formatted JSON request. Returns req_id. */
int64_t _tg_send_fmt(tg_client_t *c, const char *fmt, ...);

/* ── filter evaluation ───────────────────────────────────────────────────── */

int _tg_filter_match(const tg_message_t *msg, uint32_t filters);

#endif /* TG_INTERNAL_H */
