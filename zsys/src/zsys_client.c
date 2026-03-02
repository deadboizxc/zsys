/**
 * @file zsys_client.c
 * @brief Universal C configuration for a Telegram userbot/bot client — implementation.
 *
 * Flat JSON serialisation (secrets bot_token and api_hash are excluded).
 * Validation checks required fields based on client mode.
 */
// RU: Реализация ZsysClientConfig. Секреты в JSON не включаются.

#define _POSIX_C_SOURCE 200809L /* for strdup */

#include "zsys_client.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <stdint.h>
#include <inttypes.h>

/* ══════════════════════════ Internal Buf helper ══════════════════════════ */

typedef struct { char *data; size_t len, cap; } Buf;

static int  buf_init(Buf *b, size_t n) { b->data = malloc(n); b->len = 0; b->cap = n; return b->data != NULL; }
static char *buf_finish(Buf *b)        { char *r = b->data; b->data = NULL; return r; }

static int buf_write(Buf *b, const char *s, size_t n) {
    if (b->len + n + 1 > b->cap) {
        size_t nc = (b->cap + n + 1) * 2;
        char *p = realloc(b->data, nc);
        if (!p) return 0;
        b->data = p; b->cap = nc;
    }
    memcpy(b->data + b->len, s, n);
    b->len += n;
    b->data[b->len] = '\0';
    return 1;
}
static int buf_writec(Buf *b, char c)        { return buf_write(b, &c, 1); }
static int buf_writes(Buf *b, const char *s) { return buf_write(b, s, strlen(s)); }

/* Append a JSON-escaped string (including surrounding quotes). */
// RU: Добавить JSON-строку с экранированием и кавычками.
static void buf_json_str(Buf *b, const char *s) {
    buf_writec(b, '"');
    if (s) {
        for (const char *p = s; *p; p++) {
            if      (*p == '"')  { buf_writes(b, "\\\""); }
            else if (*p == '\\') { buf_writes(b, "\\\\"); }
            else if (*p == '\n') { buf_writes(b, "\\n");  }
            else if (*p == '\r') { buf_writes(b, "\\r");  }
            else if (*p == '\t') { buf_writes(b, "\\t");  }
            else                 { buf_writec(b, *p);      }
        }
    }
    buf_writec(b, '"');
}

/* ══════════════════════════ Internal JSON parser ═════════════════════════ */

/* Extract a string value for "key" from flat JSON into out[out_sz]. */
// RU: Извлечь строковое значение по ключу из плоского JSON.
static int json_read_str(const char *json, const char *key, char *out, size_t out_sz) {
    char needle[256];
    snprintf(needle, sizeof(needle), "\"%s\":", key);
    const char *p = strstr(json, needle);
    if (!p) return -1;
    p += strlen(needle);
    while (*p == ' ' || *p == '\t') p++;
    if (*p != '"') return -1;
    p++;
    size_t i = 0;
    while (*p && *p != '"' && i < out_sz - 1) {
        if (*p == '\\') {
            p++;
            if      (*p == 'n')  { out[i++] = '\n'; p++; }
            else if (*p == 't')  { out[i++] = '\t'; p++; }
            else if (*p == 'r')  { out[i++] = '\r'; p++; }
            else if (*p == '"')  { out[i++] = '"';  p++; }
            else if (*p == '\\') { out[i++] = '\\'; p++; }
            else if (*p)         { out[i++] = *p++;      }
        } else {
            out[i++] = *p++;
        }
    }
    out[i] = '\0';
    return 0;
}

/* Extract an int64 value for "key" from flat JSON. */
// RU: Извлечь целое 64-битное значение по ключу из плоского JSON.
static int json_read_i64(const char *json, const char *key, int64_t *out) {
    char needle[256];
    snprintf(needle, sizeof(needle), "\"%s\":", key);
    const char *p = strstr(json, needle);
    if (!p) return -1;
    p += strlen(needle);
    while (*p == ' ' || *p == '\t') p++;
    char *end;
    *out = (int64_t)strtoll(p, &end, 10);
    return (end == p) ? -1 : 0;
}

