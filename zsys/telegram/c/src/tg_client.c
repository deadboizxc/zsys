/*
 * tg_client.c  —  lifecycle, global polling thread, client registry.
 */

#include "tg_internal.h"
#include <stdarg.h>
#include <time.h>
#include <errno.h>

/* ── global registry ─────────────────────────────────────────────────────── */

tg_client_t    *_tg_clients[TG_MAX_CLIENTS]  = {0};
int             _tg_client_count             = 0;
pthread_mutex_t _tg_global_lock              = PTHREAD_MUTEX_INITIALIZER;

static pthread_t        _poll_thread;
static volatile int     _poll_running = 0;
static pthread_once_t   _poll_once    = PTHREAD_ONCE_INIT;

/* ── JSON helpers ────────────────────────────────────────────────────────── */

/* Find first occurrence of "key": in JSON and return pointer past the colon. */
static const char *_key_ptr(const char *json, const char *key)
{
    char needle[TG_TYPE_MAX + 4];
    snprintf(needle, sizeof(needle), "\"%s\"", key);
    const char *p = strstr(json, needle);
    if (!p) return NULL;
    p += strlen(needle);
    while (*p == ' ' || *p == '\t') p++;
    if (*p != ':') return NULL;
    p++;
    while (*p == ' ' || *p == '\t') p++;
    return p;
}

int _json_type(const char *json, char *buf, size_t sz)
{
    return _json_str(json, "@type", buf, sz);
}

int64_t _json_int(const char *json, const char *key)
{
    const char *p = _key_ptr(json, key);
    if (!p) return 0;
    return (int64_t)strtoll(p, NULL, 10);
}

int _json_str(const char *json, const char *key, char *buf, size_t sz)
{
    const char *p = _key_ptr(json, key);
    if (!p || *p != '"') return 0;
    p++;
    size_t i = 0;
    while (*p && *p != '"' && i + 1 < sz) {
        if (*p == '\\') {
            p++;
            if (!*p) break;
        }
        buf[i++] = *p++;
    }
    buf[i] = '\0';
    return 1;
}

int _json_bool(const char *json, const char *key)
{
    const char *p = _key_ptr(json, key);
    if (!p) return 0;
    return strncmp(p, "true", 4) == 0;
}

const char *_json_obj(const char *json, const char *key)
{
    const char *p = _key_ptr(json, key);
    if (!p || *p != '{') return NULL;
    return p;
}

/* ── global polling thread ───────────────────────────────────────────────── */

static void *_poll_loop(void *arg)
{
    (void)arg;
    while (_poll_running) {
        const char *json = td_receive(0.05);
        if (!json) continue;

        int td_id = (int)_json_int(json, "@client_id");
        if (td_id <= 0) continue;

        pthread_mutex_lock(&_tg_global_lock);
        tg_client_t *c = _tg_find_client(td_id);
        pthread_mutex_unlock(&_tg_global_lock);

        if (c && c->running) _tg_dispatch(c, json);
    }
    return NULL;
}

static void _start_poll_thread(void)
{
    _poll_running = 1;
    pthread_create(&_poll_thread, NULL, _poll_loop, NULL);
}

/* ── client registry ─────────────────────────────────────────────────────── */

tg_client_t *_tg_find_client(int td_id)
{
    for (int i = 0; i < _tg_client_count; i++) {
        if (_tg_clients[i] && _tg_clients[i]->td_id == td_id)
            return _tg_clients[i];
    }
    return NULL;
}

void _tg_register_client(tg_client_t *c)
{
    pthread_mutex_lock(&_tg_global_lock);
    for (int i = 0; i < TG_MAX_CLIENTS; i++) {
        if (!_tg_clients[i]) {
            _tg_clients[i] = c;
            if (i >= _tg_client_count) _tg_client_count = i + 1;
            break;
        }
    }
    pthread_mutex_unlock(&_tg_global_lock);
}

void _tg_unregister_client(tg_client_t *c)
{
    pthread_mutex_lock(&_tg_global_lock);
    for (int i = 0; i < TG_MAX_CLIENTS; i++) {
        if (_tg_clients[i] == c) {
            _tg_clients[i] = NULL;
            break;
        }
    }
    pthread_mutex_unlock(&_tg_global_lock);
}

/* ── config ──────────────────────────────────────────────────────────────── */

static char *_dup(const char *s)
{
    return s ? strdup(s) : NULL;
}

tg_config_t *tg_config_new(int32_t api_id, const char *api_hash)
{
    tg_config_t *cfg = calloc(1, sizeof(*cfg));
    if (!cfg) return NULL;
    cfg->api_id        = api_id;
    cfg->api_hash      = _dup(api_hash);
    cfg->session_dir   = _dup(".");
    cfg->session_name  = _dup("session");
    cfg->device_model  = _dup("Desktop");
    cfg->system_version = _dup("Linux");
    cfg->app_version   = _dup("1.0.0");
    cfg->lang_code     = _dup("en");
    cfg->log_verbosity = 0;
    return cfg;
}

