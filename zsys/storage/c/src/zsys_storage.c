/**
 * @file zsys_storage.c
 * @brief Abstract in-memory key-value storage — open-addressing hash table implementation.
 *
 * Keys and values are NUL-terminated strings. Open addressing with linear probing
 * and tombstones. Grows (doubles) when load factor exceeds 70%. Initial default
 * capacity is 16 (power-of-two). No external dependencies.
 */
// RU: Хранилище ключ-значение на основе хэш-таблицы открытой адресации.
// RU: Линейное пробирование + tombstone. Рост при load > 70%. Только libc.

#define _POSIX_C_SOURCE 200809L /* for strdup */

#include "zsys_storage.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* ══════════════════════════ Constants ═══════════════════════════════════ */

/** Default initial capacity (power of two). */
// RU: Начальная ёмкость по умолчанию (степень двойки).
#define KV_DEFAULT_CAP 16

/* ══════════════════════════ Internal types ══════════════════════════════ */

/**
 * @brief Single slot in the open-addressing hash table.
 *
 * used: 0 = empty, 1 = occupied, -1 = tombstone (deleted).
 */
// RU: Один слот хэш-таблицы. used: 0=пустой, 1=занят, -1=tombstone.
typedef struct KVEntry {
    char *key;   /**< Heap-allocated key string. */
    char *value; /**< Heap-allocated value string. */
    int   used;  /**< Slot state. */
} KVEntry;

/**
 * @brief ZsysKV — opaque key-value store backed by an open-addressing hash table.
 */
// RU: Непрозрачная структура хранилища КВ.
struct ZsysKV {
    KVEntry *table; /**< Heap-allocated slot array. */
    size_t   cap;   /**< Total slots (always a power of two). */
    size_t   count; /**< Number of live (non-tombstone) entries. */
};

/* ══════════════════════════ Internal helpers ════════════════════════════ */

/**
 * @brief FNV-1a 32-bit hash for a NUL-terminated string.
 * @param s Input string.
 * @return  Hash value.
 */
// RU: FNV-1a 32-битный хэш строки.
static size_t kv_hash(const char *s) {
    size_t h = 2166136261u;
    while (*s) { h ^= (unsigned char)*s++; h *= 16777619u; }
    return h;
}

/**
 * @brief Round n up to the nearest power of two (minimum KV_DEFAULT_CAP).
 * @param n Requested capacity.
 * @return  Power-of-two capacity >= n and >= KV_DEFAULT_CAP.
 */
// RU: Округлить n вверх до ближайшей степени двойки (мин. KV_DEFAULT_CAP).
static size_t next_pow2(size_t n) {
    if (n < KV_DEFAULT_CAP) return KV_DEFAULT_CAP;
    size_t p = 1;
    while (p < n) p <<= 1;
    return p;
}

/**
 * @brief Rehash all live entries into a new table of new_cap slots.
 *        Tombstones are discarded during rehash.
 * @param kv      KV store to resize.
 * @param new_cap New capacity (power of two).
 * @return 0 on success, -1 on allocation failure.
 */
// RU: Перехэшировать все живые записи в новую таблицу. Tombstone'ы отбрасываются.
static int kv_resize(ZsysKV *kv, size_t new_cap) {
    KVEntry *old     = kv->table;
    size_t   old_cap = kv->cap;
    KVEntry *tbl     = (KVEntry *)calloc(new_cap, sizeof(KVEntry));
    if (!tbl) return -1;
    kv->table = tbl;
    kv->cap   = new_cap;
    kv->count = 0;
    for (size_t i = 0; i < old_cap; i++) {
        if (old[i].used != 1) continue;
        size_t idx = kv_hash(old[i].key) & (new_cap - 1);
        while (tbl[idx].used == 1)
            idx = (idx + 1) & (new_cap - 1);
        tbl[idx] = old[i]; /* key/value ownership transferred */
        kv->count++;
    }
    free(old);
    return 0;
}

