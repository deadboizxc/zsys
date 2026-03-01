/*
 * zsys_i18n.c — lightweight i18n: flat JSON loader + hash-table key→value store.
 *
 * Supports multiple language codes. Only parses flat {"key":"value"} JSON
 * (no nesting, no arrays) for maximum speed.
 * No external dependencies (only libc).
 */

#define _POSIX_C_SOURCE 200809L /* for strdup */

#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>
#include "zsys_core.h"

#define I18N_INIT_CAP 256

/* Single key→value entry in an open-addressing hash table. */
typedef struct I18nEntry {
    char *key;
    char *value;
    int   used; /* 1 = occupied, 0 = empty */
} I18nEntry;

/* Per-language hash table. */
typedef struct LangTable {
    char      lang_code[32];
    I18nEntry *ht;
    size_t     ht_cap;
    size_t     count;
    struct LangTable *next; /* singly-linked list of languages */
} LangTable;

struct ZsysI18n {
    LangTable *langs;
    char       active_lang[32];
};

/* FNV-1a 32-bit hash */
static size_t i18n_hash(const char *s, size_t cap) {
    size_t h = 2166136261u;
    while (*s) { h ^= (unsigned char)*s++; h *= 16777619u; }
    return h & (cap - 1);
}

static LangTable *lang_find(ZsysI18n *i, const char *code) {
    for (LangTable *l = i->langs; l; l = l->next)
        if (strcmp(l->lang_code, code) == 0) return l;
    return NULL;
}

static LangTable *lang_new(const char *code) {
    LangTable *l = (LangTable *)calloc(1, sizeof(LangTable));
    if (!l) return NULL;
    strncpy(l->lang_code, code, sizeof(l->lang_code) - 1);
    l->ht_cap = I18N_INIT_CAP;
    l->ht     = (I18nEntry *)calloc(l->ht_cap, sizeof(I18nEntry));
    if (!l->ht) { free(l); return NULL; }
    return l;
}

static void lang_free(LangTable *l) {
    for (size_t i = 0; i < l->ht_cap; i++) {
        if (l->ht[i].used) {
            free(l->ht[i].key);
            free(l->ht[i].value);
        }
    }
    free(l->ht);
    free(l);
}

/* Insert or update key→value in a LangTable. */
static int lang_set(LangTable *l, const char *key, const char *value) {
    /* Grow when load > 70% */
    if (l->count * 10 >= l->ht_cap * 7) {
        size_t     new_cap = l->ht_cap * 2;
        I18nEntry *nt      = (I18nEntry *)calloc(new_cap, sizeof(I18nEntry));
        if (!nt) return -1;
        for (size_t i = 0; i < l->ht_cap; i++) {
            if (!l->ht[i].used) continue;
            size_t pos = i18n_hash(l->ht[i].key, new_cap);
            while (nt[pos].used) pos = (pos + 1) & (new_cap - 1);
            nt[pos] = l->ht[i];
        }
        free(l->ht);
        l->ht     = nt;
        l->ht_cap = new_cap;
    }
    size_t pos = i18n_hash(key, l->ht_cap);
    for (size_t i = 0; i < l->ht_cap; i++) {
        size_t p = (pos + i) & (l->ht_cap - 1);
        if (!l->ht[p].used) {
            l->ht[p].key   = strdup(key);
            l->ht[p].value = strdup(value);
            l->ht[p].used  = 1;
            l->count++;
            return 0;
        }
        if (strcmp(l->ht[p].key, key) == 0) {
            free(l->ht[p].value);
            l->ht[p].value = strdup(value);
            return 0;
        }
    }
    return -1;
}

/* Returns pointer to internal value string, or NULL if not found. */
static const char *lang_get(LangTable *l, const char *key) {
    size_t pos = i18n_hash(key, l->ht_cap);
    for (size_t i = 0; i < l->ht_cap; i++) {
        size_t p = (pos + i) & (l->ht_cap - 1);
        if (!l->ht[p].used) return NULL; /* empty slot → not present */
        if (strcmp(l->ht[p].key, key) == 0) return l->ht[p].value;
    }
    return NULL;
}