/* Extract a 32-bit int for "key" from flat JSON. */
// RU: Извлечь 32-битное значение по ключу из плоского JSON.
static int json_read_i32(const char *json, const char *key, int32_t *out) {
    int64_t v;
    if (json_read_i64(json, key, &v) < 0) return -1;
    *out = (int32_t)v;
    return 0;
}

/* Extract an int value for "key" from flat JSON. */
// RU: Извлечь int по ключу из плоского JSON.
static int json_read_int(const char *json, const char *key, int *out) {
    int64_t v;
    if (json_read_i64(json, key, &v) < 0) return -1;
    *out = (int)v;
    return 0;
}

/* ══════════════════════════ Lifecycle ═══════════════════════════════════ */

/**
 * @brief Allocate a new ZsysClientConfig with sensible defaults.
 *
 * Defaults: mode=USER, lang_code="en", sleep_threshold=60, max_concurrent=1.
 * @return Heap-allocated config, or NULL on failure.
 */
// RU: Создаёт ZsysClientConfig с разумными значениями по умолчанию.
ZsysClientConfig *zsys_client_config_new(void) {
    ZsysClientConfig *c = (ZsysClientConfig *)calloc(1, sizeof(ZsysClientConfig));
    if (!c) return NULL;
    c->mode            = ZSYS_CLIENT_USER;
    c->sleep_threshold = 60;
    c->max_concurrent  = 1;
    c->lang_code       = strdup("en");
    if (!c->lang_code) { free(c); return NULL; }
    return c;
}

/**
 * @brief Free a ZsysClientConfig and all its string fields.
 * @param cfg Pointer to config (NULL-safe).
 */
// RU: Освобождает ZsysClientConfig и все строки.
void zsys_client_config_free(ZsysClientConfig *cfg) {
    if (!cfg) return;
    free(cfg->api_hash);
    free(cfg->session_name);
    free(cfg->phone);
    free(cfg->bot_token);
    free(cfg->device_model);
    free(cfg->system_version);
    free(cfg->app_version);
    free(cfg->lang_code);
    free(cfg->lang_pack);
    free(cfg->proxy_host);
    free(cfg->proxy_user);
    free(cfg->proxy_pass);
    free(cfg);
}

/**
 * @brief Deep-copy src into dst (all strings strdup-ed).
 * @param dst Destination config (must be zero-initialised or freed first).
 * @param src Source config.
 * @return 0 on success, -1 on allocation failure.
 */
// RU: Глубокое копирование конфигурации (все строки через strdup).
int zsys_client_config_copy(ZsysClientConfig *dst, const ZsysClientConfig *src) {
    if (!dst || !src) return -1;
    dst->api_id          = src->api_id;
    dst->mode            = src->mode;
    dst->proxy_port      = src->proxy_port;
    dst->sleep_threshold = src->sleep_threshold;
    dst->max_concurrent  = src->max_concurrent;
    dst->api_hash       = src->api_hash       ? strdup(src->api_hash)       : NULL;
    dst->session_name   = src->session_name   ? strdup(src->session_name)   : NULL;
    dst->phone          = src->phone          ? strdup(src->phone)          : NULL;
    dst->bot_token      = src->bot_token      ? strdup(src->bot_token)      : NULL;
    dst->device_model   = src->device_model   ? strdup(src->device_model)   : NULL;
    dst->system_version = src->system_version ? strdup(src->system_version) : NULL;
    dst->app_version    = src->app_version    ? strdup(src->app_version)    : NULL;
    dst->lang_code      = src->lang_code      ? strdup(src->lang_code)      : NULL;
    dst->lang_pack      = src->lang_pack      ? strdup(src->lang_pack)      : NULL;
    dst->proxy_host     = src->proxy_host     ? strdup(src->proxy_host)     : NULL;
    dst->proxy_user     = src->proxy_user     ? strdup(src->proxy_user)     : NULL;
    dst->proxy_pass     = src->proxy_pass     ? strdup(src->proxy_pass)     : NULL;
    return 0;
}

