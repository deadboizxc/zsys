/**
 * @file zsys_user.c
 * @brief Universal C representation of a Telegram user / account — implementation.
 *
 * Flat JSON serialisation uses a minimal Buf helper (no external libs).
 * JSON parsing is a simple key-value extractor matching the output of to_json.
 */
// RU: Реализация ZsysUser. Сериализация через минимальный Buf без внешних библиотек.

#define _POSIX_C_SOURCE 200809L /* for strdup */

#include "zsys_user.h"
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

/* Extract an int value for "key" from flat JSON. */
// RU: Извлечь целое значение по ключу из плоского JSON.
static int json_read_int(const char *json, const char *key, int *out) {
    int64_t v;
    if (json_read_i64(json, key, &v) < 0) return -1;
    *out = (int)v;
    return 0;
}

/* ══════════════════════════ Lifecycle ═══════════════════════════════════ */

/**
 * @brief Allocate a new, zero-initialised ZsysUser on the heap.
 * @return Pointer to ZsysUser, or NULL on allocation failure.
 */
// RU: Выделяет новый ZsysUser на куче, инициализированный нулями.
ZsysUser *zsys_user_new(void) {
    return (ZsysUser *)calloc(1, sizeof(ZsysUser));
}

/**
 * @brief Free a heap-allocated ZsysUser and all its string fields.
 * @param u Pointer to ZsysUser (NULL-safe).
 */
// RU: Освобождает ZsysUser и все его строковые поля.
void zsys_user_free(ZsysUser *u) {
    if (!u) return;
    free(u->username);
    free(u->first_name);
    free(u->last_name);
    free(u->phone);
    free(u->lang_code);
    free(u);
}

/**
 * @brief Shallow-copy src into dst (strings are strdup-ed).
 * @param dst Destination ZsysUser (must be zero-initialised or freed first).
 * @param src Source ZsysUser.
 * @return 0 on success, -1 on allocation failure.
 */
// RU: Копирует поля src в dst (строки через strdup).
int zsys_user_copy(ZsysUser *dst, const ZsysUser *src) {
    if (!dst || !src) return -1;
    dst->id         = src->id;
    dst->is_bot     = src->is_bot;
    dst->is_premium = src->is_premium;
    dst->created_at = src->created_at;
    dst->username   = src->username   ? strdup(src->username)   : NULL;
    dst->first_name = src->first_name ? strdup(src->first_name) : NULL;
    dst->last_name  = src->last_name  ? strdup(src->last_name)  : NULL;
    dst->phone      = src->phone      ? strdup(src->phone)      : NULL;
    dst->lang_code  = src->lang_code  ? strdup(src->lang_code)  : NULL;
    return 0;
}

/* ══════════════════════════ Setters ═════════════════════════════════════ */

/**
 * @brief Set the numeric Telegram user ID.
 * @param u   ZsysUser instance.
 * @param id  Telegram user ID (int64).
 * @return 0 on success, -1 if u is NULL.
 */
// RU: Установить числовой Telegram ID пользователя.
void zsys_user_set_id(ZsysUser *u, int64_t id) {
    if (!u) return;
    u->id = id;
}

/**
 * @brief Set the is_bot flag.
 * @param u      ZsysUser instance.
 * @param is_bot Non-zero for bot accounts.
 */
// RU: Установить флаг бота.
void zsys_user_set_is_bot(ZsysUser *u, int is_bot) {
    if (!u) return;
    u->is_bot = is_bot ? 1 : 0;
}

/**
 * @brief Set account creation timestamp.
 * @param u  ZsysUser instance.
 * @param ts Unix timestamp.
 */
// RU: Установить временную метку создания аккаунта.
void zsys_user_set_created_at(ZsysUser *u, int64_t ts) {
    if (!u) return;
    u->created_at = ts;
}

/** @brief Set username (strdup). NULL clears the field. */
// RU: Установить username (strdup). NULL очищает поле.
int zsys_user_set_username(ZsysUser *u, const char *val) {
    if (!u) return -1;
    free(u->username);
    u->username = val ? strdup(val) : NULL;
    return 0;
}

/** @brief Set first_name (strdup). */
// RU: Установить first_name (strdup).
int zsys_user_set_first_name(ZsysUser *u, const char *val) {
    if (!u) return -1;
    free(u->first_name);
    u->first_name = val ? strdup(val) : NULL;
    return 0;
}

