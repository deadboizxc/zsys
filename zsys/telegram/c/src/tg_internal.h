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

#define TG_MAX_CLIENTS      16
#define TG_MAX_HANDLERS    256
#define TG_MAX_PENDING     512
#define TG_MAX_CHAT_CACHE  256
#define TG_TEXT_MAX       4096
#define TG_PATH_MAX        512
#define TG_NAME_MAX        256
#define TG_TYPE_MAX        128

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

/* ── pending async requests ──────────────────────────────────────────────── */

typedef struct {
    int64_t      req_id;
    tg_result_fn cb;
    void        *ud;
    int          active;
} tg_pending_t;

/* ── handler types ───────────────────────────────────────────────────────── */

typedef enum {
    TG_HTYPE_MESSAGE = 0,
    TG_HTYPE_EDITED,
    TG_HTYPE_RAW,
    TG_HTYPE_CALLBACK_QUERY,
    TG_HTYPE_INLINE_QUERY,
    TG_HTYPE_CHAT_MEMBER,
} tg_htype_t;

typedef struct {
    tg_handler_id_t      id;
    tg_htype_t           type;
    uint32_t             filters;
    union {
        tg_message_fn        msg_fn;
        tg_raw_fn            raw_fn;
        tg_callback_query_fn cb_query_fn;
        tg_inline_query_fn   inline_query_fn;
        tg_member_event_fn   member_event_fn;
    };
    char  raw_update_type[TG_TYPE_MAX];  /* empty = all updates */
    void *userdata;
    int   active;
    int   is_left;   /* for CHAT_MEMBER handlers: 0 = join, 1 = left */
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

/* ── struct tg_chat (public, defined here) ───────────────────────────────── */

struct tg_chat {
    int64_t        id;
    char           title[TG_NAME_MAX];
    char           username[TG_NAME_MAX];
    tg_chat_type_t type;
    int32_t        members_count;
    int64_t        linked_chat_id;
    int            is_verified;
    int            is_restricted;
    int            is_scam;
    uint32_t       permissions; /* TG_PERM_* bitmask */
};

/* ── tg_chat_member_t (public, defined here) ─────────────────────────────── */

struct tg_chat_member {
    struct tg_user user;
    char    status[64]; /* "member","administrator","creator","restricted","left","banned" */
    int     is_admin;
    int     is_creator;
    int32_t until_date; /* for restricted/banned */
    /* admin rights */
    int can_manage_chat;
    int can_post_messages;
    int can_edit_messages;
    int can_delete_messages;
    int can_ban_users;
    int can_invite_users;
    int can_pin_messages;
    int can_promote_members;
    int can_change_info;
};

/* ── tg_file_t (public, defined here) ────────────────────────────────────── */

struct tg_file {
    int32_t id;
    int64_t size;
    char    local_path[TG_PATH_MAX];
    int     is_downloading;
    int     is_downloaded;
    char    mime_type[128];
    char    file_name[TG_NAME_MAX];
};

/* ── tg_location_t ───────────────────────────────────────────────────────── */

typedef struct { double lat; double lon; double accuracy; } tg_location_t;

/* ── tg_contact_t ────────────────────────────────────────────────────────── */

typedef struct {
    char    phone[64];
    char    first_name[TG_NAME_MAX];
    char    last_name[TG_NAME_MAX];
    int64_t user_id;
} tg_contact_t;

/* ── struct tg_message (public, defined here) ────────────────────────────── */

struct tg_message {
    int64_t          id;
    int64_t          chat_id;
    int64_t          sender_id;      /* user_id or chat_id of sender */
    char             text[TG_TEXT_MAX];
    char             caption[TG_TEXT_MAX];
    int              is_out;
    int64_t          reply_to_id;
    tg_chat_type_t   chat_type;
    /* sender details */
    struct tg_user   from_user;      /* filled when sender is a user */
    int              has_from_user;  /* 1 if from_user is populated */
    int64_t          sender_chat_id; /* sender chat id (channel posts) */
    /* reply reference — NULL unless explicitly fetched */
    struct tg_message *reply_to_message;
    /* media */
    tg_media_type_t  media_type;
    int              has_photo;
    int              has_video;
    int              has_audio;
    int              has_document;
    int              has_sticker;
    int              has_voice;
    int              has_animation;
    int              has_location;
    int              has_contact;
    int32_t          file_id;
    /* metadata */
    int64_t          date;
    int32_t          views;
    int32_t          forwards;
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

    /* pending async requests — callback-based.
     * pending_lock is zero-initialized by calloc which is safe on Linux. */
    tg_pending_t     pending[TG_MAX_PENDING];
    pthread_mutex_t  pending_lock;

    /* chat cache — zero-initialized by calloc */
    struct tg_chat   chat_cache[TG_MAX_CHAT_CACHE];
    int              chat_cache_count;
    pthread_mutex_t  chat_cache_lock;
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

int         _json_type  (const char *json, char *buf, size_t sz);
int64_t     _json_int   (const char *json, const char *key);
int         _json_str   (const char *json, const char *key, char *buf, size_t sz);
int         _json_bool  (const char *json, const char *key);
const char *_json_obj   (const char *json, const char *key);

/* ── request builders ────────────────────────────────────────────────────── */

int64_t _tg_send_raw(tg_client_t *c, const char *json);
int64_t _tg_send_fmt(tg_client_t *c, const char *fmt, ...);

/* Injects "@extra":"<req_id>", stores pending callback, sends. Returns req_id or -1. */
int64_t _tg_send_pending(tg_client_t *c, const char *json,
                          tg_result_fn cb, void *ud);

/* ── filter evaluation ───────────────────────────────────────────────────── */

int _tg_filter_match(const tg_message_t *msg, uint32_t filters);

/* ── parsing helpers (implemented in tg_user.c / tg_chat.c) ─────────────── */

void _parse_user_json  (const char *json, tg_user_t *out);
void _parse_chat_json  (const char *json, tg_chat_t *out);
void _parse_member_json(const char *json, tg_chat_member_t *out);
void _parse_file_json  (const char *json, tg_file_t *out);

/* ── permissions helpers (implemented in tg_admin.c) ────────────────────── */

uint32_t _perms_json_to_bitmask(const char *perms_json);
void     _perms_bitmask_to_json(uint32_t perms, char *buf, size_t sz);
void     _admin_rights_to_json (uint32_t rights, char *buf, size_t sz);

#endif /* TG_INTERNAL_H */
