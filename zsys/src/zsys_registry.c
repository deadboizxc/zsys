/*
 * zsys_registry.c — name → handler_id registry with description/category.
 *
 * Simple dynamic array; O(n) lookup is acceptable for typical module counts.
 * No external dependencies (only libc).
 */

#define _POSIX_C_SOURCE 200809L /* for strdup */

#include <stdlib.h>
#include <string.h>
#include "zsys_core.h"

typedef struct RegEntry {
    char *name;
    int   handler_id;
    char *description;
    char *category;
} RegEntry;

struct ZsysRegistry {
    RegEntry *entries;
    size_t    count;
    size_t    cap;
};

ZsysRegistry *zsys_registry_new(void) {
    ZsysRegistry *reg = (ZsysRegistry *)calloc(1, sizeof(ZsysRegistry));
    if (!reg) return NULL;
    reg->cap     = 16;
    reg->entries = (RegEntry *)calloc(reg->cap, sizeof(RegEntry));
    if (!reg->entries) { free(reg); return NULL; }
    return reg;
}

void zsys_registry_free(ZsysRegistry *reg) {
    if (!reg) return;
    for (size_t i = 0; i < reg->count; i++) {
        free(reg->entries[i].name);
        free(reg->entries[i].description);
        free(reg->entries[i].category);
    }
    free(reg->entries);
    free(reg);
}

/* Returns index of entry with given name, or (size_t)-1 if not found. */
static size_t reg_find(ZsysRegistry *reg, const char *name) {
    for (size_t i = 0; i < reg->count; i++)
        if (strcmp(reg->entries[i].name, name) == 0)
            return i;
    return (size_t)-1;
}

int zsys_registry_register(ZsysRegistry *reg, const char *name,
                            int handler_id,
                            const char *description,
                            const char *category) {
    if (!reg || !name) return -1;
    size_t idx = reg_find(reg, name);
    if (idx != (size_t)-1) {
        /* Update existing entry in place */
        reg->entries[idx].handler_id = handler_id;
        free(reg->entries[idx].description);
        free(reg->entries[idx].category);
        reg->entries[idx].description = strdup(description ? description : "");
        reg->entries[idx].category    = strdup(category    ? category    : "");
        return 0;
    }
    /* Grow backing array if full */
    if (reg->count >= reg->cap) {
        size_t    new_cap = reg->cap * 2;
        RegEntry *tmp     = (RegEntry *)realloc(reg->entries,
                                                new_cap * sizeof(RegEntry));
        if (!tmp) return -1;
        reg->entries = tmp;
        reg->cap     = new_cap;
    }
    reg->entries[reg->count].name        = strdup(name);
    reg->entries[reg->count].handler_id  = handler_id;
    reg->entries[reg->count].description = strdup(description ? description : "");
    reg->entries[reg->count].category    = strdup(category    ? category    : "");
    reg->count++;
    return 0;
}

int zsys_registry_unregister(ZsysRegistry *reg, const char *name) {
    if (!reg || !name) return -1;
    size_t idx = reg_find(reg, name);
    if (idx == (size_t)-1) return -1;
    free(reg->entries[idx].name);
    free(reg->entries[idx].description);
    free(reg->entries[idx].category);
    /* Shift remaining entries down to fill the gap */
    for (size_t i = idx; i + 1 < reg->count; i++)
        reg->entries[i] = reg->entries[i + 1];
    reg->count--;
    return 0;
}

/* Returns handler_id, or -1 if not found. */
int zsys_registry_get(ZsysRegistry *reg, const char *name) {
    if (!reg || !name) return -1;
    size_t idx = reg_find(reg, name);
    return (idx != (size_t)-1) ? reg->entries[idx].handler_id : -1;
}

int zsys_registry_info(ZsysRegistry *reg, const char *name,
                        char *out_desc, size_t desc_len,
                        char *out_cat,  size_t cat_len) {
    if (!reg || !name) return -1;
    size_t idx = reg_find(reg, name);
    if (idx == (size_t)-1) return -1;
    if (out_desc && desc_len) {
        strncpy(out_desc, reg->entries[idx].description, desc_len - 1);
        out_desc[desc_len - 1] = '\0';
    }
    if (out_cat && cat_len) {
        strncpy(out_cat, reg->entries[idx].category, cat_len - 1);
        out_cat[cat_len - 1] = '\0';
    }
    return 0;
}

size_t zsys_registry_count(ZsysRegistry *reg) {
    return reg ? reg->count : 0;
}

/* Returns pointer to internal name string at index i, or NULL. */
const char *zsys_registry_name_at(ZsysRegistry *reg, size_t i) {
    if (!reg || i >= reg->count) return NULL;
    return reg->entries[i].name;
}
