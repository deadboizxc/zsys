/**
 * @file zsys_chat.h
 * @brief Universal C representation of a Telegram chat/channel/group.
 *
 * Platform-independent; no Python.h or Telegram SDK dependency.
 */
// RU: Универсальное C-представление Telegram-чата, канала или группы.

#ifndef ZSYS_CHAT_H
#define ZSYS_CHAT_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ═══════════════════════════ Types ══════════════════════════════════════ */

/**
 * @brief Chat type enumeration.
 */
// RU: Тип чата.
typedef enum ZsysChatType {
    ZSYS_CHAT_PRIVATE   = 0,  /**< Private conversation with one user. */
    ZSYS_CHAT_GROUP     = 1,  /**< Basic group (up to 200 members). */
    ZSYS_CHAT_SUPERGROUP = 2, /**< Supergroup (unlimited members). */
    ZSYS_CHAT_CHANNEL   = 3,  /**< Broadcast channel. */
    ZSYS_CHAT_BOT       = 4,  /**< Private chat with a bot. */
} ZsysChatType;

/**
 * @brief Represents a Telegram chat entity.
 *
 * All string fields are heap-allocated (strdup). Free with zsys_chat_free().
 */
// RU: Telegram-чат. Строки выделены через strdup, освободить zsys_chat_free().
typedef struct ZsysChat {
    int64_t      id;            /**< Unique Telegram chat ID. */
    ZsysChatType type;          /**< Chat type (private/group/supergroup/channel). */
    char        *title;         /**< Chat title, or NULL for private chats. */
    char        *username;      /**< @username without '@', or NULL. */
    char        *description;   /**< Chat description, or NULL. */
    int32_t      member_count;  /**< Number of members (-1 = unknown). */
    int          is_restricted; /**< 1 if the chat is restricted. */
    int          is_scam;       /**< 1 if Telegram flagged as scam. */
    int64_t      created_at;    /**< Unix timestamp of record creation. */
} ZsysChat;

/* ═══════════════════════════ Lifecycle ═════════════════════════════════ */

/**
 * @brief Allocate a new, zero-initialised ZsysChat on the heap.
 * @return Pointer to ZsysChat, or NULL on failure.
 */
// RU: Выделяет новый ZsysChat на куче.
ZsysChat *zsys_chat_new(void);

/**
 * @brief Free a heap-allocated ZsysChat and all its string fields.
 * @param c Pointer to ZsysChat (NULL-safe).
 */
// RU: Освобождает ZsysChat и все строковые поля.
void zsys_chat_free(ZsysChat *c);

/**
 * @brief Shallow-copy src into dst (strings are strdup-ed).
 * @return 0 on success, -1 on allocation failure.
 */
// RU: Копирует поля src в dst через strdup.
int zsys_chat_copy(ZsysChat *dst, const ZsysChat *src);

/* ═══════════════════════════ Setters ════════════════════════════════════ */

/** @brief Set title (strdup). NULL clears the field. */
int zsys_chat_set_title(ZsysChat *c, const char *val);

/** @brief Set username (strdup). NULL clears the field. */
int zsys_chat_set_username(ZsysChat *c, const char *val);

/** @brief Set description (strdup). NULL clears the field. */
int zsys_chat_set_description(ZsysChat *c, const char *val);

/* ═══════════════════════════ Helpers ════════════════════════════════════ */

/**
 * @brief Return a human-readable name for a ZsysChatType.
 * @return Static string (do not free).
 */
// RU: Возвращает строковое имя типа чата (статическая строка).
const char *zsys_chat_type_str(ZsysChatType type);

/* ═══════════════════════════ Serialisation ══════════════════════════════ */

/**
 * @brief Serialise ZsysChat to a flat JSON string.
 *        Caller must zsys_free() the result.
 */
// RU: Сериализует чат в JSON. Освободить через zsys_free().
char *zsys_chat_to_json(const ZsysChat *c);

/**
 * @brief Deserialise ZsysChat from a flat JSON string in-place.
 * @return 0 on success, -1 on parse error.
 */
// RU: Десериализует JSON в ZsysChat.
int zsys_chat_from_json(ZsysChat *c, const char *json);

#ifdef __cplusplus
}
#endif

#endif /* ZSYS_CHAT_H */
