/*
 * tg_chat.c  —  chat getters, management, accessors.
 */

#include "tg_internal.h"
#include <string.h>
#include <stdlib.h>

/* ── parsing helpers ─────────────────────────────────────────────────────── */

void _parse_chat_json(const char *json, tg_chat_t *out)
{
    memset(out, 0, sizeof(*out));
    out->id = _json_int(json, "id");
    _json_str(json, "title",    out->title,    sizeof(out->title));
    _json_str(json, "username", out->username, sizeof(out->username));

    /* type */
    const char *type_obj = _json_obj(json, "type");
    if (type_obj) {
        char tname[TG_TYPE_MAX] = {0};
        _json_type(type_obj, tname, sizeof(tname));
        if (strcmp(tname, "chatTypePrivate") == 0)
            out->type = TG_CHAT_PRIVATE;
        else if (strcmp(tname, "chatTypeBasicGroup") == 0)
            out->type = TG_CHAT_GROUP;
        else if (strcmp(tname, "chatTypeSupergroup") == 0) {
            out->type = _json_bool(type_obj, "is_channel")
                      ? TG_CHAT_CHANNEL : TG_CHAT_SUPERGROUP;
        } else if (strcmp(tname, "chatTypeSecret") == 0)
            out->type = TG_CHAT_PRIVATE;
    }

    out->linked_chat_id = _json_int(json, "linked_chat_id");
    out->is_verified    = _json_bool(json, "is_verified");
    out->is_restricted  = _json_bool(json, "is_restricted");
    out->is_scam        = _json_bool(json, "is_scam");

    /* permissions */
    const char *perms = _json_obj(json, "permissions");
    if (perms) out->permissions = _perms_json_to_bitmask(perms);
}

/* ── pending request wrappers ────────────────────────────────────────────── */

typedef struct { tg_chat_cb_fn    cb; void *ud; } _chat_req_t;
typedef struct { tg_messages_cb_fn cb; void *ud; } _history_req_t;
typedef struct { tg_dialogs_cb_fn cb; void *ud; } _dialogs_req_t;
typedef struct { tg_messages_cb_fn cb; void *ud; } _msgs_req_t;

static void _on_get_chat(tg_client_t *c, const char *json, void *ud)
{
    _chat_req_t *req = ud;
    char type[TG_TYPE_MAX] = {0};
    _json_type(json, type, sizeof(type));
    if (strcmp(type, "chat") == 0) {
        tg_chat_t chat;
        _parse_chat_json(json, &chat);
        if (req->cb) req->cb(c, &chat, req->ud);
    }
    free(req);
}

static void _on_get_history(tg_client_t *c, const char *json, void *ud)
{
    _history_req_t *req = ud;
    char type[TG_TYPE_MAX] = {0};
    _json_type(json, type, sizeof(type));
    if (strcmp(type, "messages") == 0) {
        int32_t total = (int32_t)_json_int(json, "total_count");
        if (total <= 0) {
            if (req->cb) req->cb(c, NULL, 0, req->ud);
            free(req);
            return;
        }
        /* Parse messages array — allocate on heap for callback */
        tg_message_t *msgs = calloc((size_t)total, sizeof(tg_message_t));
        if (!msgs) { free(req); return; }
        /* Iterate JSON array — simplified parser */
        const char *p = strstr(json, "\"messages\":[");
        int count = 0;
        if (p) {
            p += strlen("\"messages\":[");
            while (*p && *p != ']' && count < total) {
                if (*p == '{') {
                    /* Find end of this object */
                    int depth = 0;
                    const char *start = p;
                    while (*p) {
                        if (*p == '{') depth++;
                        else if (*p == '}') { depth--; if (!depth) { p++; break; } }
                        p++;
                    }
                    /* Parse this message (zero-length is fine) */
                    size_t mlen = (size_t)(p - start);
                    char *mbuf  = malloc(mlen + 1);
                    if (mbuf) {
                        memcpy(mbuf, start, mlen);
                        mbuf[mlen] = '\0';
                        tg_message_t *m = &msgs[count];
                        memset(m, 0, sizeof(*m));
                        m->id      = _json_int(mbuf, "id");
                        m->chat_id = _json_int(mbuf, "chat_id");
                        m->is_out  = _json_bool(mbuf, "is_outgoing");
                        m->date    = _json_int(mbuf, "date");
                        const char *content = _json_obj(mbuf, "content");
                        if (content) {
                            char ctype[TG_TYPE_MAX] = {0};
                            _json_type(content, ctype, sizeof(ctype));
                            if (strcmp(ctype, "messageText") == 0) {
                                const char *to = _json_obj(content, "text");
                                if (to) _json_str(to, "text", m->text, sizeof(m->text));
                            }
                        }
                        free(mbuf);
                        count++;
                    }
                } else p++;
            }
        }
        if (req->cb) req->cb(c, msgs, count, req->ud);
        free(msgs);
    }
    free(req);
}