/* ══════════════════════════ Setters ═════════════════════════════════════ */

/**
 * @brief Set Telegram API app ID.
 * @param c      ZsysClientConfig instance.
 * @param api_id API ID from my.telegram.org.
 */
// RU: Установить API ID приложения Telegram.
void zsys_client_set_api_id(ZsysClientConfig *c, int32_t api_id) {
    if (!c) return;
    c->api_id = api_id;
}

/**
 * @brief Set client operating mode (USER or BOT).
 * @param c    ZsysClientConfig instance.
 * @param mode ZsysClientMode enum value.
 */
// RU: Установить режим клиента (USER или BOT).
void zsys_client_set_mode(ZsysClientConfig *c, ZsysClientMode mode) {
    if (!c) return;
    c->mode = mode;
}

/**
 * @brief Set FloodWait sleep threshold in seconds.
 * @param c         ZsysClientConfig instance.
 * @param threshold Seconds to sleep (default 60).
 */
// RU: Порог ожидания FloodWait в секундах.
void zsys_client_set_sleep_threshold(ZsysClientConfig *c, int32_t threshold) {
    if (!c) return;
    c->sleep_threshold = threshold;
}

/**
 * @brief Set maximum number of concurrent message handlers.
 * @param c     ZsysClientConfig instance.
 * @param count Max concurrent handlers (default 1).
 */
// RU: Максимальное число параллельных обработчиков.
void zsys_client_set_max_concurrent(ZsysClientConfig *c, int32_t count) {
    if (!c) return;
    c->max_concurrent = (count > 0) ? count : 1;
}

/** @brief Set api_hash (strdup). NULL clears the field. */
// RU: Установить api_hash (strdup). NULL очищает поле.
int zsys_client_set_api_hash(ZsysClientConfig *c, const char *val) {
    if (!c) return -1;
    free(c->api_hash);
    c->api_hash = val ? strdup(val) : NULL;
    return 0;
}

/** @brief Set session_name (strdup). NULL clears the field. */
// RU: Установить session_name (strdup).
int zsys_client_set_session_name(ZsysClientConfig *c, const char *val) {
    if (!c) return -1;
    free(c->session_name);
    c->session_name = val ? strdup(val) : NULL;
    return 0;
}

/** @brief Set phone (strdup). NULL clears the field. */
// RU: Установить phone (strdup).
int zsys_client_set_phone(ZsysClientConfig *c, const char *val) {
    if (!c) return -1;
    free(c->phone);
    c->phone = val ? strdup(val) : NULL;
    return 0;
}

/** @brief Set bot_token (strdup). NULL clears the field. */
// RU: Установить bot_token (strdup).
int zsys_client_set_bot_token(ZsysClientConfig *c, const char *val) {
    if (!c) return -1;
    free(c->bot_token);
    c->bot_token = val ? strdup(val) : NULL;
    return 0;
}

/** @brief Set device_model (strdup). NULL clears the field. */
// RU: Установить device_model (strdup).
int zsys_client_set_device_model(ZsysClientConfig *c, const char *val) {
    if (!c) return -1;
    free(c->device_model);
    c->device_model = val ? strdup(val) : NULL;
    return 0;
}

/** @brief Set system_version (strdup). NULL clears the field. */
// RU: Установить system_version (strdup).
int zsys_client_set_system_version(ZsysClientConfig *c, const char *val) {
    if (!c) return -1;
    free(c->system_version);
    c->system_version = val ? strdup(val) : NULL;
    return 0;
}

/** @brief Set app_version (strdup). NULL clears the field. */
// RU: Установить app_version (strdup).
int zsys_client_set_app_version(ZsysClientConfig *c, const char *val) {
    if (!c) return -1;
    free(c->app_version);
    c->app_version = val ? strdup(val) : NULL;
    return 0;
}

