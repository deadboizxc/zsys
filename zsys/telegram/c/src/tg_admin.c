/*
 * tg_admin.c  —  ban/unban/restrict/promote/kick, chat permissions.
 */

#include "tg_internal.h"
#include <string.h>
#include <stdio.h>

/* ── permissions helpers ─────────────────────────────────────────────────── */

uint32_t _perms_json_to_bitmask(const char *perms_json)
{
    uint32_t bits = 0;
    if (_json_bool(perms_json, "can_send_basic_messages"))  bits |= TG_PERM_SEND_MESSAGES;
    if (_json_bool(perms_json, "can_send_audios"))          bits |= TG_PERM_SEND_MEDIA;
    if (_json_bool(perms_json, "can_send_documents"))       bits |= TG_PERM_SEND_MEDIA;
    if (_json_bool(perms_json, "can_send_photos"))          bits |= TG_PERM_SEND_MEDIA;
    if (_json_bool(perms_json, "can_send_videos"))          bits |= TG_PERM_SEND_MEDIA;
    if (_json_bool(perms_json, "can_send_voice_notes"))     bits |= TG_PERM_SEND_MEDIA;
    if (_json_bool(perms_json, "can_send_video_notes"))     bits |= TG_PERM_SEND_MEDIA;
    if (_json_bool(perms_json, "can_send_polls"))           bits |= TG_PERM_SEND_POLLS;
    if (_json_bool(perms_json, "can_send_other_messages"))  bits |= TG_PERM_SEND_OTHER;
    if (_json_bool(perms_json, "can_add_web_page_previews")) bits |= TG_PERM_ADD_PREVIEWS;
    if (_json_bool(perms_json, "can_change_info"))          bits |= TG_PERM_CHANGE_INFO;
    if (_json_bool(perms_json, "can_invite_users"))         bits |= TG_PERM_INVITE_USERS;
    if (_json_bool(perms_json, "can_pin_messages"))         bits |= TG_PERM_PIN_MESSAGES;
    return bits;
}

void _perms_bitmask_to_json(uint32_t perms, char *buf, size_t sz)
{
    snprintf(buf, sz,
        "{\"@type\":\"chatPermissions\","
        "\"can_send_basic_messages\":%s,"
        "\"can_send_audios\":%s,"
        "\"can_send_documents\":%s,"
        "\"can_send_photos\":%s,"
        "\"can_send_videos\":%s,"
        "\"can_send_voice_notes\":%s,"
        "\"can_send_video_notes\":%s,"
        "\"can_send_polls\":%s,"
        "\"can_send_other_messages\":%s,"
        "\"can_add_web_page_previews\":%s,"
        "\"can_change_info\":%s,"
        "\"can_invite_users\":%s,"
        "\"can_pin_messages\":%s}",
        (perms & TG_PERM_SEND_MESSAGES) ? "true" : "false",
        (perms & TG_PERM_SEND_MEDIA)    ? "true" : "false",
        (perms & TG_PERM_SEND_MEDIA)    ? "true" : "false",
        (perms & TG_PERM_SEND_MEDIA)    ? "true" : "false",
        (perms & TG_PERM_SEND_MEDIA)    ? "true" : "false",
        (perms & TG_PERM_SEND_MEDIA)    ? "true" : "false",
        (perms & TG_PERM_SEND_MEDIA)    ? "true" : "false",
        (perms & TG_PERM_SEND_POLLS)    ? "true" : "false",
        (perms & TG_PERM_SEND_OTHER)    ? "true" : "false",
        (perms & TG_PERM_ADD_PREVIEWS)  ? "true" : "false",
        (perms & TG_PERM_CHANGE_INFO)   ? "true" : "false",
        (perms & TG_PERM_INVITE_USERS)  ? "true" : "false",
        (perms & TG_PERM_PIN_MESSAGES)  ? "true" : "false");
}

void _admin_rights_to_json(uint32_t rights, char *buf, size_t sz)
{
    snprintf(buf, sz,
        "{\"@type\":\"chatAdministratorRights\","
        "\"can_manage_chat\":%s,"
        "\"can_post_messages\":%s,"
        "\"can_edit_messages\":%s,"
        "\"can_delete_messages\":%s,"
        "\"can_restrict_members\":%s,"
        "\"can_invite_users\":%s,"
        "\"can_pin_messages\":%s,"
        "\"can_promote_members\":%s,"
        "\"can_change_info\":%s,"
        "\"can_manage_video_chats\":%s,"
        "\"is_anonymous\":%s}",
        (rights & TG_ADMIN_MANAGE_CHAT)      ? "true" : "false",
        (rights & TG_ADMIN_POST_MESSAGES)    ? "true" : "false",
        (rights & TG_ADMIN_EDIT_MESSAGES)    ? "true" : "false",
        (rights & TG_ADMIN_DELETE_MESSAGES)  ? "true" : "false",
        (rights & TG_ADMIN_BAN_USERS)        ? "true" : "false",
        (rights & TG_ADMIN_INVITE_USERS)     ? "true" : "false",
        (rights & TG_ADMIN_PIN_MESSAGES)     ? "true" : "false",
        (rights & TG_ADMIN_PROMOTE_MEMBERS)  ? "true" : "false",
        (rights & TG_ADMIN_CHANGE_INFO)      ? "true" : "false",
        (rights & TG_ADMIN_MANAGE_VIDEO)     ? "true" : "false",
        (rights & TG_ADMIN_ANONYMOUS)        ? "true" : "false");
}