/* ══════════════════════════ Buf helper (for to_json) ════════════════════ */

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

/* ══════════════════════════ Lifecycle ═══════════════════════════════════ */

/**
 * @brief Create a new, empty KV store.
 * @param initial_cap Initial capacity (0 → default 16). Rounded up to power-of-two.
 * @return Heap-allocated ZsysKV, or NULL on failure.
 */
// RU: Создаёт пустое хранилище КВ. capacity=0 → по умолчанию 16 слотов.
ZsysKV *zsys_kv_new(size_t initial_cap) {
    ZsysKV *kv = (ZsysKV *)calloc(1, sizeof(ZsysKV));
    if (!kv) return NULL;
    kv->cap   = next_pow2(initial_cap ? initial_cap : KV_DEFAULT_CAP);
    kv->count = 0;
    kv->table = (KVEntry *)calloc(kv->cap, sizeof(KVEntry));
    if (!kv->table) { free(kv); return NULL; }
    return kv;
}

/**
 * @brief Free a ZsysKV and all keys/values it owns.
 * @param kv KV store handle (NULL-safe).
 */
// RU: Освобождает хранилище и все ключи/значения.
void zsys_kv_free(ZsysKV *kv) {
    if (!kv) return;
    for (size_t i = 0; i < kv->cap; i++) {
        if (kv->table[i].used == 1) {
            free(kv->table[i].key);
            free(kv->table[i].value);
        }
    }
    free(kv->table);
    free(kv);
}

/* ══════════════════════════ Operations ══════════════════════════════════ */

/**
 * @brief Insert or update a key-value pair.
 *
 * Both key and value are strdup-ed; caller retains ownership.
 * The table doubles when load factor exceeds 70%.
 * @param kv    KV store handle.
 * @param key   Key string (NUL-terminated).
 * @param value Value string (NUL-terminated).
 * @return 0 on success, -1 on allocation failure.
 */
// RU: Вставить или обновить пару ключ-значение.
int zsys_kv_set(ZsysKV *kv, const char *key, const char *value) {
    if (!kv || !key || !value) return -1;

    /* Grow when load factor > 70%. */
    // RU: Расширяем при load factor > 70%.
    if (kv->count * 10 >= kv->cap * 7) {
        if (kv_resize(kv, kv->cap * 2) < 0) return -1;
    }

    size_t idx        = kv_hash(key) & (kv->cap - 1);
    size_t first_tomb = (size_t)-1;

    for (size_t i = 0; i < kv->cap; i++) {
        size_t pos = (idx + i) & (kv->cap - 1);
        if (kv->table[pos].used == 0) {
            /* Empty slot — insert here (or at first tombstone). */
            // RU: Пустой слот — вставляем (или в первый tombstone).
            size_t ins = (first_tomb != (size_t)-1) ? first_tomb : pos;
            kv->table[ins].key   = strdup(key);
            kv->table[ins].value = strdup(value);
            if (!kv->table[ins].key || !kv->table[ins].value) {
                free(kv->table[ins].key);
                free(kv->table[ins].value);
                kv->table[ins].key = kv->table[ins].value = NULL;
                kv->table[ins].used = 0;
                return -1;
            }
            kv->table[ins].used = 1;
            kv->count++;
            return 0;
        }
        if (kv->table[pos].used == -1) {
            /* Tombstone — record first one for potential insertion. */
            // RU: Tombstone — запоминаем для возможной вставки.
            if (first_tomb == (size_t)-1) first_tomb = pos;
            continue;
        }
        if (strcmp(kv->table[pos].key, key) == 0) {
            /* Update existing entry. */
            // RU: Обновляем существующую запись.
            char *nv = strdup(value);
            if (!nv) return -1;
            free(kv->table[pos].value);
            kv->table[pos].value = nv;
            return 0;
        }
    }
    return -1; /* table full — should not happen if resize works */
}