/** @brief Set lang_code (strdup). NULL clears the field. */
// RU: Установить lang_code (strdup).
int zsys_client_set_lang_code(ZsysClientConfig *c, const char *val) {
    if (!c) return -1;
    free(c->lang_code);
    c->lang_code = val ? strdup(val) : NULL;
    return 0;
}

/** @brief Set lang_pack (strdup). NULL clears the field. */
// RU: Установить lang_pack (strdup).
int zsys_client_set_lang_pack(ZsysClientConfig *c, const char *val) {
    if (!c) return -1;
    free(c->lang_pack);
    c->lang_pack = val ? strdup(val) : NULL;
    return 0;
}

/**
 * @brief Set all proxy fields at once.
 * @param c    Config instance.
 * @param host Proxy hostname (strdup). NULL disables proxy.
 * @param port Proxy port (0 = disabled).
 * @param user Proxy username (strdup). NULL if not required.
 * @param pass Proxy password (strdup). NULL if not required.
 * @return 0 on success, -1 on NULL config.
 */
// RU: Установить все поля прокси разом.
int zsys_client_set_proxy(ZsysClientConfig *c,
                          const char *host, int32_t port,
                          const char *user, const char *pass) {
    if (!c) return -1;
    free(c->proxy_host); c->proxy_host = host ? strdup(host) : NULL;
    free(c->proxy_user); c->proxy_user = user ? strdup(user) : NULL;
    free(c->proxy_pass); c->proxy_pass = pass ? strdup(pass) : NULL;
    c->proxy_port = port;
    return 0;
}

/* ══════════════════════════ Validation ══════════════════════════════════ */

/**
 * @brief Check that required fields are set.
 *
 * Checks: api_id != 0, api_hash set, session_name set,
 *         and either phone (USER mode) or bot_token (BOT mode) is set.
 * @param c       Config to validate.
 * @param out_err Optional buffer for human-readable error (may be NULL).
 * @param err_len Size of out_err buffer.
 * @return 0 if valid, -1 if invalid.
 */
// RU: Проверяет обязательные поля конфигурации.
int zsys_client_config_validate(const ZsysClientConfig *c,
                                char *out_err, size_t err_len) {
#define ERR(msg) do { \
    if (out_err && err_len > 0) snprintf(out_err, err_len, "%s", (msg)); \
    return -1; \
} while (0)

    if (!c)                    ERR("config is NULL");
    if (c->api_id == 0)        ERR("api_id is not set");
    if (!c->api_hash)          ERR("api_hash is not set");
    if (!c->session_name)      ERR("session_name is not set");
    if (c->mode == ZSYS_CLIENT_USER && !c->phone)
                               ERR("phone is required in USER mode");
    if (c->mode == ZSYS_CLIENT_BOT  && !c->bot_token)
                               ERR("bot_token is required in BOT mode");
    return 0;
#undef ERR
}

/* ══════════════════════════ Serialisation ═══════════════════════════════ */

/**
 * @brief Serialise config to JSON (bot_token and api_hash are NOT included).
 *        Caller must free() the result.
 * @param c Source config.
 * @return Heap-allocated JSON string, or NULL on failure.
 */
