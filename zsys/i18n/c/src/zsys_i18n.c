/**
 * @file zsys_i18n.c
 * @brief Lightweight internationalization: flat JSON loader + hash-table key→value store.
 *
 * Architecture:
 *   - ZsysI18n holds a singly-linked list of LangTable nodes, one per language code.
 *   - Each LangTable is an open-addressing hash table mapping "module.key" → translated string.
 *   - JSON parsing is intentionally minimal: only flat {"key":"value"} objects are supported
 *     (no nesting, no arrays). Nested keys use dot-notation ("alive.title").
 *   - No external dependencies — only libc (stdlib, string, stdio, ctype).
 *
 * Typical flow:
 *   1. zsys_i18n_new()          — allocate instance
 *   2. zsys_i18n_load_json()    — load language file
 *   3. zsys_i18n_set_lang()     — activate a language
 *   4. zsys_i18n_get()          — translate a key
 *   5. zsys_i18n_free()         — release all memory
 */
// RU: Лёгкая i18n: загрузка плоского JSON + хэш-таблица ключ→значение.
// RU: Поддерживает несколько языков. Зависит только от libc.

#define _POSIX_C_SOURCE 200809L /* for strdup */

#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>
#include "zsys_core.h"

/** Initial hash table capacity for each language (must be a power of two). */
// RU: Начальная ёмкость хэш-таблицы каждого языка (степень двойки).
#define I18N_INIT_CAP 256

/**
 * @brief Single slot in a per-language open-addressing hash table.
 */
// RU: Один слот хэш-таблицы языка: ключ, значение, флаг занятости.
typedef struct I18nEntry {
    char *key;   /**< Translation key (heap-allocated). */
    char *value; /**< Translated string (heap-allocated). */
    int   used;  /**< 1 = occupied, 0 = empty. */
} I18nEntry;

/**
 * @brief Per-language hash table node in a singly-linked list.
 */
// RU: Узел связного списка языков. Каждый узел — отдельная хэш-таблица.
typedef struct LangTable {
    char      lang_code[32]; /**< ISO language code e.g. "ru", "en". */
    I18nEntry *ht;           /**< Hash table slots array (heap-allocated). */
    size_t     ht_cap;       /**< Capacity of ht. */
    size_t     count;        /**< Number of occupied slots. */
    struct LangTable *next;  /**< Next language in the linked list. */
} LangTable;

/**
 * @brief Top-level i18n container — owns the language list and active lang state.
 */
// RU: Контейнер i18n: список языков + активный язык.
struct ZsysI18n {
    LangTable *langs;          /**< Head of the language linked list. */
    char       active_lang[32];/**< Currently active language code. */
};

/**
 * @brief FNV-1a 32-bit hash, masked to [0, cap-1].
 * @param s   NUL-terminated key string.
 * @param cap Table capacity (power of two).
 * @return    Slot index in range [0, cap-1].
 */
// RU: FNV-1a хэш, усечённый до [0, cap-1].
static size_t i18n_hash(const char *s, size_t cap) {
    size_t h = 2166136261u;
    while (*s) { h ^= (unsigned char)*s++; h *= 16777619u; }
    return h & (cap - 1);
}

/**
 * @brief Find a language table by ISO code.
 * @param i    ZsysI18n instance.
 * @param code Language code to find.
 * @return Pointer to LangTable, or NULL if not loaded.
 */
// RU: Находит языковую таблицу по коду языка.
static LangTable *lang_find(ZsysI18n *i, const char *code) {
    for (LangTable *l = i->langs; l; l = l->next)
        if (strcmp(l->lang_code, code) == 0) return l;
    return NULL;
}

/**
 * @brief Allocate and initialize a new LangTable for the given language code.
 * @param code ISO language code (max 31 chars).
 * @return New LangTable, or NULL on allocation failure.
 */
// RU: Создаёт новую языковую таблицу с начальной ёмкостью I18N_INIT_CAP.
static LangTable *lang_new(const char *code) {
    LangTable *l = (LangTable *)calloc(1, sizeof(LangTable));
    if (!l) return NULL;
    strncpy(l->lang_code, code, sizeof(l->lang_code) - 1);
    l->ht_cap = I18N_INIT_CAP;
    l->ht     = (I18nEntry *)calloc(l->ht_cap, sizeof(I18nEntry));
    if (!l->ht) { free(l); return NULL; }
    return l;
}

/**
 * @brief Free a LangTable and all its heap-allocated key/value strings.
 * @param l LangTable to free (must not be NULL).
 */
// RU: Освобождает языковую таблицу и все строки внутри неё.
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

/**
 * @brief Insert or update a key→value pair in a LangTable.
 *
 * The table is automatically doubled when the load factor exceeds 70%.
 * Both key and value are strdup-ed; the caller retains ownership of its strings.
 * @param l     Target language table.
 * @param key   Translation key (NUL-terminated).
 * @param value Translated string (NUL-terminated).
 * @return 0 on success, -1 on allocation failure.
 */
