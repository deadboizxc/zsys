/**
 * @file zsys_user.h
 * @brief Universal C representation of a Telegram user / account.
 *
 * Platform-independent; no Python.h or Telegram SDK dependency.
 * Used by Python (ctypes / CPython extension), Go (CGo), and Rust (bindgen).
 *
 * Memory: zsys_user_free() releases heap memory owned by ZsysUser.
 *         Stack-allocated instances must have their string fields set
 *         via zsys_user_set_*() which strdup the value.
 */
// RU: Универсальное C-представление Telegram-пользователя / аккаунта.
//     Не зависит от Python или Telegram SDK — используется из любого языка.

#ifndef ZSYS_USER_H
#define ZSYS_USER_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ═══════════════════════════ Types ══════════════════════════════════════ */

/**
 * @brief Represents a Telegram user or bot account.
 *
 * All string fields are heap-allocated (strdup). Free with zsys_user_free().
 */
// RU: Telegram-пользователь или бот. Строки выделены через strdup.
typedef struct ZsysUser {
    int64_t  id;           /**< Unique Telegram user ID. */
    char    *username;     /**< @username without '@', or NULL. */
    char    *first_name;   /**< First name (always present). */
    char    *last_name;    /**< Last name, or NULL. */
    char    *phone;        /**< Phone number, or NULL. */
    char    *lang_code;    /**< IETF language tag, e.g. "ru", "en". */
    int      is_bot;       /**< 1 if this is a bot account, 0 otherwise. */
    int      is_premium;   /**< 1 if the user has Telegram Premium. */
    int64_t  created_at;   /**< Unix timestamp of record creation (0 = unknown). */
} ZsysUser;

/* ═══════════════════════════ Lifecycle ═════════════════════════════════ */

/**
 * @brief Allocate a new, zero-initialised ZsysUser on the heap.
 * @return Pointer to ZsysUser, or NULL on allocation failure.
 */
// RU: Выделяет новый ZsysUser на куче, инициализированный нулями.
ZsysUser *zsys_user_new(void);

/**
 * @brief Free a heap-allocated ZsysUser and all its string fields.
 * @param u Pointer to ZsysUser (NULL-safe).
 */
// RU: Освобождает ZsysUser и все его строковые поля.
void zsys_user_free(ZsysUser *u);

/**
 * @brief Shallow-copy src into dst (strings are strdup-ed).
 * @return 0 on success, -1 on allocation failure.
 */
// RU: Копирует поля src в dst (строки через strdup).
int zsys_user_copy(ZsysUser *dst, const ZsysUser *src);

/* ═══════════════════════════ Setters ════════════════════════════════════ */

/** @brief Set username (strdup). NULL clears the field. */
int zsys_user_set_username(ZsysUser *u, const char *val);

/** @brief Set first_name (strdup). */
int zsys_user_set_first_name(ZsysUser *u, const char *val);

/** @brief Set last_name (strdup). NULL clears the field. */
int zsys_user_set_last_name(ZsysUser *u, const char *val);

/** @brief Set phone (strdup). NULL clears the field. */
int zsys_user_set_phone(ZsysUser *u, const char *val);

/** @brief Set lang_code (strdup). NULL clears the field. */
int zsys_user_set_lang_code(ZsysUser *u, const char *val);

/* ═══════════════════════════ Serialisation ══════════════════════════════ */

/**
 * @brief Serialise ZsysUser to a flat JSON string.
 *        Caller must zsys_free() the result.
 * @return Heap-allocated JSON string, or NULL on failure.
 */
// RU: Сериализует пользователя в JSON-строку. Освободить через zsys_free().
char *zsys_user_to_json(const ZsysUser *u);

/**
 * @brief Deserialise ZsysUser from a flat JSON string in-place.
 * @param u    Target struct (must be zero-initialised or freed first).
 * @param json Flat JSON as produced by zsys_user_to_json().
 * @return 0 on success, -1 on parse error.
 */
// RU: Десериализует JSON в ZsysUser на месте.
int zsys_user_from_json(ZsysUser *u, const char *json);

#ifdef __cplusplus
}
#endif

#endif /* ZSYS_USER_H */
