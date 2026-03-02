/**
 * @file zsys_client.h
 * @brief Universal C configuration structure for a Telegram userbot/bot client.
 *
 * Stores all credentials and settings needed to connect to Telegram.
 * Language-agnostic: Python binds via ctypes/CPython, Go via CGo, Rust via bindgen.
 */
// RU: Конфигурация Telegram-клиента (userbota или бота). Не зависит от языка.

#ifndef ZSYS_CLIENT_H
#define ZSYS_CLIENT_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ═══════════════════════════ Types ══════════════════════════════════════ */

/**
 * @brief Client mode: user account or bot token.
 */
// RU: Режим клиента: пользователь или бот.
typedef enum ZsysClientMode {
    ZSYS_CLIENT_USER = 0,  /**< Regular user account (userbot). */
    ZSYS_CLIENT_BOT  = 1,  /**< Bot token-based account. */
} ZsysClientMode;

/**
 * @brief All configuration required to start a Telegram client session.
 *
 * String fields are heap-allocated (strdup). Free with zsys_client_config_free().
 */
// RU: Конфигурация Telegram-клиента. Строки через strdup.
typedef struct ZsysClientConfig {
    /* Telegram API credentials (required). */
    int32_t  api_id;         /**< Telegram API ID from my.telegram.org. */
    char    *api_hash;       /**< Telegram API hash (32 hex chars). */

    /* Session. */
    char    *session_name;   /**< Session file name without extension. */
    ZsysClientMode mode;     /**< User or bot mode. */

    /* User mode fields. */
    char    *phone;          /**< Phone number in international format, or NULL. */

    /* Bot mode fields. */
    char    *bot_token;      /**< Bot token from @BotFather, or NULL. */

    /* Device / app identity shown to Telegram. */
    char    *device_model;   /**< e.g. "Samsung Galaxy S23". */
    char    *system_version; /**< e.g. "Android 14". */
    char    *app_version;    /**< e.g. "1.0.0". */
    char    *lang_code;      /**< IETF language tag, e.g. "en". */
    char    *lang_pack;      /**< Telegram lang pack, e.g. "android". */

    /* Proxy (optional). */
    char    *proxy_host;     /**< Proxy hostname, or NULL to disable. */
    int32_t  proxy_port;     /**< Proxy port (0 = disabled). */
    char    *proxy_user;     /**< Proxy username, or NULL. */
    char    *proxy_pass;     /**< Proxy password, or NULL. */

    /* Behaviour. */
    int      sleep_threshold; /**< Max flood-wait sleep seconds (default 60). */
    int      max_concurrent;  /**< Max concurrent workers (default 1). */
} ZsysClientConfig;

/* ═══════════════════════════ Lifecycle ═════════════════════════════════ */

/**
 * @brief Allocate a new ZsysClientConfig with sensible defaults.
 *
 * Defaults: mode=USER, lang_code="en", sleep_threshold=60, max_concurrent=1.
 * @return Heap-allocated config, or NULL on failure.
 */
// RU: Создаёт ZsysClientConfig с разумными значениями по умолчанию.
ZsysClientConfig *zsys_client_config_new(void);

/**
 * @brief Free a ZsysClientConfig and all its string fields.
 * @param cfg Pointer to config (NULL-safe).
 */
// RU: Освобождает ZsysClientConfig и все строки.
void zsys_client_config_free(ZsysClientConfig *cfg);

/**
 * @brief Deep-copy src into dst (all strings strdup-ed).
 * @return 0 on success, -1 on allocation failure.
 */
// RU: Глубокое копирование конфигурации (все строки через strdup).
int zsys_client_config_copy(ZsysClientConfig *dst, const ZsysClientConfig *src);

/* ═══════════════════════════ Setters ════════════════════════════════════ */

int zsys_client_set_api_hash(ZsysClientConfig *c, const char *val);
int zsys_client_set_session_name(ZsysClientConfig *c, const char *val);
int zsys_client_set_phone(ZsysClientConfig *c, const char *val);
int zsys_client_set_bot_token(ZsysClientConfig *c, const char *val);
int zsys_client_set_device_model(ZsysClientConfig *c, const char *val);
int zsys_client_set_system_version(ZsysClientConfig *c, const char *val);
int zsys_client_set_app_version(ZsysClientConfig *c, const char *val);
int zsys_client_set_lang_code(ZsysClientConfig *c, const char *val);
int zsys_client_set_lang_pack(ZsysClientConfig *c, const char *val);
int zsys_client_set_proxy(ZsysClientConfig *c,
                          const char *host, int32_t port,
                          const char *user, const char *pass);

/* ═══════════════════════════ Validation ═════════════════════════════════ */

/**
 * @brief Check that required fields are set.
 *
 * Checks: api_id != 0, api_hash set, session_name set,
 *         and either phone (USER mode) or bot_token (BOT mode) is set.
 * @param out_err  Optional buffer to receive human-readable error (may be NULL).
 * @param err_len  Size of out_err buffer.
 * @return 0 if valid, -1 if invalid.
 */
// RU: Проверяет обязательные поля конфигурации.
int zsys_client_config_validate(const ZsysClientConfig *c,
                                char *out_err, size_t err_len);

/* ═══════════════════════════ Serialisation ══════════════════════════════ */

/**
 * @brief Serialise config to JSON (bot_token and api_hash are NOT included).
 *        Caller must zsys_free() the result.
 */
// RU: Сериализует конфигурацию в JSON (секреты НЕ включаются).
char *zsys_client_config_to_json(const ZsysClientConfig *c);

/**
 * @brief Deserialise config from JSON in-place.
 * @return 0 on success, -1 on parse error.
 */
// RU: Десериализует JSON в конфигурацию.
int zsys_client_config_from_json(ZsysClientConfig *c, const char *json);

#ifdef __cplusplus
}
#endif

#endif /* ZSYS_CLIENT_H */
