/*
 * tg_auth.c  —  TDLib authorization state machine.
 *
 * States (following TDLib's authorizationState sequence):
 *   INITIAL
 *     ↓  updateAuthorizationState
 *   WAIT_PARAMS    → send tdlibParameters
 *     ↓
 *   WAIT_ENCRYPTION_KEY  → send checkDatabaseEncryptionKey("")
 *     ↓
 *   WAIT_PHONE   → call ask_phone callback, user calls tg_client_provide_phone()
 *     ↓            (for bot mode: send checkAuthenticationBotToken)
 *   WAIT_CODE    → call ask_code callback, user calls tg_client_provide_code()
 *     ↓
 *   WAIT_PASS    → call ask_pass callback (2FA)
 *     ↓
 *   READY        → signal auth_cond, call on_ready callback, request getMe
 */

#include "tg_internal.h"

/* ── send tdlibParameters ────────────────────────────────────────────────── */

void _send_tdlib_params(tg_client_t *c)
{
    const tg_config_t *cfg = c->config;
    char buf[2048];
    /* TDLib 1.8.29+ uses flat parameters (no nested "parameters" object) */
    snprintf(buf, sizeof(buf),
        "{"
        "\"@type\":\"setTdlibParameters\","
        "\"use_test_dc\":%s,"
        "\"database_directory\":\"%s/%s\","
        "\"files_directory\":\"%s/%s_files\","
        "\"database_encryption_key\":\"\","
        "\"use_file_database\":true,"
        "\"use_chat_info_database\":true,"
        "\"use_message_database\":true,"
        "\"use_secret_chats\":false,"
        "\"api_id\":%d,"
        "\"api_hash\":\"%s\","
        "\"system_language_code\":\"%s\","
        "\"device_model\":\"%s\","
        "\"system_version\":\"%s\","
        "\"application_version\":\"%s\""
        "}",
        cfg->use_test_dc ? "true" : "false",
        cfg->session_dir  ? cfg->session_dir  : ".",
        cfg->session_name ? cfg->session_name : "session",
        cfg->session_dir  ? cfg->session_dir  : ".",
        cfg->session_name ? cfg->session_name : "session",
        cfg->api_id,
        cfg->api_hash,
        cfg->lang_code    ? cfg->lang_code    : "en",
        cfg->device_model ? cfg->device_model : "Desktop",
        cfg->system_version ? cfg->system_version : "Linux",
        cfg->app_version  ? cfg->app_version  : "1.0.0"
    );
    _tg_send_raw(c, buf);
}

/* ── public auth response functions ─────────────────────────────────────── */

void tg_client_provide_phone(tg_client_t *c, const char *phone)
{
    char buf[256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"setAuthenticationPhoneNumber\","
             "\"phone_number\":\"%s\"}", phone);
    _tg_send_raw(c, buf);
}

void tg_client_provide_code(tg_client_t *c, const char *code)
{
    char buf[128];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"checkAuthenticationCode\","
             "\"code\":\"%s\"}", code);
    _tg_send_raw(c, buf);
}

void tg_client_provide_pass(tg_client_t *c, const char *password)
{
    char buf[512];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"checkAuthenticationPassword\","
             "\"password\":\"%s\"}", password);
    _tg_send_raw(c, buf);
}

/* ── getMe request (called after READY) ─────────────────────────────────── */

static void _request_me(tg_client_t *c)
{
    _tg_send_fmt(c, "{\"@type\":\"getMe\",\"@extra\":\"__tg_get_me__\"}");
}

/* ── state transition ────────────────────────────────────────────────────── */

void _tg_dispatch_auth(tg_client_t *c, const char *state_json)
{
    char state_type[TG_TYPE_MAX] = {0};
    _json_type(state_json, state_type, sizeof(state_type));

    if (strcmp(state_type, "authorizationStateWaitTdlibParameters") == 0) {
        c->auth_state = TG_AUTH_WAIT_PARAMS;
        _send_tdlib_params(c);

    } else if (strcmp(state_type, "authorizationStateWaitEncryptionKey") == 0) {
        c->auth_state = TG_AUTH_WAIT_ENCRYPTION_KEY;
        _tg_send_raw(c, "{\"@type\":\"checkDatabaseEncryptionKey\",\"encryption_key\":\"\"}");

    } else if (strcmp(state_type, "authorizationStateWaitPhoneNumber") == 0) {
        c->auth_state = TG_AUTH_WAIT_PHONE;
        const tg_config_t *cfg = c->config;

        if (cfg->bot_token) {
            /* bot mode: skip phone, send token directly */
            char buf[512];
            snprintf(buf, sizeof(buf),
                     "{\"@type\":\"checkAuthenticationBotToken\","
                     "\"token\":\"%s\"}", cfg->bot_token);
            _tg_send_raw(c, buf);
        } else if (cfg->phone) {
            /* userbot with pre-configured phone */
            tg_client_provide_phone(c, cfg->phone);
        } else {
            /* interactive: ask caller */
            if (c->ask_phone) c->ask_phone(c, c->auth_ud);
        }

    } else if (strcmp(state_type, "authorizationStateWaitCode") == 0) {
        c->auth_state = TG_AUTH_WAIT_CODE;
        if (c->ask_code) c->ask_code(c, c->auth_ud);

    } else if (strcmp(state_type, "authorizationStateWaitPassword") == 0) {
        c->auth_state = TG_AUTH_WAIT_PASS;
        if (c->ask_pass) c->ask_pass(c, c->auth_ud);

    } else if (strcmp(state_type, "authorizationStateWaitRegistration") == 0) {
        c->auth_state = TG_AUTH_WAIT_REGISTRATION;
        /* Register with empty name — caller should handle this properly */
        _tg_send_raw(c,
            "{\"@type\":\"registerUser\","
            "\"first_name\":\"User\","
            "\"last_name\":\"\"}");

    } else if (strcmp(state_type, "authorizationStateReady") == 0) {
        c->auth_state = TG_AUTH_READY;

        /* Wake up tg_client_wait_ready() */
        pthread_mutex_lock(&c->auth_lock);
        pthread_cond_broadcast(&c->auth_cond);
        pthread_mutex_unlock(&c->auth_lock);

        /* Fire on_ready callback and fetch self info */
        if (c->on_ready) c->on_ready(c, c->auth_ud);
        _request_me(c);

    } else if (strcmp(state_type, "authorizationStateClosing") == 0) {
        c->auth_state = TG_AUTH_CLOSING;

    } else if (strcmp(state_type, "authorizationStateClosed") == 0) {
        c->auth_state = TG_AUTH_CLOSED;
        tg_client_stop(c);

    } else if (strcmp(state_type, "authorizationStateLoggingOut") == 0) {
        c->auth_state = TG_AUTH_CLOSING;
        tg_client_stop(c);
    }
}