// RU: Вставляет или обновляет пару ключ→значение. Таблица растёт при load > 70%.
static int lang_set(LangTable *l, const char *key, const char *value) {
    /* Grow when load factor > 70%. */
    // RU: Увеличиваем таблицу при превышении load factor 70%.
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

/**
 * @brief Look up a translation key in a LangTable.
 * @param l   Language table to search.
 * @param key Translation key.
 * @return Pointer to the internal value string, or NULL if not found.
 *         The pointer is valid for the lifetime of the LangTable.
 */
// RU: Ищет ключ в хэш-таблице языка. Возвращает указатель на значение или NULL.
static const char *lang_get(LangTable *l, const char *key) {
    size_t pos = i18n_hash(key, l->ht_cap);
    for (size_t i = 0; i < l->ht_cap; i++) {
        size_t p = (pos + i) & (l->ht_cap - 1);
        if (!l->ht[p].used) return NULL; /* empty slot — key not present */
        // RU: Пустой слот означает, что ключа нет в таблице.
        if (strcmp(l->ht[p].key, key) == 0) return l->ht[p].value;
    }
    return NULL;
}

/* ═══════════════════════ Minimal flat JSON parser ═══════════════════════════
 * Handles only top-level: {"key": "value", ...}
 * Supports escape sequences: \n \t \r \" \\ and any other \X → X.
 * Skips non-string values (numbers, booleans, null) silently.
 */
// RU: Минимальный парсер плоского JSON. Только {"ключ":"значение"}.
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
    /* Advance to the opening '{'. */
    // RU: Пропускаем всё до открывающей '{'.
    while (*p && *p != '{') p++;
    if (!*p) { free(buf); return -1; }
    p++; /* skip '{' */

    char key[1024];
    char val[8192];

    while (*p) {
        /* Skip whitespace and comma separators. */
        // RU: Пропускаем пробелы и запятые.
        while (*p && (isspace((unsigned char)*p) || *p == ',')) p++;
        if (*p == '}' || !*p) break;
        if (*p != '"') { p++; continue; } /* unexpected token, skip */

        /* Read the key string character by character, handling backslash escapes. */
        // RU: Читаем строку ключа, обрабатывая escape-последовательности.
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

        /* Skip whitespace then colon separator. */
        // RU: Пропускаем пробелы и двоеточие между ключом и значением.
        while (*p && isspace((unsigned char)*p)) p++;
        if (*p != ':') continue;
        p++;
        while (*p && isspace((unsigned char)*p)) p++;

        /* Skip non-string values (numbers, booleans, null). */
        // RU: Пропускаем не-строковые значения (числа, boolean, null).
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

/* ═══════════════════════════ Public API ═════════════════════════════════════ */

/**
 * @brief Allocate a new, empty ZsysI18n instance.
 * @return Pointer to ZsysI18n, or NULL on allocation failure.
 */
// RU: Создаёт пустой экземпляр i18n. NULL при ошибке выделения памяти.
ZsysI18n *zsys_i18n_new(void) {
    return (ZsysI18n *)calloc(1, sizeof(ZsysI18n));
}

/**
 * @brief Free a ZsysI18n instance and all owned language tables.
 * @param i ZsysI18n instance (NULL-safe).
 */
// RU: Освобождает экземпляр i18n и все языковые таблицы.
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

/**
 * @brief Load (or merge) a flat JSON file into the table for lang_code.
 *
 * If the language was already loaded, new keys are merged in; existing keys
 * are overwritten with the new values.
 * @param i         ZsysI18n instance.
 * @param lang_code ISO language code (e.g. "ru", "en").
 * @param json_path Path to the flat JSON translation file.
 * @return 0 on success, -1 on NULL args, file not found, or parse error.
 */
// RU: Загружает плоский JSON-файл переводов в указанный язык (мерджит если уже загружен).
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

/**
 * @brief Set the active language for lookups.
 * @param i         ZsysI18n instance.
 * @param lang_code Language code to activate (e.g. "ru").
 */
// RU: Устанавливает активный язык для последующих вызовов zsys_i18n_get().
void zsys_i18n_set_lang(ZsysI18n *i, const char *lang_code) {
    if (!i || !lang_code) return;
    strncpy(i->active_lang, lang_code, sizeof(i->active_lang) - 1);
    i->active_lang[sizeof(i->active_lang) - 1] = '\0';
}

/**
 * @brief Translate a key using the active language.
 *
 * Falls back to returning the key itself when no translation is found,
 * so the call is always safe and never returns NULL (unless key is NULL).
 * @param i   ZsysI18n instance.
 * @param key Translation key.
 * @return Translated string, or key on miss; no allocation is performed.
 */
// RU: Переводит ключ активным языком. При отсутствии перевода возвращает сам ключ.
const char *zsys_i18n_get(ZsysI18n *i, const char *key) {
    return zsys_i18n_get_lang(i, i->active_lang, key);
}

/**
 * @brief Translate a key using an explicitly specified language.
 * @param i         ZsysI18n instance.
 * @param lang_code Language code to use for lookup.
 * @param key       Translation key.
 * @return Translated string, or key on miss; NULL if key is NULL.
 */
// RU: Переводит ключ указанным языком; при промахе возвращает исходный ключ.
const char *zsys_i18n_get_lang(ZsysI18n *i, const char *lang_code,
                                const char *key) {
    if (!i || !key) return key;
    LangTable  *lt = lang_find(i, lang_code);
    if (!lt) return key;
    const char *v  = lang_get(lt, key);
    return v ? v : key;
}
