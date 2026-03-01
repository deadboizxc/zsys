/*
 * zsys_router.c — trigger → handler_id hash table (open addressing, linear probing).
 *
 * Keys are stored lowercase. No external dependencies (only libc).
 * Thread-unsafe by design (add locking at caller level if needed).
 */

#define _POSIX_C_SOURCE 200809L /* for strdup */

#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "zsys_core.h"

#define ROUTER_INIT_CAP 64

typedef struct RouterEntry {
    char *key;       /* lowercase trigger (heap-allocated) */
    int   handler_id;
    int   used;      /* 1 = occupied, -1 = tombstone, 0 = empty */
} RouterEntry;

struct ZsysRouter {
    RouterEntry *table;
    size_t       cap;
    size_t       count;
};

/* FNV-1a 32-bit hash */
static size_t fnv1a(const char *s) {
    size_t h = 2166136261u;
    while (*s) {
        h ^= (unsigned char)*s++;
        h *= 16777619u;
    }
    return h;
}

static void to_lower_buf(char *dst, const char *src, size_t max) {
    size_t i = 0;
    for (; src[i] && i < max - 1; i++)
        dst[i] = (char)tolower((unsigned char)src[i]);
    dst[i] = '\0';
}

ZsysRouter *zsys_router_new(void) {
    ZsysRouter *r = (ZsysRouter *)calloc(1, sizeof(ZsysRouter));
    if (!r) return NULL;
    r->cap   = ROUTER_INIT_CAP;
    r->count = 0;
    r->table = (RouterEntry *)calloc(r->cap, sizeof(RouterEntry));
    if (!r->table) { free(r); return NULL; }
    return r;
}

void zsys_router_free(ZsysRouter *r) {
    if (!r) return;
    for (size_t i = 0; i < r->cap; i++)
        if (r->table[i].used == 1)
            free(r->table[i].key);
    free(r->table);
    free(r);
}

/* Rehash to new_cap (must be a power of two larger than current count). */
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

int zsys_router_add(ZsysRouter *r, const char *trigger, int handler_id) {
    if (!r || !trigger) return -1;
    /* grow when load factor > 0.7 */
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
            r->table[pos].handler_id = handler_id; /* update */
            return 0;
        }
    }
    return -1;
}

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

/* Returns handler_id, or -1 if not found. Trigger is case-insensitive. */
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

size_t zsys_router_count(ZsysRouter *r) {
    return r ? r->count : 0;
}

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
