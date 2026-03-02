/**
 * @file zsys_chat.c
 * @brief Universal C representation of a Telegram chat/channel/group — implementation.
 *
 * Flat JSON serialisation uses a minimal Buf helper (no external libs).
 * JSON parsing is a simple key-value extractor matching the output of to_json.
 */
// RU: Реализация ZsysChat. Сериализация через минимальный Buf без внешних библиотек.

#define _POSIX_C_SOURCE 200809L /* for strdup */

#include "zsys_chat.h"
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
 * @brief Allocate a new, zero-initialised ZsysChat on the heap.
 * @return Pointer to ZsysChat, or NULL on failure.
 */
// RU: Выделяет новый ZsysChat на куче, инициализированный нулями.
ZsysChat *zsys_chat_new(void) {
    ZsysChat *c = (ZsysChat *)calloc(1, sizeof(ZsysChat));
    if (c) c->member_count = -1; /* -1 = unknown by default */
    return c;
}

/**
 * @brief Free a heap-allocated ZsysChat and all its string fields.
 * @param c Pointer to ZsysChat (NULL-safe).
 */
// RU: Освобождает ZsysChat и все его строковые поля.
void zsys_chat_free(ZsysChat *c) {
    if (!c) return;
    free(c->title);
    free(c->username);
    free(c->description);
    free(c);
}

/**
 * @brief Shallow-copy src into dst (strings are strdup-ed).
 * @param dst Destination ZsysChat (must be zero-initialised or freed first).
 * @param src Source ZsysChat.
 * @return 0 on success, -1 on allocation failure.
 */
// RU: Копирует поля src в dst через strdup.
int zsys_chat_copy(ZsysChat *dst, const ZsysChat *src) {
    if (!dst || !src) return -1;
    dst->id            = src->id;
    dst->type          = src->type;
    dst->member_count  = src->member_count;
    dst->is_restricted = src->is_restricted;
    dst->is_scam       = src->is_scam;
    dst->created_at    = src->created_at;
    dst->title       = src->title       ? strdup(src->title)       : NULL;
    dst->username    = src->username    ? strdup(src->username)    : NULL;
    dst->description = src->description ? strdup(src->description) : NULL;
    return 0;
}

/* ══════════════════════════ Setters ═════════════════════════════════════ */

/**
 * @brief Set the numeric Telegram chat ID.
 * @param c  ZsysChat instance.
 * @param id Chat ID (int64, negative for groups/channels).
 */
// RU: Установить числовой Telegram chat ID.
void zsys_chat_set_id(ZsysChat *c, int64_t id) {
    if (!c) return;
    c->id = id;
}

/**
 * @brief Set the chat type.
 * @param c    ZsysChat instance.
 * @param type ZsysChatType enum value.
 */
// RU: Установить тип чата.
void zsys_chat_set_type(ZsysChat *c, ZsysChatType type) {
    if (!c) return;
    c->type = type;
}

/**
 * @brief Set the member count.
 * @param c     ZsysChat instance.
 * @param count Number of members.
 */
// RU: Установить количество участников.
void zsys_chat_set_member_count(ZsysChat *c, int32_t count) {
    if (!c) return;
    c->member_count = count;
}

/** @brief Set title (strdup). NULL clears the field. */
// RU: Установить title (strdup). NULL очищает поле.
int zsys_chat_set_title(ZsysChat *c, const char *val) {
    if (!c) return -1;
    free(c->title);
    c->title = val ? strdup(val) : NULL;
    return 0;
}

/** @brief Set username (strdup). NULL clears the field. */
// RU: Установить username (strdup). NULL очищает поле.
int zsys_chat_set_username(ZsysChat *c, const char *val) {
    if (!c) return -1;
    free(c->username);
    c->username = val ? strdup(val) : NULL;
    return 0;
}

/** @brief Set description (strdup). NULL clears the field. */
// RU: Установить description (strdup). NULL очищает поле.
int zsys_chat_set_description(ZsysChat *c, const char *val) {
    if (!c) return -1;
    free(c->description);
    c->description = val ? strdup(val) : NULL;
    return 0;
}

/* ══════════════════════════ Helpers ═════════════════════════════════════ */

