/*
 * tg_user.c  —  user getters, member queries, block/unblock.
 */

#include "tg_internal.h"
#include <string.h>
#include <stdlib.h>

/* ── parsing helpers ─────────────────────────────────────────────────────── */

void _parse_user_json(const char *json, tg_user_t *out)
{
    memset(out, 0, sizeof(*out));
    out->id         = _json_int(json, "id");
    out->is_bot     = 0;
    out->is_premium = _json_bool(json, "is_premium");
    _json_str(json, "first_name",    out->first_name, sizeof(out->first_name));
    _json_str(json, "last_name",     out->last_name,  sizeof(out->last_name));
    _json_str(json, "username",      out->username,   sizeof(out->username));
    _json_str(json, "phone_number",  out->phone,      sizeof(out->phone));

    const char *utype = _json_obj(json, "type");
    if (utype) {
        char tname[TG_TYPE_MAX] = {0};
        _json_type(utype, tname, sizeof(tname));
        out->is_bot = (strcmp(tname, "userTypeBot") == 0);
    }
}

void _parse_member_json(const char *json, tg_chat_member_t *out)
{
    memset(out, 0, sizeof(*out));

    /* member_id → user */
    const char *mid = _json_obj(json, "member_id");
    if (mid) out->user.id = _json_int(mid, "user_id");

    /* status */
    const char *status_obj = _json_obj(json, "status");
    if (!status_obj) return;

    char stype[TG_TYPE_MAX] = {0};
    _json_type(status_obj, stype, sizeof(stype));

    if (strcmp(stype, "chatMemberStatusMember") == 0) {
        snprintf(out->status, sizeof(out->status), "member");
    } else if (strcmp(stype, "chatMemberStatusCreator") == 0) {
        snprintf(out->status, sizeof(out->status), "creator");
        out->is_creator = 1;
        out->is_admin   = 1;
    } else if (strcmp(stype, "chatMemberStatusAdministrator") == 0) {
        snprintf(out->status, sizeof(out->status), "administrator");
        out->is_admin = 1;
        const char *rights = _json_obj(status_obj, "rights");
        if (rights) {
            out->can_manage_chat     = _json_bool(rights, "can_manage_chat");
            out->can_post_messages   = _json_bool(rights, "can_post_messages");
            out->can_edit_messages   = _json_bool(rights, "can_edit_messages");
            out->can_delete_messages = _json_bool(rights, "can_delete_messages");
            out->can_ban_users       = _json_bool(rights, "can_restrict_members");
            out->can_invite_users    = _json_bool(rights, "can_invite_users");
            out->can_pin_messages    = _json_bool(rights, "can_pin_messages");
            out->can_promote_members = _json_bool(rights, "can_promote_members");
            out->can_change_info     = _json_bool(rights, "can_change_info");
        }
    } else if (strcmp(stype, "chatMemberStatusRestricted") == 0) {
        snprintf(out->status, sizeof(out->status), "restricted");
        out->until_date = (int32_t)_json_int(status_obj, "restricted_until_date");
    } else if (strcmp(stype, "chatMemberStatusLeft") == 0) {
        snprintf(out->status, sizeof(out->status), "left");
    } else if (strcmp(stype, "chatMemberStatusBanned") == 0) {
        snprintf(out->status, sizeof(out->status), "banned");
        out->until_date = (int32_t)_json_int(status_obj, "banned_until_date");
    }
}

/* ── pending request wrappers ────────────────────────────────────────────── */

typedef struct { tg_user_cb_fn    cb; void *ud; } _user_req_t;
typedef struct { tg_member_cb_fn  cb; void *ud; } _member_req_t;
typedef struct { tg_members_cb_fn cb; void *ud; } _members_req_t;

static void _on_get_user(tg_client_t *c, const char *json, void *ud)
{
    _user_req_t *req = ud;
    char type[TG_TYPE_MAX] = {0};
    _json_type(json, type, sizeof(type));
    if (strcmp(type, "user") == 0) {
        tg_user_t user;
        _parse_user_json(json, &user);
        if (req->cb) req->cb(c, &user, req->ud);
    }
    free(req);
}

static void _on_get_member(tg_client_t *c, const char *json, void *ud)
{
    _member_req_t *req = ud;
    char type[TG_TYPE_MAX] = {0};
    _json_type(json, type, sizeof(type));
    if (strcmp(type, "chatMember") == 0) {
        tg_chat_member_t m;
        _parse_member_json(json, &m);
        if (req->cb) req->cb(c, &m, req->ud);
    }
    free(req);
}

