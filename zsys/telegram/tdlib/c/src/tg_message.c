/*
 * tg_message.c  —  message accessors, actions, handler registration.
 */

#include "tg_internal.h"
#include <string.h>
#include <stdio.h>

/* ── message accessors ───────────────────────────────────────────────────── */

int64_t tg_msg_id(const tg_message_t *m)          { return m->id; }
int64_t tg_msg_chat_id(const tg_message_t *m)     { return m->chat_id; }
int64_t tg_msg_sender_id(const tg_message_t *m)   { return m->sender_id; }
int64_t tg_msg_reply_to(const tg_message_t *m)    { return m->reply_to_id; }
int     tg_msg_is_out(const tg_message_t *m)      { return m->is_out; }
int     tg_msg_is_private(const tg_message_t *m)  { return m->chat_type == TG_CHAT_PRIVATE; }
int     tg_msg_is_group(const tg_message_t *m)    {
    return m->chat_type == TG_CHAT_GROUP || m->chat_type == TG_CHAT_SUPERGROUP;
}
int     tg_msg_is_channel(const tg_message_t *m)  { return m->chat_type == TG_CHAT_CHANNEL; }

const char *tg_msg_text(const tg_message_t *m)
{
    return m->text[0] ? m->text : NULL;
}

/* ── user accessors ──────────────────────────────────────────────────────── */

int64_t     tg_user_id(const tg_user_t *u)         { return u->id; }
const char *tg_user_first_name(const tg_user_t *u) { return u->first_name; }
const char *tg_user_last_name(const tg_user_t *u)  { return u->last_name; }
const char *tg_user_username(const tg_user_t *u)   { return u->username; }
int         tg_user_is_bot(const tg_user_t *u)     { return u->is_bot; }

/* ── self info ───────────────────────────────────────────────────────────── */

int64_t     tg_me_id(tg_client_t *c)         { return c->me.id; }
const char *tg_me_username(tg_client_t *c)   { return c->me.username; }
const char *tg_me_first_name(tg_client_t *c) { return c->me.first_name; }

/* ── handler registration ────────────────────────────────────────────────── */

static tg_handler_id_t _add_handler(tg_client_t *c, tg_handler_t *h)
{
    pthread_mutex_lock(&c->handlers_lock);
    if (c->handler_count >= TG_MAX_HANDLERS) {
        pthread_mutex_unlock(&c->handlers_lock);
        return -1;
    }
    h->id = c->next_handler_id++;
    h->active = 1;
    c->handlers[c->handler_count++] = *h;
    pthread_mutex_unlock(&c->handlers_lock);
    return h->id;
}

tg_handler_id_t tg_on_message(tg_client_t *c, uint32_t filters,
                               tg_message_fn fn, void *ud)
{
    tg_handler_t h = {0};
    h.type    = TG_HTYPE_MESSAGE;
    h.filters = filters;
    h.msg_fn  = fn;
    h.userdata = ud;
    return _add_handler(c, &h);
}

tg_handler_id_t tg_on_edited(tg_client_t *c, uint32_t filters,
                              tg_message_fn fn, void *ud)
{
    tg_handler_t h = {0};
    h.type    = TG_HTYPE_EDITED;
    h.filters = filters;
    h.msg_fn  = fn;
    h.userdata = ud;
    return _add_handler(c, &h);
}

tg_handler_id_t tg_on_raw(tg_client_t *c, const char *update_type,
                           tg_raw_fn fn, void *ud)
{
    tg_handler_t h = {0};
    h.type     = TG_HTYPE_RAW;
    h.raw_fn   = fn;
    h.userdata = ud;
    if (update_type)
        snprintf(h.raw_update_type, sizeof(h.raw_update_type), "%s", update_type);
    return _add_handler(c, &h);
}

void tg_remove_handler(tg_client_t *c, tg_handler_id_t hid)
{
    pthread_mutex_lock(&c->handlers_lock);
    for (int i = 0; i < c->handler_count; i++) {
        if (c->handlers[i].id == hid) {
            c->handlers[i].active = 0;
            break;
        }
    }
    pthread_mutex_unlock(&c->handlers_lock);
}

/* ── format_input_message_content helper ────────────────────────────────── */

static void _build_text_content(char *out, size_t sz,
                                 const char *text, const char *parse_mode)
{
    if (!parse_mode || strcmp(parse_mode, "plain") == 0) {
        snprintf(out, sz,
            "{\"@type\":\"inputMessageText\","
            "\"text\":{\"@type\":\"formattedText\",\"text\":\"%s\","
            "\"entities\":[]}}",
            text);
    } else {
        const char *tdpm = strcmp(parse_mode, "md") == 0
                           ? "textParseModeMarkdown"
                           : "textParseModeHTML";
        snprintf(out, sz,
            "{\"@type\":\"inputMessageText\","
            "\"text\":{\"@type\":\"formattedText\",\"text\":\"%s\","
            "\"entities\":[]},"
            "\"parse_mode\":{\"@type\":\"%s\"}}",
            text, tdpm);
    }
}

/* ── actions ─────────────────────────────────────────────────────────────── */

int tg_send_text(tg_client_t *c, int64_t chat_id,
                 const char *text, const char *parse_mode)
{
    char content[TG_TEXT_MAX + 256];
    _build_text_content(content, sizeof(content), text, parse_mode);

    char buf[TG_TEXT_MAX + 512];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"sendMessage\","
             "\"chat_id\":%lld,"
             "\"input_message_content\":%s}",
             (long long)chat_id, content);
    return (int)_tg_send_raw(c, buf);
}