/* ── minimal flat JSON parser ─────────────────────────────────────────────
 * Handles only: {"key":"value", ...}
 * Supports basic escape sequences: \n \t \r \" \\ and any \X → X.
 * Skips non-string values (numbers, booleans, null).
 */
static int parse_flat_json(LangTable *lt, const char *json_path) {
    FILE *f = fopen(json_path, "rb");
    if (!f) return -1;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (sz <= 0) { fclose(f); return -1; }
    char *buf = (char *)malloc((size_t)sz + 1);
    if (!buf) { fclose(f); return -1; }
    fread(buf, 1, (size_t)sz, f);
    fclose(f);
    buf[sz] = '\0';

    const char *p = buf;
    /* Skip to opening '{' */
    while (*p && *p != '{') p++;
    if (!*p) { free(buf); return -1; }
    p++; /* skip '{' */

    char key[1024];
    char val[8192];

    while (*p) {
        /* skip whitespace and commas */
        while (*p && (isspace((unsigned char)*p) || *p == ',')) p++;
        if (*p == '}' || !*p) break;
        if (*p != '"') { p++; continue; } /* unexpected token, skip */

        /* read key string */
        p++;
        int ki = 0;
        while (*p && *p != '"' && ki < (int)sizeof(key) - 1) {
            if (*p == '\\') {
                p++;
                if (*p) key[ki++] = *p++;
            } else {
                key[ki++] = *p++;
            }
        }
        key[ki] = '\0';
        if (*p == '"') p++;

        /* skip to ':' */
        while (*p && isspace((unsigned char)*p)) p++;
        if (*p != ':') continue;
        p++;
        while (*p && isspace((unsigned char)*p)) p++;

        /* only handle string values */
        if (*p != '"') {
            while (*p && *p != ',' && *p != '}') p++;
            continue;
        }
        p++; /* skip opening '"' */

        int vi = 0;
        while (*p && *p != '"' && vi < (int)sizeof(val) - 1) {
            if (*p == '\\') {
                p++;
                switch (*p) {
                    case 'n':  val[vi++] = '\n'; p++; break;
                    case 't':  val[vi++] = '\t'; p++; break;
                    case 'r':  val[vi++] = '\r'; p++; break;
                    default:   if (*p) val[vi++] = *p++; break;
                }
            } else {
                val[vi++] = *p++;
            }
        }
        val[vi] = '\0';
        if (*p == '"') p++;

        lang_set(lt, key, val);
    }

    free(buf);
    return 0;
}

/* ── public API ───────────────────────────────────────────────────────────── */

ZsysI18n *zsys_i18n_new(void) {
    return (ZsysI18n *)calloc(1, sizeof(ZsysI18n));
}

void zsys_i18n_free(ZsysI18n *i) {
    if (!i) return;
    LangTable *l = i->langs;
    while (l) {
        LangTable *next = l->next;
        lang_free(l);
        l = next;
    }
    free(i);
}

int zsys_i18n_load_json(ZsysI18n *i, const char *lang_code,
                         const char *json_path) {
    if (!i || !lang_code || !json_path) return -1;
    LangTable *lt = lang_find(i, lang_code);
    if (!lt) {
        lt = lang_new(lang_code);
        if (!lt) return -1;
        lt->next = i->langs;
        i->langs = lt;
    }
    return parse_flat_json(lt, json_path);
}

void zsys_i18n_set_lang(ZsysI18n *i, const char *lang_code) {
    if (!i || !lang_code) return;
    strncpy(i->active_lang, lang_code, sizeof(i->active_lang) - 1);
    i->active_lang[sizeof(i->active_lang) - 1] = '\0';
}

/* Returns translated string or falls back to key (no allocation). */
const char *zsys_i18n_get(ZsysI18n *i, const char *key) {
    return zsys_i18n_get_lang(i, i->active_lang, key);
}

const char *zsys_i18n_get_lang(ZsysI18n *i, const char *lang_code,
                                const char *key) {
    if (!i || !key) return key;
    LangTable  *lt = lang_find(i, lang_code);
    if (!lt) return key;
    const char *v  = lang_get(lt, key);
    return v ? v : key;
}