/** @brief Set last_name (strdup). NULL clears the field. */
// RU: Установить last_name (strdup). NULL очищает поле.
int zsys_user_set_last_name(ZsysUser *u, const char *val) {
    if (!u) return -1;
    free(u->last_name);
    u->last_name = val ? strdup(val) : NULL;
    return 0;
}

/** @brief Set phone (strdup). NULL clears the field. */
// RU: Установить phone (strdup). NULL очищает поле.
int zsys_user_set_phone(ZsysUser *u, const char *val) {
    if (!u) return -1;
    free(u->phone);
    u->phone = val ? strdup(val) : NULL;
    return 0;
}

/** @brief Set lang_code (strdup). NULL clears the field. */
// RU: Установить lang_code (strdup). NULL очищает поле.
int zsys_user_set_lang_code(ZsysUser *u, const char *val) {
    if (!u) return -1;
    free(u->lang_code);
    u->lang_code = val ? strdup(val) : NULL;
    return 0;
}

/* ══════════════════════════ Serialisation ═══════════════════════════════ */

/**
 * @brief Serialise ZsysUser to a flat JSON string.
 *        Caller must free() the result.
 * @param u Source ZsysUser.
 * @return Heap-allocated JSON string, or NULL on failure.
 */
// RU: Сериализует пользователя в JSON-строку. Освободить через free().
char *zsys_user_to_json(const ZsysUser *u) {
    if (!u) return NULL;
    Buf b;
    if (!buf_init(&b, 256)) return NULL;

    char tmp[64];

    buf_writes(&b, "{");

    snprintf(tmp, sizeof(tmp), "%" PRId64, u->id);
    buf_writes(&b, "\"id\":"); buf_writes(&b, tmp);

    buf_writes(&b, ",\"username\":"); buf_json_str(&b, u->username);
    buf_writes(&b, ",\"first_name\":"); buf_json_str(&b, u->first_name ? u->first_name : "");
    buf_writes(&b, ",\"last_name\":"); buf_json_str(&b, u->last_name);
    buf_writes(&b, ",\"phone\":"); buf_json_str(&b, u->phone);
    buf_writes(&b, ",\"lang_code\":"); buf_json_str(&b, u->lang_code);

    snprintf(tmp, sizeof(tmp), "%d", u->is_bot);
    buf_writes(&b, ",\"is_bot\":"); buf_writes(&b, tmp);
    snprintf(tmp, sizeof(tmp), "%d", u->is_premium);
    buf_writes(&b, ",\"is_premium\":"); buf_writes(&b, tmp);
    snprintf(tmp, sizeof(tmp), "%" PRId64, u->created_at);
    buf_writes(&b, ",\"created_at\":"); buf_writes(&b, tmp);

    buf_writec(&b, '}');
    return buf_finish(&b);
}

/**
 * @brief Deserialise ZsysUser from a flat JSON string in-place.
 * @param u    Target struct (must be zero-initialised or freed first).
 * @param json Flat JSON as produced by zsys_user_to_json().
 * @return 0 on success, -1 on parse error.
 */
// RU: Десериализует JSON в ZsysUser на месте.
int zsys_user_from_json(ZsysUser *u, const char *json) {
    if (!u || !json) return -1;

    char tmp[1024];
    int64_t v64;
    int vi;

    if (json_read_i64(json, "id", &v64)         == 0) u->id         = v64;
    if (json_read_i64(json, "created_at", &v64) == 0) u->created_at = v64;
    if (json_read_int(json, "is_bot", &vi)      == 0) u->is_bot     = vi;
    if (json_read_int(json, "is_premium", &vi)  == 0) u->is_premium = vi;

    if (json_read_str(json, "username",   tmp, sizeof(tmp)) == 0 && tmp[0])
        zsys_user_set_username(u, tmp);
    if (json_read_str(json, "first_name", tmp, sizeof(tmp)) == 0)
        zsys_user_set_first_name(u, tmp);
    if (json_read_str(json, "last_name",  tmp, sizeof(tmp)) == 0 && tmp[0])
        zsys_user_set_last_name(u, tmp);
    if (json_read_str(json, "phone",      tmp, sizeof(tmp)) == 0 && tmp[0])
        zsys_user_set_phone(u, tmp);
    if (json_read_str(json, "lang_code",  tmp, sizeof(tmp)) == 0 && tmp[0])
        zsys_user_set_lang_code(u, tmp);

    return 0;
}