/**
 * @brief Look up a value by key.
 * @param kv  KV store handle.
 * @param key Key to look up.
 * @return Internal pointer to value string, or NULL if not found.
 */
// RU: Получить значение по ключу. NULL если нет. Указатель до следующего set/del.
const char *zsys_kv_get(ZsysKV *kv, const char *key) {
    if (!kv || !key) return NULL;
    size_t idx = kv_hash(key) & (kv->cap - 1);
    for (size_t i = 0; i < kv->cap; i++) {
        size_t pos = (idx + i) & (kv->cap - 1);
        if (kv->table[pos].used == 0) return NULL;
        if (kv->table[pos].used == 1 && strcmp(kv->table[pos].key, key) == 0)
            return kv->table[pos].value;
    }
    return NULL;
}

/**
 * @brief Delete a key-value pair (marks slot as tombstone).
 * @param kv  KV store handle.
 * @param key Key to delete.
 * @return 0 if found and deleted, -1 if key not found.
 */
// RU: Удалить пару по ключу. -1 если ключ не найден.
int zsys_kv_del(ZsysKV *kv, const char *key) {
    if (!kv || !key) return -1;
    size_t idx = kv_hash(key) & (kv->cap - 1);
    for (size_t i = 0; i < kv->cap; i++) {
        size_t pos = (idx + i) & (kv->cap - 1);
        if (kv->table[pos].used == 0) return -1;
        if (kv->table[pos].used == 1 && strcmp(kv->table[pos].key, key) == 0) {
            free(kv->table[pos].key);
            free(kv->table[pos].value);
            kv->table[pos].key   = NULL;
            kv->table[pos].value = NULL;
            kv->table[pos].used  = -1; /* tombstone */
            kv->count--;
            return 0;
        }
    }
    return -1;
}

/**
 * @brief Check if a key exists.
 * @param kv  KV store handle.
 * @param key Key to check.
 * @return 1 if exists, 0 otherwise.
 */
// RU: Проверить наличие ключа.
int zsys_kv_has(ZsysKV *kv, const char *key) {
    return zsys_kv_get(kv, key) != NULL ? 1 : 0;
}

/**
 * @brief Return the number of entries in the store.
 * @param kv KV store handle (NULL-safe).
 * @return Entry count.
 */
// RU: Количество пар в хранилище.
size_t zsys_kv_count(ZsysKV *kv) {
    return kv ? kv->count : 0;
}

/**
 * @brief Remove all entries from the store without deallocating the table.
 * @param kv KV store handle (NULL-safe).
 */
// RU: Очистить хранилище без освобождения самой таблицы.
void zsys_kv_clear(ZsysKV *kv) {
    if (!kv) return;
    for (size_t i = 0; i < kv->cap; i++) {
        if (kv->table[i].used == 1) {
            free(kv->table[i].key);
            free(kv->table[i].value);
        }
        kv->table[i].key   = NULL;
        kv->table[i].value = NULL;
        kv->table[i].used  = 0;
    }
    kv->count = 0;
}

/**
 * @brief Iterate over all key-value pairs in undefined order.
 *
 * Calls fn(key, value, ctx) for each live pair.
 * Stops if fn returns non-zero.
 * @param kv  KV store handle (NULL-safe).
 * @param fn  Callback function.
 * @param ctx User-supplied context pointer.
 */
// RU: Обойти все пары. Останавливается если fn вернула не 0.
void zsys_kv_foreach(ZsysKV *kv, ZsysKVIterFn fn, void *ctx) {
    if (!kv || !fn) return;
    for (size_t i = 0; i < kv->cap; i++) {
        if (kv->table[i].used == 1) {
            if (fn(kv->table[i].key, kv->table[i].value, ctx) != 0)
                return;
        }
    }
}

/* ══════════════════════════ Serialisation ═══════════════════════════════ */

