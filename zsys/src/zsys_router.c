/**
 * @file zsys_router.c
 * @brief Trigger-to-handler-id hash table using open addressing with linear probing.
 *
 * Keys are stored normalized to lowercase. No external dependencies — only libc.
 * Thread-unsafe by design; add a mutex at the call site if concurrent access is needed.
 *
 * Typical usage: register command triggers ("alive", "ping") → integer handler IDs,
 * then perform O(1) lookup at message-dispatch time.
 */
// RU: Хэш-таблица триггер→handler_id на открытой адресации с линейным пробированием.
// RU: Ключи хранятся в нижнем регистре. Нет внешних зависимостей — только libc.

#define _POSIX_C_SOURCE 200809L /* for strdup */

#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "zsys_core.h"

/** Initial capacity of the hash table (must be a power of two). */
// RU: Начальная ёмкость хэш-таблицы (должна быть степенью двойки).
#define ROUTER_INIT_CAP 64

/**
 * @brief Single slot in the open-addressing hash table.
 *
 * `used` states:
 *   -  0 = empty (never written)
 *   -  1 = occupied
 *   - -1 = tombstone (deleted; probing must continue past it)
 */
// RU: Один слот хэш-таблицы. used: 0=пустой, 1=занят, -1=tombstone (удалён).
typedef struct RouterEntry {
    char *key;       /**< Lowercase trigger string (heap-allocated). */
    int   handler_id;/**< Opaque integer ID of the associated handler. */
    int   used;      /**< Slot state: 1=occupied, -1=tombstone, 0=empty. */
} RouterEntry;

/**
 * @brief Router instance — wraps the hash table and its metadata.
 */
// RU: Экземпляр роутера — хэш-таблица + метаданные размера.
struct ZsysRouter {
    RouterEntry *table; /**< Heap-allocated slot array. */
    size_t       cap;   /**< Total number of slots (always a power of two). */
    size_t       count; /**< Number of occupied (non-tombstone) entries. */
};

/**
 * @brief FNV-1a 32-bit hash for a NUL-terminated string.
 * @param s Input string.
 * @return  Hash value in range [0, SIZE_MAX].
 */
// RU: FNV-1a 32-битный хэш для строки, завершённой NUL.
static size_t fnv1a(const char *s) {
    size_t h = 2166136261u;
    while (*s) {
        h ^= (unsigned char)*s++;
        h *= 16777619u;
    }
    return h;
}

/**
 * @brief Lowercase-normalize src into dst buffer of size max.
 * @param dst Destination buffer (NUL-terminated on return).
 * @param src Source string.
 * @param max Size of dst including the terminating NUL.
 */
// RU: Копирует src в dst, приводя все символы к нижнему регистру.
static void to_lower_buf(char *dst, const char *src, size_t max) {
    size_t i = 0;
    for (; src[i] && i < max - 1; i++)
        dst[i] = (char)tolower((unsigned char)src[i]);
    dst[i] = '\0';
}

/**
 * @brief Allocate and initialize a new router with default capacity.
 * @return Pointer to ZsysRouter, or NULL on allocation failure.
 */
// RU: Создаёт новый роутер с начальной ёмкостью ROUTER_INIT_CAP.
ZsysRouter *zsys_router_new(void) {
    ZsysRouter *r = (ZsysRouter *)calloc(1, sizeof(ZsysRouter));
    if (!r) return NULL;
    r->cap   = ROUTER_INIT_CAP;
    r->count = 0;
    r->table = (RouterEntry *)calloc(r->cap, sizeof(RouterEntry));
    if (!r->table) { free(r); return NULL; }
    return r;
}

/**
 * @brief Free all memory owned by the router, including heap-copied keys.
 * @param r Router instance (NULL-safe).
 */
// RU: Освобождает всю память роутера, включая скопированные ключи.
void zsys_router_free(ZsysRouter *r) {
    if (!r) return;
    for (size_t i = 0; i < r->cap; i++)
        if (r->table[i].used == 1)
            free(r->table[i].key);
    free(r->table);
    free(r);
}

/**
 * @brief Rehash all live entries into a new table of size new_cap.
 *
 * Tombstones are discarded during rehash — they do not carry over.
 * @param r       Router to resize.
 * @param new_cap New capacity (must be a power of two > current count).
 * @return 0 on success, -1 on allocation failure.
 */
// RU: Перехэширует все живые записи в новую таблицу. Tombstone'ы отбрасываются.
static int router_resize(ZsysRouter *r, size_t new_cap) {
    RouterEntry *old     = r->table;
    size_t       old_cap = r->cap;
    RouterEntry *tbl     = (RouterEntry *)calloc(new_cap, sizeof(RouterEntry));
    if (!tbl) return -1;
    r->table = tbl;
    r->cap   = new_cap;
    r->count = 0;
    for (size_t i = 0; i < old_cap; i++) {
        if (old[i].used != 1) continue;
        size_t idx = fnv1a(old[i].key) & (new_cap - 1);
        while (tbl[idx].used == 1)
            idx = (idx + 1) & (new_cap - 1);
        tbl[idx] = old[i]; /* key ownership transferred */
        r->count++;
    }
    free(old);
    return 0;
}

