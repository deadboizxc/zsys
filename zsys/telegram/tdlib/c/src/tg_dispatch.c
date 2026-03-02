/*
 * tg_dispatch.c  —  route TDLib JSON events to registered handlers.
 */

#include "tg_internal.h"
#include <string.h>

/* ── parse message JSON → tg_message_t ──────────────────────────────────── */

static tg_chat_type_t _resolve_chat_type(tg_client_t *c, int64_t chat_id)
{
    /* Heuristic: channels have large negative IDs starting with -100.
     * For full accuracy a chat cache is needed (future improvement). */
    if (chat_id > 0)         return TG_CHAT_PRIVATE;
    if (chat_id < -999999999) return TG_CHAT_CHANNEL;
    return TG_CHAT_GROUP;
}

static void _parse_content(const char *content_json, tg_message_t *m)
{
    char ctype[TG_TYPE_MAX] = {0};
    _json_type(content_json, ctype, sizeof(ctype));

    if (strcmp(ctype, "messageText") == 0) {
        /* "text": {"text": "..."} */
        const char *text_obj = _json_obj(content_json, "text");
        if (text_obj)
            _json_str(text_obj, "text", m->text, sizeof(m->text));

    } else if (strcmp(ctype, "messagePhoto") == 0) {
        m->has_photo = 1;
        _json_str(content_json, "caption", m->text, sizeof(m->text));

    } else if (strcmp(ctype, "messageVideo") == 0) {
        m->has_video = 1;
        _json_str(content_json, "caption", m->text, sizeof(m->text));

    } else if (strcmp(ctype, "messageAudio") == 0) {
        m->has_audio = 1;
        _json_str(content_json, "caption", m->text, sizeof(m->text));

    } else if (strcmp(ctype, "messageDocument") == 0) {
        m->has_document = 1;
        _json_str(content_json, "caption", m->text, sizeof(m->text));

    } else if (strcmp(ctype, "messageSticker") == 0) {
        m->has_sticker = 1;
    }
}

static void _parse_sender(const char *sender_json, tg_message_t *m)
{
    char stype[TG_TYPE_MAX] = {0};
    _json_type(sender_json, stype, sizeof(stype));

    if (strcmp(stype, "messageSenderUser") == 0) {
        m->sender_id = _json_int(sender_json, "user_id");
    } else if (strcmp(stype, "messageSenderChat") == 0) {
        m->sender_id = _json_int(sender_json, "chat_id");
    }
}

static int _fill_message(const char *msg_json, tg_message_t *m,
                          tg_client_t *c)
{
    memset(m, 0, sizeof(*m));

    m->id      = _json_int(msg_json, "id");
    m->chat_id = _json_int(msg_json, "chat_id");
    m->is_out  = _json_bool(msg_json, "is_outgoing");

    /* sender */
    const char *sender = _json_obj(msg_json, "sender_id");
    if (sender) _parse_sender(sender, m);
    else        m->sender_id = m->chat_id;   /* old API fallback */

    /* reply_to */
    const char *rto = _json_obj(msg_json, "reply_to");
    if (rto) m->reply_to_id = _json_int(rto, "message_id");

    /* content */
    const char *content = _json_obj(msg_json, "content");
    if (content) _parse_content(content, m);

    m->chat_type = _resolve_chat_type(c, m->chat_id);
    return 1;
}

/* ── filter matching ─────────────────────────────────────────────────────── */

int _tg_filter_match(const tg_message_t *m, uint32_t filters)
{
    if (filters == TG_FILTER_NONE || filters == TG_FILTER_ALL) return 1;

    if ((filters & TG_FILTER_OUTGOING)  && !m->is_out)                   return 0;
    if ((filters & TG_FILTER_INCOMING)  && m->is_out)                    return 0;
    if ((filters & TG_FILTER_PRIVATE)   && m->chat_type != TG_CHAT_PRIVATE) return 0;
    if ((filters & TG_FILTER_GROUP)     &&
        m->chat_type != TG_CHAT_GROUP &&
        m->chat_type != TG_CHAT_SUPERGROUP)                               return 0;
    if ((filters & TG_FILTER_CHANNEL)   && m->chat_type != TG_CHAT_CHANNEL) return 0;
    if ((filters & TG_FILTER_TEXT)      && m->text[0] == '\0')            return 0;
    if ((filters & TG_FILTER_PHOTO)     && !m->has_photo)                 return 0;
    if ((filters & TG_FILTER_VIDEO)     && !m->has_video)                 return 0;
    if ((filters & TG_FILTER_AUDIO)     && !m->has_audio)                 return 0;
    if ((filters & TG_FILTER_DOCUMENT)  && !m->has_document)              return 0;
    if ((filters & TG_FILTER_STICKER)   && !m->has_sticker)               return 0;
    if ((filters & TG_FILTER_BOT_CMD)   && m->text[0] != '/')             return 0;

    return 1;
}

