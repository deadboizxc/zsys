/*
 * tg_bot.c  —  bot-specific handlers: callback/inline queries, member events,
 *              answer_callback_query.
 */

#include "tg_internal.h"
#include <string.h>

/* ── _add_handler (duplicated from tg_message.c for independence) ────────── */

static tg_handler_id_t _bot_add_handler(tg_client_t *c, tg_handler_t *h)
{
    pthread_mutex_lock(&c->handlers_lock);
    if (c->handler_count >= TG_MAX_HANDLERS) {
        pthread_mutex_unlock(&c->handlers_lock);
        return -1;
    }
    h->id     = c->next_handler_id++;
    h->active = 1;
    c->handlers[c->handler_count++] = *h;
    pthread_mutex_unlock(&c->handlers_lock);
    return h->id;
}

/* ── callback query handler ──────────────────────────────────────────────── */

tg_handler_id_t tg_on_callback_query(tg_client_t *c,
                                      tg_callback_query_fn fn, void *ud)
{
    tg_handler_t h = {0};
    h.type          = TG_HTYPE_CALLBACK_QUERY;
    h.cb_query_fn   = fn;
    h.userdata      = ud;
    return _bot_add_handler(c, &h);
}

/* ── inline query handler ────────────────────────────────────────────────── */

tg_handler_id_t tg_on_inline_query(tg_client_t *c,
                                    tg_inline_query_fn fn, void *ud)
{
    tg_handler_t h = {0};
    h.type            = TG_HTYPE_INLINE_QUERY;
    h.inline_query_fn = fn;
    h.userdata        = ud;
    return _bot_add_handler(c, &h);
}

/* ── chat member join/left handlers ──────────────────────────────────────── */

tg_handler_id_t tg_on_new_chat_member(tg_client_t *c,
                                       tg_member_event_fn fn, void *ud)
{
    tg_handler_t h = {0};
    h.type             = TG_HTYPE_CHAT_MEMBER;
    h.member_event_fn  = fn;
    h.userdata         = ud;
    h.is_left          = 0;
    return _bot_add_handler(c, &h);
}

tg_handler_id_t tg_on_left_chat_member(tg_client_t *c,
                                        tg_member_event_fn fn, void *ud)
{
    tg_handler_t h = {0};
    h.type             = TG_HTYPE_CHAT_MEMBER;
    h.member_event_fn  = fn;
    h.userdata         = ud;
    h.is_left          = 1;
    return _bot_add_handler(c, &h);
}

/* ── answer callback query ───────────────────────────────────────────────── */

int tg_answer_callback_query(tg_client_t *c, int64_t query_id,
                              const char *text, int show_alert, int cache_time)
{
    char buf[TG_TEXT_MAX + 256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"answerCallbackQuery\","
             "\"callback_query_id\":%lld,"
             "\"text\":\"%s\","
             "\"show_alert\":%s,"
             "\"url\":\"\","
             "\"cache_time\":%d}",
             (long long)query_id,
             text ? text : "",
             show_alert ? "true" : "false",
             cache_time);
    return (int)_tg_send_raw(c, buf);
}