/**
 * @brief Return a human-readable name for a ZsysChatType.
 * @param type ZsysChatType value.
 * @return Static string (do not free).
 */
// RU: Возвращает строковое имя типа чата (статическая строка).
const char *zsys_chat_type_str(ZsysChatType type) {
    switch (type) {
        case ZSYS_CHAT_PRIVATE:    return "private";
        case ZSYS_CHAT_GROUP:      return "group";
        case ZSYS_CHAT_SUPERGROUP: return "supergroup";
        case ZSYS_CHAT_CHANNEL:    return "channel";
        case ZSYS_CHAT_BOT:        return "bot";
        default:                   return "unknown";
    }
}

/* ══════════════════════════ Serialisation ═══════════════════════════════ */

/**
 * @brief Serialise ZsysChat to a flat JSON string.
 *        Caller must free() the result.
 * @param c Source ZsysChat.
 * @return Heap-allocated JSON string, or NULL on failure.
 */
// RU: Сериализует чат в JSON. Освободить через free().
char *zsys_chat_to_json(const ZsysChat *c) {
    if (!c) return NULL;
    Buf b;
    if (!buf_init(&b, 256)) return NULL;

    char tmp[64];

    buf_writes(&b, "{");

    snprintf(tmp, sizeof(tmp), "%" PRId64, c->id);
    buf_writes(&b, "\"id\":"); buf_writes(&b, tmp);

    snprintf(tmp, sizeof(tmp), "%d", (int)c->type);
    buf_writes(&b, ",\"type\":"); buf_writes(&b, tmp);

    buf_writes(&b, ",\"title\":"); buf_json_str(&b, c->title);
    buf_writes(&b, ",\"username\":"); buf_json_str(&b, c->username);
    buf_writes(&b, ",\"description\":"); buf_json_str(&b, c->description);

    snprintf(tmp, sizeof(tmp), "%" PRId32, c->member_count);
    buf_writes(&b, ",\"member_count\":"); buf_writes(&b, tmp);

    snprintf(tmp, sizeof(tmp), "%d", c->is_restricted);
    buf_writes(&b, ",\"is_restricted\":"); buf_writes(&b, tmp);
    snprintf(tmp, sizeof(tmp), "%d", c->is_scam);
    buf_writes(&b, ",\"is_scam\":"); buf_writes(&b, tmp);
    snprintf(tmp, sizeof(tmp), "%" PRId64, c->created_at);
    buf_writes(&b, ",\"created_at\":"); buf_writes(&b, tmp);

    buf_writec(&b, '}');
    return buf_finish(&b);
}

/**
 * @brief Deserialise ZsysChat from a flat JSON string in-place.
 * @param c    Target struct (must be zero-initialised or freed first).
 * @param json Flat JSON as produced by zsys_chat_to_json().
 * @return 0 on success, -1 on parse error.
 */
// RU: Десериализует JSON в ZsysChat.
int zsys_chat_from_json(ZsysChat *c, const char *json) {
    if (!c || !json) return -1;

    char tmp[4096];
    int64_t v64;
    int32_t v32;
    int vi;

    if (json_read_i64(json, "id",           &v64) == 0) c->id         = v64;
    if (json_read_i64(json, "created_at",   &v64) == 0) c->created_at = v64;
    if (json_read_i32(json, "type",         &v32) == 0) c->type       = (ZsysChatType)v32;
    if (json_read_i32(json, "member_count", &v32) == 0) c->member_count = v32;
    if (json_read_int(json, "is_restricted",&vi)  == 0) c->is_restricted = vi;
    if (json_read_int(json, "is_scam",      &vi)  == 0) c->is_scam      = vi;

    if (json_read_str(json, "title",       tmp, sizeof(tmp)) == 0 && tmp[0])
        zsys_chat_set_title(c, tmp);
    if (json_read_str(json, "username",    tmp, sizeof(tmp)) == 0 && tmp[0])
        zsys_chat_set_username(c, tmp);
    if (json_read_str(json, "description", tmp, sizeof(tmp)) == 0 && tmp[0])
        zsys_chat_set_description(c, tmp);

    return 0;
}