/**
 * @brief Serialise the entire store to a flat JSON object string.
 *        Caller must free() the result.
 * @param kv KV store handle.
 * @return JSON string like {"key1":"val1","key2":"val2"}, or NULL on failure.
 */
// RU: Сериализует всё хранилище в JSON-объект. Освободить через free().
char *zsys_kv_to_json(ZsysKV *kv) {
    if (!kv) return NULL;
    Buf b;
    if (!buf_init(&b, 64 + kv->count * 32)) return NULL;

    buf_writec(&b, '{');
    int first = 1;
    for (size_t i = 0; i < kv->cap; i++) {
        if (kv->table[i].used != 1) continue;
        if (!first) buf_writec(&b, ',');
        first = 0;
        buf_json_str(&b, kv->table[i].key);
        buf_writec(&b, ':');
        buf_json_str(&b, kv->table[i].value);
    }
    buf_writec(&b, '}');
    return buf_finish(&b);
}

/**
 * @brief Deserialise a flat JSON object and merge into an existing store.
 *        Existing keys are overwritten.
 * @param kv   KV store handle.
 * @param json Flat JSON string as produced by zsys_kv_to_json().
 * @return 0 on success, -1 on parse or allocation error.
 */
// RU: Десериализует JSON в хранилище (мерджит с существующим).
int zsys_kv_from_json(ZsysKV *kv, const char *json) {
    if (!kv || !json) return -1;

    const char *p = json;
    /* Advance to '{'. */
    // RU: Пропускаем до открывающей '{'.
    while (*p && *p != '{') p++;
    if (!*p) return -1;
    p++;

    char key[1024];
    char val[8192];

    while (*p) {
        /* Skip whitespace and commas. */
        // RU: Пропускаем пробелы и запятые.
        while (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r' || *p == ',') p++;
        if (*p == '}' || !*p) break;
        if (*p != '"') { p++; continue; }
        p++;

        /* Read key. */
        // RU: Читаем ключ.
        int ki = 0;
        while (*p && *p != '"' && ki < (int)sizeof(key) - 1) {
            if (*p == '\\') {
                p++;
                if      (*p == 'n')  { key[ki++] = '\n'; p++; }
                else if (*p == 't')  { key[ki++] = '\t'; p++; }
                else if (*p == 'r')  { key[ki++] = '\r'; p++; }
                else if (*p == '"')  { key[ki++] = '"';  p++; }
                else if (*p == '\\') { key[ki++] = '\\'; p++; }
                else if (*p)         { key[ki++] = *p++;      }
            } else {
                key[ki++] = *p++;
            }
        }
        key[ki] = '\0';
        if (*p == '"') p++;

        /* Skip whitespace then colon. */
        // RU: Пропускаем пробелы и двоеточие.
        while (*p == ' ' || *p == '\t') p++;
        if (*p != ':') continue;
        p++;
        while (*p == ' ' || *p == '\t') p++;

        /* Skip non-string values. */
        // RU: Пропускаем не-строковые значения.
        if (*p != '"') {
            while (*p && *p != ',' && *p != '}') p++;
            continue;
        }
        p++;

        /* Read value. */
        // RU: Читаем значение.
        int vi = 0;
        while (*p && *p != '"' && vi < (int)sizeof(val) - 1) {
            if (*p == '\\') {
                p++;
                if      (*p == 'n')  { val[vi++] = '\n'; p++; }
                else if (*p == 't')  { val[vi++] = '\t'; p++; }
                else if (*p == 'r')  { val[vi++] = '\r'; p++; }
                else if (*p == '"')  { val[vi++] = '"';  p++; }
                else if (*p == '\\') { val[vi++] = '\\'; p++; }
                else if (*p)         { val[vi++] = *p++;      }
            } else {
                val[vi++] = *p++;
            }
        }
        val[vi] = '\0';
        if (*p == '"') p++;

        if (ki > 0 && zsys_kv_set(kv, key, val) < 0)
            return -1;
    }

    return 0;
}