/**
 * @brief Register a trigger string mapped to a handler ID.
 *
 * If the trigger already exists its handler_id is updated in place.
 * The table is grown automatically when load factor exceeds 0.7.
 * @param r          Router instance.
 * @param trigger    Command trigger string (case-insensitive, max 511 chars).
 * @param handler_id Opaque integer to associate with the trigger.
 * @return 0 on success, -1 on error (NULL args or allocation failure).
 */
// RU: Регистрирует триггер→handler_id. При превышении load factor 0.7 таблица растёт.
int zsys_router_add(ZsysRouter *r, const char *trigger, int handler_id) {
    if (!r || !trigger) return -1;
    /* Grow when load factor > 0.7. */
    // RU: Расширяем, если load factor превысил 0.7.
    if (r->count * 10 >= r->cap * 7) {
        if (router_resize(r, r->cap * 2) < 0) return -1;
    }
    char lc[512];
    to_lower_buf(lc, trigger, sizeof(lc));
    size_t idx        = fnv1a(lc) & (r->cap - 1);
    size_t first_tomb = (size_t)-1;
    for (size_t i = 0; i < r->cap; i++) {
        size_t pos = (idx + i) & (r->cap - 1);
        if (r->table[pos].used == 0) {
            size_t ins = (first_tomb != (size_t)-1) ? first_tomb : pos;
            r->table[ins].key        = strdup(lc);
            r->table[ins].handler_id = handler_id;
            r->table[ins].used       = 1;
            r->count++;
            return 0;
        }
        if (r->table[pos].used == -1) {
            if (first_tomb == (size_t)-1) first_tomb = pos;
            continue;
        }
        if (strcmp(r->table[pos].key, lc) == 0) {
            r->table[pos].handler_id = handler_id; /* update existing entry */
            // RU: Обновляем существующую запись.
            return 0;
        }
    }
    return -1;
}

/**
 * @brief Remove a trigger from the router (marks slot as tombstone).
 * @param r       Router instance.
 * @param trigger Trigger to remove (case-insensitive).
 * @return 0 if found and removed, -1 if not found or NULL args.
 */
// RU: Удаляет триггер из роутера (помечает слот как tombstone).
int zsys_router_remove(ZsysRouter *r, const char *trigger) {
    if (!r || !trigger) return -1;
    char lc[512];
    to_lower_buf(lc, trigger, sizeof(lc));
    size_t idx = fnv1a(lc) & (r->cap - 1);
    for (size_t i = 0; i < r->cap; i++) {
        size_t pos = (idx + i) & (r->cap - 1);
        if (r->table[pos].used == 0) return -1;
        if (r->table[pos].used == 1 && strcmp(r->table[pos].key, lc) == 0) {
            free(r->table[pos].key);
            r->table[pos].key  = NULL;
            r->table[pos].used = -1; /* tombstone */
            r->count--;
            return 0;
        }
    }
    return -1;
}

/**
 * @brief Look up a trigger and return its handler ID.
 *
 * Case-insensitive lookup; internally normalizes to lowercase.
 * @param r       Router instance.
 * @param trigger Trigger string to look up.
 * @return handler_id if found, -1 if not found or NULL args.
 */
// RU: Ищет триггер и возвращает handler_id. Поиск регистронезависимый.
int zsys_router_lookup(ZsysRouter *r, const char *trigger) {
    if (!r || !trigger) return -1;
    char lc[512];
    to_lower_buf(lc, trigger, sizeof(lc));
    size_t idx = fnv1a(lc) & (r->cap - 1);
    for (size_t i = 0; i < r->cap; i++) {
        size_t pos = (idx + i) & (r->cap - 1);
        if (r->table[pos].used == 0) return -1;
        if (r->table[pos].used == 1 && strcmp(r->table[pos].key, lc) == 0)
            return r->table[pos].handler_id;
    }
    return -1;
}

/**
 * @brief Return the number of live (non-tombstone) entries.
 * @param r Router instance (NULL-safe).
 * @return Entry count, or 0 for NULL router.
 */
// RU: Возвращает количество живых записей (без tombstone).
size_t zsys_router_count(ZsysRouter *r) {
    return r ? r->count : 0;
}

/**
 * @brief Remove all entries from the router without deallocating the table.
 *
 * After this call the router is empty and ready for re-use without a full
 * free/new cycle.
 * @param r Router instance (NULL-safe).
 */
// RU: Очищает роутер (удаляет все записи) без освобождения самой таблицы.
void zsys_router_clear(ZsysRouter *r) {
    if (!r) return;
    for (size_t i = 0; i < r->cap; i++) {
        if (r->table[i].used == 1)
            free(r->table[i].key);
        r->table[i].key  = NULL;
        r->table[i].used = 0;
    }
    r->count = 0;
}