static void _on_get_members(tg_client_t *c, const char *json, void *ud)
{
    _members_req_t *req = ud;
    char type[TG_TYPE_MAX] = {0};
    _json_type(json, type, sizeof(type));
    if (strcmp(type, "chatMembers") == 0) {
        int32_t total = (int32_t)_json_int(json, "total_count");
        if (total <= 0) {
            if (req->cb) req->cb(c, NULL, 0, req->ud);
            free(req); return;
        }
        tg_chat_member_t *members = calloc((size_t)total, sizeof(tg_chat_member_t));
        if (!members) { free(req); return; }

        /* Parse members array */
        const char *p = strstr(json, "\"members\":[");
        int count = 0;
        if (p) {
            p += strlen("\"members\":[");
            while (*p && *p != ']' && count < (int)total) {
                if (*p == '{') {
                    int depth = 0;
                    const char *start = p;
                    while (*p) {
                        if (*p == '{') depth++;
                        else if (*p == '}') { depth--; if (!depth) { p++; break; } }
                        p++;
                    }
                    size_t mlen = (size_t)(p - start);
                    char *mbuf  = malloc(mlen + 1);
                    if (mbuf) {
                        memcpy(mbuf, start, mlen);
                        mbuf[mlen] = '\0';
                        _parse_member_json(mbuf, &members[count]);
                        free(mbuf);
                        count++;
                    }
                } else p++;
            }
        }
        if (req->cb) req->cb(c, members, count, req->ud);
        free(members);
    }
    free(req);
}

/* ── async getters ───────────────────────────────────────────────────────── */

int tg_get_user(tg_client_t *c, int64_t user_id,
                tg_user_cb_fn cb, void *ud)
{
    _user_req_t *req = malloc(sizeof(*req));
    if (!req) return -1;
    req->cb = cb; req->ud = ud;
    char json[128];
    snprintf(json, sizeof(json),
             "{\"@type\":\"getUser\",\"user_id\":%lld}", (long long)user_id);
    return (int)_tg_send_pending(c, json, _on_get_user, req);
}

int tg_get_member(tg_client_t *c, int64_t chat_id, int64_t user_id,
                  tg_member_cb_fn cb, void *ud)
{
    _member_req_t *req = malloc(sizeof(*req));
    if (!req) return -1;
    req->cb = cb; req->ud = ud;
    char json[256];
    snprintf(json, sizeof(json),
             "{\"@type\":\"getChatMember\","
             "\"chat_id\":%lld,"
             "\"member_id\":{"
             "\"@type\":\"messageSenderUser\","
             "\"user_id\":%lld}}",
             (long long)chat_id, (long long)user_id);
    return (int)_tg_send_pending(c, json, _on_get_member, req);
}

int tg_get_members(tg_client_t *c, int64_t chat_id, int offset, int limit,
                   tg_members_cb_fn cb, void *ud)
{
    _members_req_t *req = malloc(sizeof(*req));
    if (!req) return -1;
    req->cb = cb; req->ud = ud;
    /* Use supergroup id (absolute value of chat_id minus 100000000000) */
    int64_t sg_id = (chat_id < -999999999) ? -(chat_id + 1000000000000LL) : -chat_id;
    char json[256];
    snprintf(json, sizeof(json),
             "{\"@type\":\"getSupergroupMembers\","
             "\"supergroup_id\":%lld,"
             "\"filter\":{\"@type\":\"supergroupMembersFilterRecent\"},"
             "\"offset\":%d,\"limit\":%d}",
             (long long)sg_id, offset, limit);
    return (int)_tg_send_pending(c, json, _on_get_members, req);
}

int tg_get_admins(tg_client_t *c, int64_t chat_id,
                  tg_members_cb_fn cb, void *ud)
{
    _members_req_t *req = malloc(sizeof(*req));
    if (!req) return -1;
    req->cb = cb; req->ud = ud;
    int64_t sg_id = (chat_id < -999999999) ? -(chat_id + 1000000000000LL) : -chat_id;
    char json[256];
    snprintf(json, sizeof(json),
             "{\"@type\":\"getSupergroupMembers\","
             "\"supergroup_id\":%lld,"
             "\"filter\":{"
             "\"@type\":\"supergroupMembersFilterAdministrators\"},"
             "\"offset\":0,\"limit\":200}",
             (long long)sg_id);
    return (int)_tg_send_pending(c, json, _on_get_members, req);
}