// RU: Сериализует конфигурацию в JSON (секреты НЕ включаются).
char *zsys_client_config_to_json(const ZsysClientConfig *c) {
    if (!c) return NULL;
    Buf b;
    if (!buf_init(&b, 512)) return NULL;

    char tmp[64];

    buf_writes(&b, "{");

    snprintf(tmp, sizeof(tmp), "%" PRId32, c->api_id);
    buf_writes(&b, "\"api_id\":"); buf_writes(&b, tmp);

    buf_writes(&b, ",\"session_name\":"); buf_json_str(&b, c->session_name);

    snprintf(tmp, sizeof(tmp), "%d", (int)c->mode);
    buf_writes(&b, ",\"mode\":"); buf_writes(&b, tmp);

    buf_writes(&b, ",\"phone\":"); buf_json_str(&b, c->phone);
    buf_writes(&b, ",\"device_model\":"); buf_json_str(&b, c->device_model);
    buf_writes(&b, ",\"system_version\":"); buf_json_str(&b, c->system_version);
    buf_writes(&b, ",\"app_version\":"); buf_json_str(&b, c->app_version);
    buf_writes(&b, ",\"lang_code\":"); buf_json_str(&b, c->lang_code);
    buf_writes(&b, ",\"lang_pack\":"); buf_json_str(&b, c->lang_pack);
    buf_writes(&b, ",\"proxy_host\":"); buf_json_str(&b, c->proxy_host);

    snprintf(tmp, sizeof(tmp), "%" PRId32, c->proxy_port);
    buf_writes(&b, ",\"proxy_port\":"); buf_writes(&b, tmp);

    buf_writes(&b, ",\"proxy_user\":"); buf_json_str(&b, c->proxy_user);

    snprintf(tmp, sizeof(tmp), "%d", c->sleep_threshold);
    buf_writes(&b, ",\"sleep_threshold\":"); buf_writes(&b, tmp);
    snprintf(tmp, sizeof(tmp), "%d", c->max_concurrent);
    buf_writes(&b, ",\"max_concurrent\":"); buf_writes(&b, tmp);

    buf_writec(&b, '}');
    return buf_finish(&b);
}

/**
 * @brief Deserialise config from JSON in-place.
 * @param c    Target config (must be zero-initialised or freed first).
 * @param json Flat JSON as produced by zsys_client_config_to_json().
 * @return 0 on success, -1 on parse error.
 */
// RU: Десериализует JSON в конфигурацию.
int zsys_client_config_from_json(ZsysClientConfig *c, const char *json) {
    if (!c || !json) return -1;

    char tmp[1024];
    int64_t v64;
    int32_t v32;
    int vi;

    if (json_read_i32(json, "api_id",          &v32) == 0) c->api_id = v32;
    if (json_read_i64(json, "mode",            &v64) == 0) c->mode   = (ZsysClientMode)v64;
    if (json_read_i32(json, "proxy_port",      &v32) == 0) c->proxy_port      = v32;
    if (json_read_int(json, "sleep_threshold", &vi)  == 0) c->sleep_threshold = vi;
    if (json_read_int(json, "max_concurrent",  &vi)  == 0) c->max_concurrent  = vi;

    if (json_read_str(json, "session_name",   tmp, sizeof(tmp)) == 0 && tmp[0])
        zsys_client_set_session_name(c, tmp);
    if (json_read_str(json, "phone",          tmp, sizeof(tmp)) == 0 && tmp[0])
        zsys_client_set_phone(c, tmp);
    if (json_read_str(json, "device_model",   tmp, sizeof(tmp)) == 0 && tmp[0])
        zsys_client_set_device_model(c, tmp);
    if (json_read_str(json, "system_version", tmp, sizeof(tmp)) == 0 && tmp[0])
        zsys_client_set_system_version(c, tmp);
    if (json_read_str(json, "app_version",    tmp, sizeof(tmp)) == 0 && tmp[0])
        zsys_client_set_app_version(c, tmp);
    if (json_read_str(json, "lang_code",      tmp, sizeof(tmp)) == 0 && tmp[0])
        zsys_client_set_lang_code(c, tmp);
    if (json_read_str(json, "lang_pack",      tmp, sizeof(tmp)) == 0 && tmp[0])
        zsys_client_set_lang_pack(c, tmp);
    if (json_read_str(json, "proxy_host",     tmp, sizeof(tmp)) == 0 && tmp[0])
        { free(c->proxy_host); c->proxy_host = strdup(tmp); }
    if (json_read_str(json, "proxy_user",     tmp, sizeof(tmp)) == 0 && tmp[0])
        { free(c->proxy_user); c->proxy_user = strdup(tmp); }

    return 0;
}
