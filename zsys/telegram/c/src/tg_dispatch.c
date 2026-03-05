/*
 * tg_dispatch.c  —  route TDLib JSON events to registered handlers.
 */

#include "tg_internal.h"
#include <string.h>

/* ── _tg_send_pending implementation ────────────────────────────────────── */

int64_t _tg_send_pending(tg_client_t *c, const char *json,
                          tg_result_fn cb, void *ud)
{
    pthread_mutex_lock(&c->pending_lock);
    int64_t req_id = ++c->next_req_id;
    int slot = -1;
    for (int i = 0; i < TG_MAX_PENDING; i++) {
        if (!c->pending[i].active) { slot = i; break; }
    }
    if (slot < 0) {
        pthread_mutex_unlock(&c->pending_lock);
        return -1;
    }
    c->pending[slot].req_id = req_id;
    c->pending[slot].cb     = cb;
    c->pending[slot].ud     = ud;
    c->pending[slot].active = 1;
    pthread_mutex_unlock(&c->pending_lock);

    /* Inject @extra into JSON (assumes JSON ends with '}') */
    size_t jlen = strlen(json);
    char extra[64];
    int extra_len = snprintf(extra, sizeof(extra),
                             ",\"@extra\":\"%lld\"}", (long long)req_id);
    char *buf = malloc(jlen + (size_t)extra_len + 1);
    if (!buf) return -1;
    /* Copy all but trailing '}' */
    memcpy(buf, json, jlen - 1);
    memcpy(buf + jlen - 1, extra, (size_t)extra_len + 1);
    td_send(c->td_id, buf);
    free(buf);
    return req_id;
}

/* ── parse message JSON → tg_message_t ──────────────────────────────────── */

static tg_chat_type_t _resolve_chat_type(tg_client_t *c, int64_t chat_id)
{
    (void)c;
    if (chat_id > 0)          return TG_CHAT_PRIVATE;
    if (chat_id < -999999999) return TG_CHAT_CHANNEL;
    return TG_CHAT_GROUP;
}

/* Extract first file id from a content object field named "file_id" or from
 * the nested file object.  Returns 0 if not found. */
static int32_t _extract_file_id(const char *content_json)
{
    /* Try direct "file_id" integer (some content types) */
    int64_t fid = _json_int(content_json, "file_id");
    if (fid) return (int32_t)fid;
    /* Try nested photo/video/audio/document/sticker/voice/animation object */
    static const char *nested_keys[] = {
        "photo", "video", "audio", "document", "sticker",
        "voice", "animation", "video_note", NULL
    };
    for (int k = 0; nested_keys[k]; k++) {
        const char *obj = _json_obj(content_json, nested_keys[k]);
        if (obj) {
            /* Try "id" first (file id inside media object) */
            int64_t id = _json_int(obj, "id");
            if (id) return (int32_t)id;
            /* Try nested "file" object */
            const char *file = _json_obj(obj, "file");
            if (file) {
                id = _json_int(file, "id");
                if (id) return (int32_t)id;
            }
        }
    }
    return 0;
}