void tg_config_free(tg_config_t *cfg)
{
    if (!cfg) return;
    free((char *)cfg->api_hash);
    free((char *)cfg->session_dir);
    free((char *)cfg->session_name);
    free((char *)cfg->bot_token);
    free((char *)cfg->phone);
    free((char *)cfg->device_model);
    free((char *)cfg->system_version);
    free((char *)cfg->app_version);
    free((char *)cfg->lang_code);
    free(cfg);
}

static tg_config_t *_config_clone(const tg_config_t *src)
{
    tg_config_t *dst = calloc(1, sizeof(*dst));
    if (!dst) return NULL;
    dst->api_id        = src->api_id;
    dst->api_hash      = _dup(src->api_hash);
    dst->session_dir   = _dup(src->session_dir);
    dst->session_name  = _dup(src->session_name);
    dst->bot_token     = _dup(src->bot_token);
    dst->phone         = _dup(src->phone);
    dst->device_model  = _dup(src->device_model);
    dst->system_version = _dup(src->system_version);
    dst->app_version   = _dup(src->app_version);
    dst->lang_code     = _dup(src->lang_code);
    dst->use_test_dc   = src->use_test_dc;
    dst->log_verbosity = src->log_verbosity;
    return dst;
}

/* ── public API ──────────────────────────────────────────────────────────── */

tg_client_t *tg_client_new(const tg_config_t *cfg)
{
    tg_client_t *c = calloc(1, sizeof(*c));
    if (!c) return NULL;

    c->config          = _config_clone(cfg);
    c->auth_state      = TG_AUTH_INITIAL;
    c->next_handler_id = 1;

    pthread_mutex_init(&c->handlers_lock, NULL);
    pthread_mutex_init(&c->auth_lock, NULL);
    pthread_cond_init(&c->auth_cond, NULL);
    pthread_mutex_init(&c->run_lock, NULL);
    pthread_cond_init(&c->run_cond, NULL);

    /* Set TDLib log verbosity */
    char log_req[128];
    snprintf(log_req, sizeof(log_req),
             "{\"@type\":\"setLogVerbosityLevel\",\"new_verbosity_level\":%d}",
             cfg->log_verbosity);
    td_execute(log_req);

    c->td_id = td_create_client_id();
    return c;
}

void tg_client_free(tg_client_t *c)
{
    if (!c) return;
    tg_config_free(c->config);
    pthread_mutex_destroy(&c->handlers_lock);
    pthread_mutex_destroy(&c->auth_lock);
    pthread_cond_destroy(&c->auth_cond);
    pthread_mutex_destroy(&c->run_lock);
    pthread_cond_destroy(&c->run_cond);
    free(c);
}

void tg_client_set_auth_handlers(
    tg_client_t    *c,
    tg_ask_phone_fn ask_phone,
    tg_ask_code_fn  ask_code,
    tg_ask_pass_fn  ask_pass,
    tg_ready_fn     on_ready,
    tg_error_fn     on_error,
    void           *userdata)
{
    c->ask_phone = ask_phone;
    c->ask_code  = ask_code;
    c->ask_pass  = ask_pass;
    c->on_ready  = on_ready;
    c->on_error  = on_error;
    c->auth_ud   = userdata;
}

int tg_client_start(tg_client_t *c)
{
    c->running = 1;
    _tg_register_client(c);

    /* Start global polling thread (idempotent via pthread_once) */
    pthread_once(&_poll_once, _start_poll_thread);

    /* Kick TDLib to start sending updates */
    _tg_send_fmt(c, "{\"@type\":\"getOption\",\"name\":\"version\"}");
    return 0;
}

void tg_client_stop(tg_client_t *c)
{
    if (!c->running) return;
    c->running = 0;
    _tg_send_fmt(c, "{\"@type\":\"close\"}");
    _tg_unregister_client(c);

    pthread_mutex_lock(&c->run_lock);
    pthread_cond_broadcast(&c->run_cond);
    pthread_mutex_unlock(&c->run_lock);
}

void tg_client_run(tg_client_t *c)
{
    pthread_mutex_lock(&c->run_lock);
    while (c->running)
        pthread_cond_wait(&c->run_cond, &c->run_lock);
    pthread_mutex_unlock(&c->run_lock);
}

int tg_client_wait_ready(tg_client_t *c, int timeout_sec)
{
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    ts.tv_sec += timeout_sec;

    pthread_mutex_lock(&c->auth_lock);
    while (c->auth_state != TG_AUTH_READY && c->auth_state != TG_AUTH_ERROR) {
        int rc = pthread_cond_timedwait(&c->auth_cond, &c->auth_lock, &ts);
        if (rc == ETIMEDOUT) {
            pthread_mutex_unlock(&c->auth_lock);
            return -1;
        }
    }
    int ok = (c->auth_state == TG_AUTH_READY) ? 0 : -1;
    pthread_mutex_unlock(&c->auth_lock);
    return ok;
}

/* ── memory ──────────────────────────────────────────────────────────────── */

void tg_free(char *ptr)
{
    free(ptr);
}

/* ── request helpers ─────────────────────────────────────────────────────── */

int64_t _tg_send_raw(tg_client_t *c, const char *json)
{
    td_send(c->td_id, json);
    return ++c->next_req_id;
}

int64_t _tg_send_fmt(tg_client_t *c, const char *fmt, ...)
{
    char buf[8192];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    return _tg_send_raw(c, buf);
}
