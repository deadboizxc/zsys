/*
 * tg_account.c  —  account management (username, profile, photo, online).
 */

#include "tg_internal.h"
#include <string.h>

int tg_set_username(tg_client_t *c, const char *username)
{
    char buf[TG_NAME_MAX + 64];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"setUsername\","
             "\"username\":\"%s\"}",
             username ? username : "");
    return (int)_tg_send_raw(c, buf);
}

int tg_update_profile(tg_client_t *c, const char *first_name,
                      const char *last_name, const char *bio)
{
    int r = 0;
    if (first_name || last_name) {
        char buf[TG_NAME_MAX * 2 + 128];
        snprintf(buf, sizeof(buf),
                 "{\"@type\":\"setName\","
                 "\"first_name\":\"%s\","
                 "\"last_name\":\"%s\"}",
                 first_name ? first_name : "",
                 last_name  ? last_name  : "");
        r = (int)_tg_send_raw(c, buf);
    }
    if (bio) {
        char buf[TG_TEXT_MAX + 64];
        snprintf(buf, sizeof(buf),
                 "{\"@type\":\"setBio\",\"bio\":\"%s\"}", bio);
        r = (int)_tg_send_raw(c, buf);
    }
    return r;
}

int tg_set_profile_photo(tg_client_t *c, const char *path)
{
    char buf[TG_PATH_MAX + 256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"setProfilePhoto\","
             "\"photo\":{"
             "\"@type\":\"inputChatPhotoLocal\","
             "\"photo\":{"
             "\"@type\":\"inputFileLocal\","
             "\"path\":\"%s\"}}}",
             path);
    return (int)_tg_send_raw(c, buf);
}

int tg_set_online(tg_client_t *c, int is_online)
{
    char buf[128];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"setOption\","
             "\"name\":\"online\","
             "\"value\":{"
             "\"@type\":\"optionValueBoolean\","
             "\"value\":%s}}",
             is_online ? "true" : "false");
    return (int)_tg_send_raw(c, buf);
}