int tg_reply_text(tg_client_t *c, const tg_message_t *orig,
                  const char *text, const char *parse_mode)
{
    char content[TG_TEXT_MAX + 256];
    _build_text_content(content, sizeof(content), text, parse_mode);

    char buf[TG_TEXT_MAX + 512];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"sendMessage\","
             "\"chat_id\":%lld,"
             "\"reply_to\":{\"@type\":\"inputMessageReplyToMessage\","
             "\"message_id\":%lld},"
             "\"input_message_content\":%s}",
             (long long)orig->chat_id,
             (long long)orig->id,
             content);
    return (int)_tg_send_raw(c, buf);
}

int tg_edit_text(tg_client_t *c, int64_t chat_id, int64_t msg_id,
                 const char *text, const char *parse_mode)
{
    char content[TG_TEXT_MAX + 256];
    _build_text_content(content, sizeof(content), text, parse_mode);

    char buf[TG_TEXT_MAX + 512];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"editMessageText\","
             "\"chat_id\":%lld,"
             "\"message_id\":%lld,"
             "\"input_message_content\":%s}",
             (long long)chat_id, (long long)msg_id, content);
    return (int)_tg_send_raw(c, buf);
}

int tg_delete_msg(tg_client_t *c, int64_t chat_id, int64_t msg_id)
{
    char buf[256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"deleteMessages\","
             "\"chat_id\":%lld,"
             "\"message_ids\":[%lld],"
             "\"revoke\":true}",
             (long long)chat_id, (long long)msg_id);
    return (int)_tg_send_raw(c, buf);
}

int tg_forward(tg_client_t *c, int64_t to_chat,
               int64_t from_chat, int64_t msg_id)
{
    char buf[256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"forwardMessages\","
             "\"chat_id\":%lld,"
             "\"from_chat_id\":%lld,"
             "\"message_ids\":[%lld]}",
             (long long)to_chat,
             (long long)from_chat,
             (long long)msg_id);
    return (int)_tg_send_raw(c, buf);
}

int tg_react(tg_client_t *c, int64_t chat_id, int64_t msg_id,
             const char *emoji)
{
    char buf[256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"addMessageReaction\","
             "\"chat_id\":%lld,"
             "\"message_id\":%lld,"
             "\"reaction_type\":{\"@type\":\"reactionTypeEmoji\","
             "\"emoji\":\"%s\"},"
             "\"is_big\":false}",
             (long long)chat_id, (long long)msg_id, emoji);
    return (int)_tg_send_raw(c, buf);
}

/* ── file upload helpers ─────────────────────────────────────────────────── */

static int _send_file(tg_client_t *c, int64_t chat_id,
                      const char *tg_type, const char *path,
                      const char *caption)
{
    char buf[TG_PATH_MAX + 512];
    if (caption && caption[0]) {
        snprintf(buf, sizeof(buf),
                 "{\"@type\":\"sendMessage\","
                 "\"chat_id\":%lld,"
                 "\"input_message_content\":{"
                 "\"@type\":\"%s\","
                 "\"file\":{\"@type\":\"inputFileLocal\",\"path\":\"%s\"},"
                 "\"caption\":{\"@type\":\"formattedText\","
                 "\"text\":\"%s\",\"entities\":[]}}}",
                 (long long)chat_id, tg_type, path, caption);
    } else {
        snprintf(buf, sizeof(buf),
                 "{\"@type\":\"sendMessage\","
                 "\"chat_id\":%lld,"
                 "\"input_message_content\":{"
                 "\"@type\":\"%s\","
                 "\"file\":{\"@type\":\"inputFileLocal\",\"path\":\"%s\"}}}",
                 (long long)chat_id, tg_type, path);
    }
    return (int)_tg_send_raw(c, buf);
}

int tg_send_photo(tg_client_t *c, int64_t chat_id,
                  const char *path, const char *caption)
{
    return _send_file(c, chat_id, "inputMessagePhoto", path, caption);
}

int tg_send_video(tg_client_t *c, int64_t chat_id,
                  const char *path, const char *caption)
{
    return _send_file(c, chat_id, "inputMessageVideo", path, caption);
}

int tg_send_audio(tg_client_t *c, int64_t chat_id,
                  const char *path, const char *caption)
{
    return _send_file(c, chat_id, "inputMessageAudio", path, caption);
}

int tg_send_doc(tg_client_t *c, int64_t chat_id,
                const char *path, const char *caption)
{
    return _send_file(c, chat_id, "inputMessageDocument", path, caption);
}

/* ── file download ───────────────────────────────────────────────────────── */

int tg_download_file(tg_client_t *c, int32_t file_id,
                     const char *dest_path,
                     tg_progress_fn cb, void *ud)
{
    /* TODO: store dest_path + cb + ud in a pending download map,
     * then track updateFile events until is_downloading_completed == true.
     * For now: just send the TDLib request. */
    (void)dest_path; (void)cb; (void)ud;

    char buf[256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"downloadFile\","
             "\"file_id\":%d,"
             "\"priority\":1,"
             "\"offset\":0,"
             "\"limit\":0,"
             "\"synchronous\":false}",
             file_id);
    return (int)_tg_send_raw(c, buf);
}