static void _on_get_chats(tg_client_t *c, const char *json, void *ud)
{
    _dialogs_req_t *req = ud;
    char type[TG_TYPE_MAX] = {0};
    _json_type(json, type, sizeof(type));
    if (strcmp(type, "chats") == 0) {
        int64_t total = _json_int(json, "total_count");
        if (total <= 0) {
            if (req->cb) req->cb(c, NULL, 0, req->ud);
            free(req); return;
        }
        int64_t *ids = calloc((size_t)total, sizeof(int64_t));
        if (!ids) { free(req); return; }
        /* Parse chat_ids array */
        const char *p = strstr(json, "\"chat_ids\":[");
        int count = 0;
        if (p) {
            p += strlen("\"chat_ids\":[");
            while (*p && *p != ']' && count < (int)total) {
                char *end;
                int64_t id = strtoll(p, &end, 10);
                if (end == p) { p++; continue; }
                ids[count++] = id;
                p = end;
                if (*p == ',') p++;
            }
        }
        if (req->cb) req->cb(c, ids, count, req->ud);
        free(ids);
    }
    free(req);
}

static void _on_invite_link(tg_client_t *c, const char *json, void *ud)
{
    /* ud is a heap-allocated struct with raw_fn + void* */
    typedef struct { tg_raw_fn fn; void *ud; } _raw_req_t;
    _raw_req_t *r = ud;
    if (r->fn) r->fn(c, json, r->ud);
    free(r);
}

/* ── async getters ───────────────────────────────────────────────────────── */

int tg_get_chat(tg_client_t *c, int64_t chat_id, tg_chat_cb_fn cb, void *ud)
{
    _chat_req_t *req = malloc(sizeof(*req));
    if (!req) return -1;
    req->cb = cb; req->ud = ud;
    char json[128];
    snprintf(json, sizeof(json),
             "{\"@type\":\"getChat\",\"chat_id\":%lld}", (long long)chat_id);
    return (int)_tg_send_pending(c, json, _on_get_chat, req);
}

int tg_get_history(tg_client_t *c, int64_t chat_id, int64_t from_msg_id,
                   int limit, tg_messages_cb_fn cb, void *ud)
{
    _history_req_t *req = malloc(sizeof(*req));
    if (!req) return -1;
    req->cb = cb; req->ud = ud;
    char json[256];
    snprintf(json, sizeof(json),
             "{\"@type\":\"getChatHistory\","
             "\"chat_id\":%lld,"
             "\"from_message_id\":%lld,"
             "\"offset\":0,"
             "\"limit\":%d,"
             "\"only_local\":false}",
             (long long)chat_id, (long long)from_msg_id, limit);
    return (int)_tg_send_pending(c, json, _on_get_history, req);
}

int tg_get_dialogs(tg_client_t *c, int limit, tg_dialogs_cb_fn cb, void *ud)
{
    _dialogs_req_t *req = malloc(sizeof(*req));
    if (!req) return -1;
    req->cb = cb; req->ud = ud;
    /* First load chats, then get their IDs */
    char json[256];
    snprintf(json, sizeof(json),
             "{\"@type\":\"getChats\","
             "\"chat_list\":{\"@type\":\"chatListMain\"},"
             "\"limit\":%d}", limit);
    return (int)_tg_send_pending(c, json, _on_get_chats, req);
}

int tg_search_public_chat(tg_client_t *c, const char *username,
                           tg_chat_cb_fn cb, void *ud)
{
    _chat_req_t *req = malloc(sizeof(*req));
    if (!req) return -1;
    req->cb = cb; req->ud = ud;
    char json[TG_NAME_MAX + 64];
    snprintf(json, sizeof(json),
             "{\"@type\":\"searchPublicChat\",\"username\":\"%s\"}", username);
    return (int)_tg_send_pending(c, json, _on_get_chat, req);
}

/* ── chat management ─────────────────────────────────────────────────────── */

int tg_join_chat(tg_client_t *c, int64_t chat_id)
{
    char buf[128];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"joinChat\",\"chat_id\":%lld}", (long long)chat_id);
    return (int)_tg_send_raw(c, buf);
}

int tg_join_by_link(tg_client_t *c, const char *invite_link)
{
    char buf[512];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"joinChatByInviteLink\","
             "\"invite_link\":\"%s\"}", invite_link);
    return (int)_tg_send_raw(c, buf);
}