/* ── handler dispatch ────────────────────────────────────────────────────── */

void _tg_dispatch_message(tg_client_t *c, const char *msg_json, int edited)
{
    tg_message_t msg;
    if (!_fill_message(msg_json, &msg, c)) return;

    tg_htype_t want = edited ? TG_HTYPE_EDITED : TG_HTYPE_MESSAGE;

    pthread_mutex_lock(&c->handlers_lock);
    for (int i = 0; i < c->handler_count; i++) {
        tg_handler_t *h = &c->handlers[i];
        if (!h->active || h->type != want) continue;
        if (!_tg_filter_match(&msg, h->filters)) continue;
        tg_message_fn fn = h->msg_fn;
        void *ud         = h->userdata;
        pthread_mutex_unlock(&c->handlers_lock);
        fn(c, &msg, ud);
        pthread_mutex_lock(&c->handlers_lock);
    }
    pthread_mutex_unlock(&c->handlers_lock);
}

/* ── handle getMe response ───────────────────────────────────────────────── */

static void _handle_get_me(tg_client_t *c, const char *json)
{
    struct tg_user *me = &c->me;
    me->id      = _json_int (json, "id");
    me->is_bot  = _json_bool(json, "is_bot");
    _json_str(json, "first_name", me->first_name, sizeof(me->first_name));
    _json_str(json, "last_name",  me->last_name,  sizeof(me->last_name));
    _json_str(json, "username",   me->username,   sizeof(me->username));
    c->me_loaded = 1;
}

/* ── main dispatch entry point ───────────────────────────────────────────── */

void _tg_dispatch(tg_client_t *c, const char *json)
{
    char type[TG_TYPE_MAX] = {0};
    _json_type(json, type, sizeof(type));

    /* ── auth ── */
    if (strcmp(type, "updateAuthorizationState") == 0) {
        const char *auth_state = _json_obj(json, "authorization_state");
        if (auth_state) _tg_dispatch_auth(c, auth_state);
        return;
    }

    /* ── getMe response ── */
    char extra[128] = {0};
    _json_str(json, "@extra", extra, sizeof(extra));
    if (strcmp(extra, "__tg_get_me__") == 0 && strcmp(type, "user") == 0) {
        _handle_get_me(c, json);
        return;
    }

    /* ── new message ── */
    if (strcmp(type, "updateNewMessage") == 0) {
        const char *msg = _json_obj(json, "message");
        if (msg) _tg_dispatch_message(c, msg, 0);
        return;
    }

    /* ── edited message ── */
    if (strcmp(type, "updateMessageContent") == 0 ||
        strcmp(type, "updateMessageEdited")  == 0) {
        /* For updateMessageContent we rebuild a minimal message */
        const char *content = _json_obj(json, "new_content");
        if (content) {
            /* Dispatch a synthetic message with available fields */
            tg_message_t msg;
            memset(&msg, 0, sizeof(msg));
            msg.id      = _json_int(json, "message_id");
            msg.chat_id = _json_int(json, "chat_id");
            msg.chat_type = _resolve_chat_type(c, msg.chat_id);
            _parse_content(content, &msg);
            _tg_dispatch_message(c, json, 1);
        }
        return;
    }

    /* ── raw handlers ── */
    pthread_mutex_lock(&c->handlers_lock);
    for (int i = 0; i < c->handler_count; i++) {
        tg_handler_t *h = &c->handlers[i];
        if (!h->active || h->type != TG_HTYPE_RAW) continue;
        if (h->raw_update_type[0] != '\0' &&
            strcmp(h->raw_update_type, type) != 0) continue;
        tg_raw_fn fn = h->raw_fn;
        void *ud     = h->userdata;
        pthread_mutex_unlock(&c->handlers_lock);
        fn(c, json, ud);
        pthread_mutex_lock(&c->handlers_lock);
    }
    pthread_mutex_unlock(&c->handlers_lock);
}