static void _parse_content(const char *content_json, tg_message_t *m)
{
    char ctype[TG_TYPE_MAX] = {0};
    _json_type(content_json, ctype, sizeof(ctype));

    if (strcmp(ctype, "messageText") == 0) {
        const char *text_obj = _json_obj(content_json, "text");
        if (text_obj)
            _json_str(text_obj, "text", m->text, sizeof(m->text));

    } else if (strcmp(ctype, "messagePhoto") == 0) {
        m->has_photo  = 1;
        m->media_type = TG_MEDIA_PHOTO;
        const char *cap = _json_obj(content_json, "caption");
        if (cap) _json_str(cap, "text", m->caption, sizeof(m->caption));
        m->file_id = _extract_file_id(content_json);

    } else if (strcmp(ctype, "messageVideo") == 0) {
        m->has_video  = 1;
        m->media_type = TG_MEDIA_VIDEO;
        const char *cap = _json_obj(content_json, "caption");
        if (cap) _json_str(cap, "text", m->caption, sizeof(m->caption));
        m->file_id = _extract_file_id(content_json);

    } else if (strcmp(ctype, "messageAudio") == 0) {
        m->has_audio  = 1;
        m->media_type = TG_MEDIA_AUDIO;
        const char *cap = _json_obj(content_json, "caption");
        if (cap) _json_str(cap, "text", m->caption, sizeof(m->caption));
        m->file_id = _extract_file_id(content_json);

    } else if (strcmp(ctype, "messageDocument") == 0) {
        m->has_document = 1;
        m->media_type   = TG_MEDIA_DOCUMENT;
        const char *cap = _json_obj(content_json, "caption");
        if (cap) _json_str(cap, "text", m->caption, sizeof(m->caption));
        m->file_id = _extract_file_id(content_json);

    } else if (strcmp(ctype, "messageSticker") == 0) {
        m->has_sticker = 1;
        m->media_type  = TG_MEDIA_STICKER;
        m->file_id     = _extract_file_id(content_json);

    } else if (strcmp(ctype, "messageVoiceNote") == 0) {
        m->has_voice  = 1;
        m->media_type = TG_MEDIA_VOICE;
        const char *cap = _json_obj(content_json, "caption");
        if (cap) _json_str(cap, "text", m->caption, sizeof(m->caption));
        m->file_id = _extract_file_id(content_json);

    } else if (strcmp(ctype, "messageAnimation") == 0) {
        m->has_animation = 1;
        m->media_type    = TG_MEDIA_ANIMATION;
        const char *cap  = _json_obj(content_json, "caption");
        if (cap) _json_str(cap, "text", m->caption, sizeof(m->caption));
        m->file_id = _extract_file_id(content_json);

    } else if (strcmp(ctype, "messageVideoNote") == 0) {
        m->media_type = TG_MEDIA_VIDEO_NOTE;
        m->file_id    = _extract_file_id(content_json);

    } else if (strcmp(ctype, "messageLocation") == 0) {
        m->has_location = 1;
        m->media_type   = TG_MEDIA_LOCATION;

    } else if (strcmp(ctype, "messageContact") == 0) {
        m->has_contact = 1;
        m->media_type  = TG_MEDIA_CONTACT;

    } else if (strcmp(ctype, "messagePoll") == 0) {
        m->media_type = TG_MEDIA_POLL;

    } else if (strcmp(ctype, "messageDice") == 0) {
        m->media_type = TG_MEDIA_DICE;

    } else if (strcmp(ctype, "messageVenue") == 0) {
        m->media_type = TG_MEDIA_VENUE;
    }
}

static void _parse_sender(const char *sender_json, tg_message_t *m)
{
    char stype[TG_TYPE_MAX] = {0};
    _json_type(sender_json, stype, sizeof(stype));

    if (strcmp(stype, "messageSenderUser") == 0) {
        int64_t uid = _json_int(sender_json, "user_id");
        m->sender_id         = uid;
        m->from_user.id      = uid;
        m->has_from_user     = 1;
    } else if (strcmp(stype, "messageSenderChat") == 0) {
        m->sender_id      = _json_int(sender_json, "chat_id");
        m->sender_chat_id = m->sender_id;
        m->has_from_user  = 0;
    }
}

static int _fill_message(const char *msg_json, tg_message_t *m,
                          tg_client_t *c)
{
    memset(m, 0, sizeof(*m));

    m->id       = _json_int(msg_json, "id");
    m->chat_id  = _json_int(msg_json, "chat_id");
    m->is_out   = _json_bool(msg_json, "is_outgoing");
    m->date     = _json_int(msg_json, "date");
    m->views    = (int32_t)_json_int(msg_json, "interaction_info");
    m->forwards = (int32_t)_json_int(msg_json, "forward_count");

    /* sender */
    const char *sender = _json_obj(msg_json, "sender_id");
    if (sender) _parse_sender(sender, m);
    else        m->sender_id = m->chat_id;

    /* reply_to */
    const char *rto = _json_obj(msg_json, "reply_to");
    if (rto) m->reply_to_id = _json_int(rto, "message_id");

    /* content */
    const char *content = _json_obj(msg_json, "content");
    if (content) _parse_content(content, m);

    m->chat_type          = _resolve_chat_type(c, m->chat_id);
    m->reply_to_message   = NULL; /* fetched on-demand via tg_get_messages */
    return 1;
}