int tg_leave_chat(tg_client_t *c, int64_t chat_id)
{
    char buf[128];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"leaveChat\",\"chat_id\":%lld}", (long long)chat_id);
    return (int)_tg_send_raw(c, buf);
}

int tg_set_chat_title(tg_client_t *c, int64_t chat_id, const char *title)
{
    char buf[TG_NAME_MAX + 128];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"setChatTitle\","
             "\"chat_id\":%lld,\"title\":\"%s\"}",
             (long long)chat_id, title);
    return (int)_tg_send_raw(c, buf);
}

int tg_set_chat_description(tg_client_t *c, int64_t chat_id, const char *desc)
{
    char buf[TG_TEXT_MAX + 128];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"setChatDescription\","
             "\"chat_id\":%lld,\"description\":\"%s\"}",
             (long long)chat_id, desc ? desc : "");
    return (int)_tg_send_raw(c, buf);
}

int tg_set_chat_photo(tg_client_t *c, int64_t chat_id, const char *path)
{
    char buf[TG_PATH_MAX + 256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"setChatPhoto\","
             "\"chat_id\":%lld,"
             "\"photo\":{\"@type\":\"inputChatPhotoLocal\","
             "\"photo\":{\"@type\":\"inputFileLocal\",\"path\":\"%s\"}}}",
             (long long)chat_id, path);
    return (int)_tg_send_raw(c, buf);
}

int tg_delete_chat_photo(tg_client_t *c, int64_t chat_id)
{
    char buf[128];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"setChatPhoto\","
             "\"chat_id\":%lld,\"photo\":null}", (long long)chat_id);
    return (int)_tg_send_raw(c, buf);
}

int tg_archive_chat(tg_client_t *c, int64_t chat_id)
{
    char buf[256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"addChatToList\","
             "\"chat_id\":%lld,"
             "\"chat_list\":{\"@type\":\"chatListArchive\"}}",
             (long long)chat_id);
    return (int)_tg_send_raw(c, buf);
}

int tg_unarchive_chat(tg_client_t *c, int64_t chat_id)
{
    char buf[256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"addChatToList\","
             "\"chat_id\":%lld,"
             "\"chat_list\":{\"@type\":\"chatListMain\"}}",
             (long long)chat_id);
    return (int)_tg_send_raw(c, buf);
}

int tg_mute_chat(tg_client_t *c, int64_t chat_id, int mute_for_seconds)
{
    char buf[256];
    if (mute_for_seconds == 0) {
        /* unmute: use_default_mute_for=true */
        snprintf(buf, sizeof(buf),
                 "{\"@type\":\"setChatNotificationSettings\","
                 "\"chat_id\":%lld,"
                 "\"notification_settings\":{"
                 "\"@type\":\"chatNotificationSettings\","
                 "\"use_default_mute_for\":true}}",
                 (long long)chat_id);
    } else {
        snprintf(buf, sizeof(buf),
                 "{\"@type\":\"setChatNotificationSettings\","
                 "\"chat_id\":%lld,"
                 "\"notification_settings\":{"
                 "\"@type\":\"chatNotificationSettings\","
                 "\"use_default_mute_for\":false,"
                 "\"mute_for\":%d}}",
                 (long long)chat_id, mute_for_seconds);
    }
    return (int)_tg_send_raw(c, buf);
}

int tg_get_invite_link(tg_client_t *c, int64_t chat_id, tg_raw_fn cb, void *ud)
{
    typedef struct { tg_raw_fn fn; void *ud; } _raw_req_t;
    _raw_req_t *req = malloc(sizeof(*req));
    if (!req) return -1;
    req->fn = cb; req->ud = ud;
    char json[128];
    snprintf(json, sizeof(json),
             "{\"@type\":\"createChatInviteLink\","
             "\"chat_id\":%lld}", (long long)chat_id);
    return (int)_tg_send_pending(c, json, _on_invite_link, req);
}

/* ── chat accessors ──────────────────────────────────────────────────────── */

int64_t     tg_chat_id(const tg_chat_t *ch)             { return ch->id; }
const char *tg_chat_title(const tg_chat_t *ch)          { return ch->title; }
const char *tg_chat_username(const tg_chat_t *ch)       { return ch->username; }
int         tg_chat_type(const tg_chat_t *ch)           { return (int)ch->type; }
int32_t     tg_chat_members_count(const tg_chat_t *ch)  { return ch->members_count; }
int64_t     tg_chat_linked_chat_id(const tg_chat_t *ch) { return ch->linked_chat_id; }
uint32_t    tg_chat_permissions(const tg_chat_t *ch)    { return ch->permissions; }
