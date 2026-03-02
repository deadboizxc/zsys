/**
 * @file zsys_storage.h
 * @brief Abstract in-memory key-value storage for zsys.
 *
 * Provides a language-agnostic KV store backed by an open-addressing hash
 * table. All keys and values are NUL-terminated strings.
 *
 * Intended for session state, module config, and ephemeral caching.
 * For persistence, serialize to/from JSON via zsys_kv_to_json() and call
 * your language-native DB layer to store the JSON string.
 */
// RU: Абстрактное хранилище ключ-значение для zsys. Строковые ключи и значения.

#ifndef ZSYS_STORAGE_H
#define ZSYS_STORAGE_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ═══════════════════════════ Types ══════════════════════════════════════ */

/**
 * @brief Opaque key-value store handle.
 */
// RU: Непрозрачный дескриптор хранилища ключ-значение.
typedef struct ZsysKV ZsysKV;

/**
 * @brief Callback signature for zsys_kv_foreach().
 *
 * @param key   Current key (internal pointer, do not free).
 * @param value Current value (internal pointer, do not free).
 * @param ctx   User-supplied context pointer.
 * @return 0 to continue iteration, non-zero to stop.
 */
// RU: Коллбэк для обхода всех пар ключ-значение.
typedef int (*ZsysKVIterFn)(const char *key, const char *value, void *ctx);

/* ═══════════════════════════ Lifecycle ═════════════════════════════════ */

/**
 * @brief Create a new, empty KV store.
 * @param initial_cap Initial hash-table capacity (0 → use default 16).
 * @return Heap-allocated ZsysKV, or NULL on failure.
 */
// RU: Создаёт пустое хранилище КВ. capacity=0 → по умолчанию 16 слотов.
ZsysKV *zsys_kv_new(size_t initial_cap);

/**
 * @brief Free a ZsysKV and all keys/values it owns.
 * @param kv KV store handle (NULL-safe).
 */
// RU: Освобождает хранилище и все ключи/значения.
void zsys_kv_free(ZsysKV *kv);

/* ═══════════════════════════ Operations ═════════════════════════════════ */

/**
 * @brief Insert or update a key-value pair.
 *
 * Both key and value are strdup-ed; caller retains ownership.
 * The table doubles when load factor exceeds 70%.
 * @return 0 on success, -1 on allocation failure.
 */
// RU: Вставить или обновить пару ключ-значение.
int zsys_kv_set(ZsysKV *kv, const char *key, const char *value);

/**
 * @brief Look up a value by key.
 * @return Internal pointer to value string, or NULL if not found.
 *         Valid until the next zsys_kv_set/del on the same key.
 */
// RU: Получить значение по ключу. NULL если нет. Указатель до следующего set/del.
const char *zsys_kv_get(ZsysKV *kv, const char *key);

/**
 * @brief Delete a key-value pair.
 * @return 0 if found and deleted, -1 if key not found.
 */
// RU: Удалить пару по ключу. -1 если ключ не найден.
int zsys_kv_del(ZsysKV *kv, const char *key);

/**
 * @brief Check if a key exists.
 * @return 1 if exists, 0 otherwise.
 */
// RU: Проверить наличие ключа.
int zsys_kv_has(ZsysKV *kv, const char *key);

/**
 * @brief Return the number of entries in the store.
 */
// RU: Количество пар в хранилище.
size_t zsys_kv_count(ZsysKV *kv);

/**
 * @brief Remove all entries.
 */
// RU: Очистить хранилище.
void zsys_kv_clear(ZsysKV *kv);

/**
 * @brief Iterate over all key-value pairs in undefined order.
 *
 * Calls fn(key, value, ctx) for each pair.
 * Stops if fn returns non-zero.
 */
// RU: Обойти все пары. Останавливается если fn вернула не 0.
void zsys_kv_foreach(ZsysKV *kv, ZsysKVIterFn fn, void *ctx);

/* ═══════════════════════════ Serialisation ══════════════════════════════ */

/**
 * @brief Serialise the entire store to a flat JSON object string.
 *        Caller must zsys_free() the result.
 * @return JSON string like {"key1":"val1","key2":"val2"}, or NULL on failure.
 */
// RU: Сериализует всё хранилище в JSON-объект. Освободить через zsys_free().
char *zsys_kv_to_json(ZsysKV *kv);

/**
 * @brief Deserialise a flat JSON object and merge into an existing store.
 *        Existing keys are overwritten.
 * @return 0 on success, -1 on parse or allocation error.
 */
// RU: Десериализует JSON в хранилище (мерджит с существующим).
int zsys_kv_from_json(ZsysKV *kv, const char *json);

#ifdef __cplusplus
}
#endif

#endif /* ZSYS_STORAGE_H */