/* ── helper: build messageSenderUser JSON ────────────────────────────────── */

static void _sender_user(int64_t user_id, char *buf, size_t sz)
{
    snprintf(buf, sz,
             "{\"@type\":\"messageSenderUser\",\"user_id\":%lld}",
             (long long)user_id);
}

/* ── ban / unban / kick ──────────────────────────────────────────────────── */

int tg_ban_member(tg_client_t *c, int64_t chat_id, int64_t user_id,
                  int32_t until_date)
{
    char sender[128];
    _sender_user(user_id, sender, sizeof(sender));
    char buf[512];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"banChatMember\","
             "\"chat_id\":%lld,"
             "\"member_id\":%s,"
             "\"banned_until_date\":%d,"
             "\"revoke_messages\":false}",
             (long long)chat_id, sender, (int)until_date);
    return (int)_tg_send_raw(c, buf);
}

int tg_unban_member(tg_client_t *c, int64_t chat_id, int64_t user_id)
{
    char sender[128];
    _sender_user(user_id, sender, sizeof(sender));
    char buf[512];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"setChatMemberStatus\","
             "\"chat_id\":%lld,"
             "\"member_id\":%s,"
             "\"status\":{\"@type\":\"chatMemberStatusMember\"}}",
             (long long)chat_id, sender);
    return (int)_tg_send_raw(c, buf);
}

int tg_kick_member(tg_client_t *c, int64_t chat_id, int64_t user_id)
{
    /* Ban first, then immediately unban */
    int r = tg_ban_member(c, chat_id, user_id, 0);
    if (r < 0) return r;
    return tg_unban_member(c, chat_id, user_id);
}

/* ── restrict ────────────────────────────────────────────────────────────── */

int tg_restrict_member(tg_client_t *c, int64_t chat_id, int64_t user_id,
                       uint32_t perms, int32_t until_date)
{
    char sender[128];
    _sender_user(user_id, sender, sizeof(sender));
    char perms_json[1024];
    _perms_bitmask_to_json(perms, perms_json, sizeof(perms_json));
    char buf[2048];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"setChatMemberStatus\","
             "\"chat_id\":%lld,"
             "\"member_id\":%s,"
             "\"status\":{"
             "\"@type\":\"chatMemberStatusRestricted\","
             "\"is_member\":true,"
             "\"restricted_until_date\":%d,"
             "\"permissions\":%s}}",
             (long long)chat_id, sender, (int)until_date, perms_json);
    return (int)_tg_send_raw(c, buf);
}

/* ── promote ─────────────────────────────────────────────────────────────── */

int tg_promote_member(tg_client_t *c, int64_t chat_id, int64_t user_id,
                      uint32_t admin_rights, const char *custom_title)
{
    char sender[128];
    _sender_user(user_id, sender, sizeof(sender));
    char rights_json[1024];
    _admin_rights_to_json(admin_rights, rights_json, sizeof(rights_json));

    char title_buf[256] = {0};
    if (custom_title && custom_title[0])
        snprintf(title_buf, sizeof(title_buf),
                 ",\"custom_title\":\"%s\"", custom_title);

    char buf[2048];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"setChatMemberStatus\","
             "\"chat_id\":%lld,"
             "\"member_id\":%s,"
             "\"status\":{"
             "\"@type\":\"chatMemberStatusAdministrator\","
             "\"can_be_edited\":true%s,"
             "\"rights\":%s}}",
             (long long)chat_id, sender, title_buf, rights_json);
    return (int)_tg_send_raw(c, buf);
}

/* ── set chat permissions ────────────────────────────────────────────────── */

int tg_set_chat_permissions(tg_client_t *c, int64_t chat_id, uint32_t perms)
{
    char perms_json[1024];
    _perms_bitmask_to_json(perms, perms_json, sizeof(perms_json));
    char buf[1280];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"setChatPermissions\","
             "\"chat_id\":%lld,"
             "\"permissions\":%s}",
             (long long)chat_id, perms_json);
    return (int)_tg_send_raw(c, buf);
}
