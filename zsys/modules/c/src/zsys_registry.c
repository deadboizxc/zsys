/**
 * @file zsys_registry.c
 * @brief Name-to-handler-id registry with optional description and category.
 *
 * Backed by a simple dynamic array. O(n) lookup is acceptable because
 * typical module counts stay well below 256 entries. No external dependencies.
 *
 * Use this to maintain a global catalogue of registered commands/handlers,
 * decoupled from the hash-table router in zsys_router.c.
 */
// RU: Реестр имя→handler_id с описанием и категорией. Динамический массив, O(n) поиск.

#define _POSIX_C_SOURCE 200809L /* for strdup */

#include <stdlib.h>
#include <string.h>
#include "zsys_core.h"

/**
 * @brief Single registry record.
 */
// RU: Одна запись реестра: имя, handler ID, описание, категория.
typedef struct RegEntry {
    char *name;        /**< Unique command name (heap-allocated). */
    int   handler_id;  /**< Opaque integer handler identifier. */
    char *description; /**< Human-readable description (heap-allocated). */
    char *category;    /**< Category label e.g. "system", "fun" (heap-allocated). */
} RegEntry;

/**
 * @brief Registry instance — owns a growable array of RegEntry.
 */
// RU: Экземпляр реестра — динамический массив записей.
struct ZsysRegistry {
    RegEntry *entries; /**< Heap-allocated array of entries. */
    size_t    count;   /**< Number of currently registered entries. */
    size_t    cap;     /**< Allocated capacity of the entries array. */
};

/**
 * @brief Allocate and initialize a new registry with default capacity (16).
 * @return Pointer to ZsysRegistry, or NULL on allocation failure.
 */
// RU: Создаёт новый реестр с начальной ёмкостью 16.
ZsysRegistry *zsys_registry_new(void) {
    ZsysRegistry *reg = (ZsysRegistry *)calloc(1, sizeof(ZsysRegistry));
    if (!reg) return NULL;
    reg->cap     = 16;
    reg->entries = (RegEntry *)calloc(reg->cap, sizeof(RegEntry));
    if (!reg->entries) { free(reg); return NULL; }
    return reg;
}

/**
 * @brief Free all memory owned by the registry (entries and their strings).
 * @param reg Registry instance (NULL-safe).
 */
// RU: Освобождает всю память реестра, включая строки внутри записей.
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

/**
 * @brief Linear search for an entry by name.
 * @param reg  Registry to search.
 * @param name Name to find.
 * @return Index of the matching entry, or (size_t)-1 if not found.
 */
// RU: Линейный поиск записи по имени. Возвращает индекс или (size_t)-1.
static size_t reg_find(ZsysRegistry *reg, const char *name) {
    for (size_t i = 0; i < reg->count; i++)
        if (strcmp(reg->entries[i].name, name) == 0)
            return i;
    return (size_t)-1;
}

/**
 * @brief Register a command by name or update it if already present.
 *
 * On update, only handler_id, description, and category are replaced; the
 * name string itself is kept intact.
 * @param reg         Registry instance.
 * @param name        Unique command name.
 * @param handler_id  Opaque integer handler ID.
 * @param description Human-readable description (may be NULL → stored as "").
 * @param category    Category label (may be NULL → stored as "").
 * @return 0 on success, -1 on NULL args or allocation failure.
 */
// RU: Регистрирует команду или обновляет существующую запись.
int zsys_registry_register(ZsysRegistry *reg, const char *name,
                            int handler_id,
                            const char *description,
                            const char *category) {
    if (!reg || !name) return -1;
    size_t idx = reg_find(reg, name);
    if (idx != (size_t)-1) {
        /* Update existing entry in place. */
        // RU: Обновляем существующую запись.
        reg->entries[idx].handler_id = handler_id;
        free(reg->entries[idx].description);
        free(reg->entries[idx].category);
        reg->entries[idx].description = strdup(description ? description : "");
        reg->entries[idx].category    = strdup(category    ? category    : "");
        return 0;
    }
    /* Grow backing array if at capacity. */
    // RU: Увеличиваем массив в 2 раза, если достигнута ёмкость.
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

/**
 * @brief Unregister a command by name.
 *
 * The gap left by the removed entry is filled by shifting subsequent entries
 * down by one position (preserves insertion order).
 * @param reg  Registry instance.
 * @param name Name to remove.
 * @return 0 if found and removed, -1 if not found or NULL args.
 */
// RU: Удаляет команду из реестра; сдвигает последующие записи, заполняя пробел.
int zsys_registry_unregister(ZsysRegistry *reg, const char *name) {
    if (!reg || !name) return -1;
    size_t idx = reg_find(reg, name);
    if (idx == (size_t)-1) return -1;
    free(reg->entries[idx].name);
    free(reg->entries[idx].description);
    free(reg->entries[idx].category);
    /* Shift remaining entries down to fill the gap. */
    // RU: Сдвигаем оставшиеся записи, заполняя пробел.
    for (size_t i = idx; i + 1 < reg->count; i++)
        reg->entries[i] = reg->entries[i + 1];
    reg->count--;
    return 0;
}

/**
 * @brief Look up a handler ID by command name.
 * @param reg  Registry instance.
 * @param name Command name to look up.
 * @return handler_id if found, -1 if not found or NULL args.
 */
// RU: Возвращает handler_id по имени команды или -1, если не найдено.
int zsys_registry_get(ZsysRegistry *reg, const char *name) {
    if (!reg || !name) return -1;
    size_t idx = reg_find(reg, name);
    return (idx != (size_t)-1) ? reg->entries[idx].handler_id : -1;
}

/**
 * @brief Retrieve description and category strings for a registered command.
 * @param reg      Registry instance.
 * @param name     Command name to query.
 * @param out_desc Output buffer for description (may be NULL to skip).
 * @param desc_len Size of out_desc buffer in bytes.
 * @param out_cat  Output buffer for category (may be NULL to skip).
 * @param cat_len  Size of out_cat buffer in bytes.
 * @return 0 on success, -1 if not found or NULL args.
 */
// RU: Возвращает описание и категорию команды. Любой из out_* может быть NULL.
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

/**
 * @brief Return the total number of registered entries.
 * @param reg Registry instance (NULL-safe).
 * @return Entry count, or 0 for NULL registry.
 */
// RU: Возвращает количество зарегистрированных записей.
size_t zsys_registry_count(ZsysRegistry *reg) {
    return reg ? reg->count : 0;
}

/**
 * @brief Return a pointer to the internal name string at the given index.
 *
 * The pointer is valid only as long as the registry and the entry at index i
 * are not modified. Do not free the returned pointer.
 * @param reg Registry instance.
 * @param i   Zero-based index.
 * @return Pointer to name string, or NULL if out of range or NULL registry.
 */
// RU: Возвращает указатель на имя записи по индексу. Не освобождать!
const char *zsys_registry_name_at(ZsysRegistry *reg, size_t i) {
    if (!reg || i >= reg->count) return NULL;
    return reg->entries[i].name;
}