/* ── filter matching ─────────────────────────────────────────────────────── */

int _tg_filter_match(const tg_message_t *m, uint32_t filters)
{
    if (filters == TG_FILTER_NONE || filters == TG_FILTER_ALL) return 1;

    if ((filters & TG_FILTER_OUTGOING)  && !m->is_out)                      return 0;
    if ((filters & TG_FILTER_INCOMING)  && m->is_out)                       return 0;
    if ((filters & TG_FILTER_PRIVATE)   && m->chat_type != TG_CHAT_PRIVATE) return 0;
    if ((filters & TG_FILTER_GROUP)     &&
        m->chat_type != TG_CHAT_GROUP &&
        m->chat_type != TG_CHAT_SUPERGROUP)                                  return 0;
    if ((filters & TG_FILTER_CHANNEL)   && m->chat_type != TG_CHAT_CHANNEL) return 0;
    if ((filters & TG_FILTER_TEXT)      && m->text[0] == '\0')              return 0;
    if ((filters & TG_FILTER_PHOTO)     && !m->has_photo)                   return 0;
    if ((filters & TG_FILTER_VIDEO)     && !m->has_video)                   return 0;
    if ((filters & TG_FILTER_AUDIO)     && !m->has_audio)                   return 0;
    if ((filters & TG_FILTER_DOCUMENT)  && !m->has_document)                return 0;
    if ((filters & TG_FILTER_STICKER)   && !m->has_sticker)                 return 0;
    if ((filters & TG_FILTER_BOT_CMD)   && m->text[0] != '/')               return 0;

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

/* ── dispatch callback query ─────────────────────────────────────────────── */

static void _dispatch_callback_query(tg_client_t *c, const char *json)
{
    int64_t query_id = _json_int(json, "id");
    int64_t from_id  = 0;
    char    data[512] = {0};

    const char *sender = _json_obj(json, "sender_user_id");
    if (sender) from_id = _json_int(sender, "user_id");
    else from_id = _json_int(json, "sender_user_id");

    _json_str(json, "payload", data, sizeof(data));
    if (!data[0]) _json_str(json, "data", data, sizeof(data));

    pthread_mutex_lock(&c->handlers_lock);
    for (int i = 0; i < c->handler_count; i++) {
        tg_handler_t *h = &c->handlers[i];
        if (!h->active || h->type != TG_HTYPE_CALLBACK_QUERY) continue;
        tg_callback_query_fn fn = h->cb_query_fn;
        void *ud = h->userdata;
        pthread_mutex_unlock(&c->handlers_lock);
        fn(c, query_id, from_id, data, ud);
        pthread_mutex_lock(&c->handlers_lock);
    }
    pthread_mutex_unlock(&c->handlers_lock);
}

/* ── dispatch inline query ───────────────────────────────────────────────── */

static void _dispatch_inline_query(tg_client_t *c, const char *json)
{
    int64_t query_id = _json_int(json, "id");
    int64_t from_id  = _json_int(json, "sender_user_id");
    char    query[512]  = {0};
    char    offset[128] = {0};
    _json_str(json, "query",  query,  sizeof(query));
    _json_str(json, "offset", offset, sizeof(offset));

    pthread_mutex_lock(&c->handlers_lock);
    for (int i = 0; i < c->handler_count; i++) {
        tg_handler_t *h = &c->handlers[i];
        if (!h->active || h->type != TG_HTYPE_INLINE_QUERY) continue;
        tg_inline_query_fn fn = h->inline_query_fn;
        void *ud = h->userdata;
        pthread_mutex_unlock(&c->handlers_lock);
        fn(c, query_id, from_id, query, offset, ud);
        pthread_mutex_lock(&c->handlers_lock);
    }
    pthread_mutex_unlock(&c->handlers_lock);
}

/* ── dispatch chat member update ─────────────────────────────────────────── */

static void _dispatch_chat_member(tg_client_t *c, const char *json)
{
    int64_t chat_id = _json_int(json, "chat_id");

    /* Determine if join or left by comparing old/new status */
    const char *new_status = _json_obj(json, "new_chat_member");
    const char *old_status = _json_obj(json, "old_chat_member");

    char new_type[TG_TYPE_MAX] = {0};
    char old_type[TG_TYPE_MAX] = {0};
    if (new_status) {
        const char *ns = _json_obj(new_status, "status");
        if (ns) _json_type(ns, new_type, sizeof(new_type));
    }
    if (old_status) {
        const char *os = _json_obj(old_status, "status");
        if (os) _json_type(os, old_type, sizeof(old_type));
    }

    /* Extract user from member_id */
    struct tg_user user;
    memset(&user, 0, sizeof(user));
    const char *mid = _json_obj(json, "member_id");
    if (mid) user.id = _json_int(mid, "user_id");

    int is_left = (strcmp(new_type, "chatMemberStatusLeft") == 0 ||
                   strcmp(new_type, "chatMemberStatusBanned") == 0);

    pthread_mutex_lock(&c->handlers_lock);
    for (int i = 0; i < c->handler_count; i++) {
        tg_handler_t *h = &c->handlers[i];
        if (!h->active || h->type != TG_HTYPE_CHAT_MEMBER) continue;
        if (h->is_left != is_left) continue;
        tg_member_event_fn fn = h->member_event_fn;
        void *ud = h->userdata;
        pthread_mutex_unlock(&c->handlers_lock);
        fn(c, chat_id, &user, ud);
        pthread_mutex_lock(&c->handlers_lock);
    }
    pthread_mutex_unlock(&c->handlers_lock);
}

/* ── main dispatch entry point ───────────────────────────────────────────── */

void _tg_dispatch(tg_client_t *c, const char *json)
{
    char type[TG_TYPE_MAX] = {0};
    _json_type(json, type, sizeof(type));

    /* ── error ── */
    if (strcmp(type, "error") == 0) {
        int code = (int)_json_int(json, "code");
        char msg[256] = {0};
        _json_str(json, "message", msg, sizeof(msg));
        fprintf(stderr, "[libtg] ERROR %d: %s\n", code, msg);
        if (c->on_error) c->on_error(c, code, msg, c->auth_ud);
        return;
    }

    /* ── auth ── */
    if (strcmp(type, "updateAuthorizationState") == 0) {
        const char *auth_state = _json_obj(json, "authorization_state");
        if (auth_state) _tg_dispatch_auth(c, auth_state);
        return;
    }

    /* ── pending callbacks — check @extra field ── */
    char extra[128] = {0};
    _json_str(json, "@extra", extra, sizeof(extra));
    if (extra[0] != '\0' && extra[0] != '_') {
        /* Try to parse as numeric req_id */
        char *end;
        int64_t req_id = (int64_t)strtoll(extra, &end, 10);
        if (end != extra && req_id > 0) {
            tg_result_fn cb  = NULL;
            void        *ud  = NULL;
            int          slot = -1;
            pthread_mutex_lock(&c->pending_lock);
            for (int i = 0; i < TG_MAX_PENDING; i++) {
                if (c->pending[i].active && c->pending[i].req_id == req_id) {
                    cb   = c->pending[i].cb;
                    ud   = c->pending[i].ud;
                    slot = i;
                    c->pending[i].active = 0;
                    break;
                }
            }
            pthread_mutex_unlock(&c->pending_lock);
            if (cb) cb(c, json, ud);
            if (slot >= 0) return;  /* consumed */
        }
    }

    /* ── getMe response ── */
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
        const char *content = _json_obj(json, "new_content");
        if (content) {
            tg_message_t msg;
            memset(&msg, 0, sizeof(msg));
            msg.id       = _json_int(json, "message_id");
            msg.chat_id  = _json_int(json, "chat_id");
            msg.chat_type = _resolve_chat_type(c, msg.chat_id);
            _parse_content(content, &msg);
            _tg_dispatch_message(c, json, 1);
        }
        return;
    }

    /* ── callback query (bot) ── */
    if (strcmp(type, "updateNewCallbackQuery") == 0) {
        _dispatch_callback_query(c, json);
        return;
    }

    /* ── inline query (bot) ── */
    if (strcmp(type, "updateNewInlineQuery") == 0) {
        _dispatch_inline_query(c, json);
        return;
    }

    /* ── chat member update ── */
    if (strcmp(type, "updateChatMember") == 0) {
        _dispatch_chat_member(c, json);
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