typedef struct { tg_messages_cb_fn cb; void *ud; } _msgs_req_t;

static void _on_get_messages(tg_client_t *c, const char *json, void *ud)
{
    _msgs_req_t *req = ud;
    char type[TG_TYPE_MAX] = {0};
    _json_type(json, type, sizeof(type));
    if (strcmp(type, "messages") == 0) {
        int32_t total = (int32_t)_json_int(json, "total_count");
        if (total <= 0) {
            if (req->cb) req->cb(c, NULL, 0, req->ud);
            free(req); return;
        }
        tg_message_t *msgs = calloc((size_t)total, sizeof(tg_message_t));
        if (!msgs) { free(req); return; }
        const char *p = strstr(json, "\"messages\":[");
        int count = 0;
        if (p) {
            p += strlen("\"messages\":[");
            while (*p && *p != ']' && count < (int)total) {
                if (*p == '{') {
                    int depth = 0;
                    const char *start = p;
                    while (*p) {
                        if (*p == '{') depth++;
                        else if (*p == '}') { depth--; if (!depth) { p++; break; } }
                        p++;
                    }
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

int tg_get_messages(tg_client_t *c, int64_t chat_id,
                    const int64_t *msg_ids, int count,
                    tg_messages_cb_fn cb, void *ud)
{
    _msgs_req_t *req = malloc(sizeof(*req));
    if (!req) return -1;
    req->cb = cb; req->ud = ud;

    char ids_buf[TG_TEXT_MAX] = {0};
    int pos = 0;
    pos += snprintf(ids_buf + pos, sizeof(ids_buf) - (size_t)pos, "[");
    for (int i = 0; i < count; i++) {
        if (i > 0)
            pos += snprintf(ids_buf + pos, sizeof(ids_buf) - (size_t)pos, ",");
        pos += snprintf(ids_buf + pos, sizeof(ids_buf) - (size_t)pos,
                        "%lld", (long long)msg_ids[i]);
    }
    snprintf(ids_buf + pos, sizeof(ids_buf) - (size_t)pos, "]");

    char json[TG_TEXT_MAX + 128];
    snprintf(json, sizeof(json),
             "{\"@type\":\"getMessages\","
             "\"chat_id\":%lld,\"message_ids\":%s}",
             (long long)chat_id, ids_buf);
    return (int)_tg_send_pending(c, json, _on_get_messages, req);
}

/* ── block / unblock ─────────────────────────────────────────────────────── */

int tg_block_user(tg_client_t *c, int64_t user_id)
{
    char buf[256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"toggleMessageSenderIsBlocked\","
             "\"sender_id\":{"
             "\"@type\":\"messageSenderUser\","
             "\"user_id\":%lld},"
             "\"is_blocked\":true}",
             (long long)user_id);
    return (int)_tg_send_raw(c, buf);
}

int tg_unblock_user(tg_client_t *c, int64_t user_id)
{
    char buf[256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"toggleMessageSenderIsBlocked\","
             "\"sender_id\":{"
             "\"@type\":\"messageSenderUser\","
             "\"user_id\":%lld},"
             "\"is_blocked\":false}",
             (long long)user_id);
    return (int)_tg_send_raw(c, buf);
}

/* ── member accessors ────────────────────────────────────────────────────── */

const tg_user_t *tg_member_user(const tg_chat_member_t *m)    { return &m->user; }
const char      *tg_member_status(const tg_chat_member_t *m)  { return m->status; }
int              tg_member_is_admin(const tg_chat_member_t *m) { return m->is_admin; }
int              tg_member_is_creator(const tg_chat_member_t *m){ return m->is_creator; }
int32_t          tg_member_until_date(const tg_chat_member_t *m){ return m->until_date; }
int              tg_member_can_ban(const tg_chat_member_t *m)  { return m->can_ban_users; }
int              tg_member_can_delete_msgs(const tg_chat_member_t *m)
                                                { return m->can_delete_messages; }
int              tg_member_can_invite(const tg_chat_member_t *m){ return m->can_invite_users; }
int              tg_member_can_pin(const tg_chat_member_t *m)  { return m->can_pin_messages; }
