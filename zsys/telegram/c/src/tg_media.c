/*
 * tg_media.c  —  send animation/sticker/voice/video_note/location/contact/
 *                poll/dice/chat_action/copy_message, file operations.
 */

#include "tg_internal.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

/* ── file info parsing ───────────────────────────────────────────────────── */

void _parse_file_json(const char *json, tg_file_t *out)
{
    memset(out, 0, sizeof(*out));
    out->id   = (int32_t)_json_int(json, "id");
    out->size = _json_int(json, "size");
    out->is_downloading = _json_bool(json, "is_downloading_active");
    out->is_downloaded  = _json_bool(json, "is_downloading_completed");

    const char *local = _json_obj(json, "local");
    if (local) {
        _json_str(local, "path", out->local_path, sizeof(out->local_path));
        if (!out->is_downloaded)
            out->is_downloaded = _json_bool(local, "is_downloading_completed");
    }
    _json_str(json, "mime_type", out->mime_type, sizeof(out->mime_type));
    _json_str(json, "file_name", out->file_name, sizeof(out->file_name));
}

/* ── pending file download callback ─────────────────────────────────────── */

typedef struct { tg_file_cb_fn cb; void *ud; } _file_req_t;

static void _on_get_file(tg_client_t *c, const char *json, void *ud)
{
    _file_req_t *req = ud;
    char type[TG_TYPE_MAX] = {0};
    _json_type(json, type, sizeof(type));
    if (strcmp(type, "file") == 0) {
        tg_file_t f;
        _parse_file_json(json, &f);
        if (req->cb) req->cb(c, &f, req->ud);
    }
    free(req);
}

int tg_get_file(tg_client_t *c, int32_t file_id, tg_file_cb_fn cb, void *ud)
{
    _file_req_t *req = malloc(sizeof(*req));
    if (!req) return -1;
    req->cb = cb; req->ud = ud;
    char json[128];
    snprintf(json, sizeof(json),
             "{\"@type\":\"getFile\",\"file_id\":%d}", file_id);
    return (int)_tg_send_pending(c, json, _on_get_file, req);
}

/* ── file accessors ──────────────────────────────────────────────────────── */

int32_t     tg_file_id(const tg_file_t *f)           { return f->id; }
int64_t     tg_file_size(const tg_file_t *f)         { return f->size; }
const char *tg_file_local_path(const tg_file_t *f)   { return f->local_path; }
int         tg_file_is_downloaded(const tg_file_t *f){ return f->is_downloaded; }
const char *tg_file_mime_type(const tg_file_t *f)    { return f->mime_type; }
const char *tg_file_name(const tg_file_t *f)         { return f->file_name; }

/* ── chat action name → TDLib type ──────────────────────────────────────── */

static const char *_action_to_tdtype(const char *action)
{
    if (!action) return "chatActionTyping";
    if (strcmp(action, "typing")         == 0) return "chatActionTyping";
    if (strcmp(action, "upload_photo")   == 0) return "chatActionUploadingPhoto";
    if (strcmp(action, "upload_video")   == 0) return "chatActionUploadingVideo";
    if (strcmp(action, "upload_document")== 0) return "chatActionUploadingDocument";
    if (strcmp(action, "upload_audio")   == 0) return "chatActionUploadingVoiceNote";
    if (strcmp(action, "record_video")   == 0) return "chatActionRecordingVideo";
    if (strcmp(action, "record_audio")   == 0) return "chatActionRecordingVoiceNote";
    if (strcmp(action, "find_location")  == 0) return "chatActionChoosingLocation";
    if (strcmp(action, "record_video_note") == 0) return "chatActionRecordingVideoNote";
    if (strcmp(action, "upload_video_note") == 0) return "chatActionUploadingVideoNote";
    if (strcmp(action, "choose_sticker") == 0) return "chatActionChoosingSticker";
    if (strcmp(action, "cancel")         == 0) return "chatActionCancel";
    return action;  /* pass through if already TDLib type */
}

/* ── send actions ────────────────────────────────────────────────────────── */

int tg_send_animation(tg_client_t *c, int64_t chat_id,
                      const char *path, const char *caption)
{
    char cap_buf[TG_TEXT_MAX + 128] = {0};
    if (caption && caption[0])
        snprintf(cap_buf, sizeof(cap_buf),
                 ",\"caption\":{\"@type\":\"formattedText\","
                 "\"text\":\"%s\",\"entities\":[]}", caption);
    char buf[TG_PATH_MAX + TG_TEXT_MAX + 256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"sendMessage\","
             "\"chat_id\":%lld,"
             "\"input_message_content\":{"
             "\"@type\":\"inputMessageAnimation\","
             "\"animation\":{\"@type\":\"inputFileLocal\",\"path\":\"%s\"}%s}}",
             (long long)chat_id, path, cap_buf);
    return (int)_tg_send_raw(c, buf);
}

int tg_send_sticker(tg_client_t *c, int64_t chat_id,
                    const char *file_id_or_path)
{
    /* Heuristic: if starts with '/' or '.', treat as local file */
    const char *file_type = (file_id_or_path[0] == '/' || file_id_or_path[0] == '.')
                            ? "inputFileLocal" : "inputFileRemote";
    const char *field_key = (strcmp(file_type, "inputFileLocal") == 0)
                            ? "path" : "id";
    char buf[TG_PATH_MAX + 256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"sendMessage\","
             "\"chat_id\":%lld,"
             "\"input_message_content\":{"
             "\"@type\":\"inputMessageSticker\","
             "\"sticker\":{"
             "\"@type\":\"%s\",\"%s\":\"%s\"}}}",
             (long long)chat_id, file_type, field_key, file_id_or_path);
    return (int)_tg_send_raw(c, buf);
}

int tg_send_voice(tg_client_t *c, int64_t chat_id,
                  const char *path, const char *caption)
{
    char cap_buf[TG_TEXT_MAX + 128] = {0};
    if (caption && caption[0])
        snprintf(cap_buf, sizeof(cap_buf),
                 ",\"caption\":{\"@type\":\"formattedText\","
                 "\"text\":\"%s\",\"entities\":[]}", caption);
    char buf[TG_PATH_MAX + TG_TEXT_MAX + 256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"sendMessage\","
             "\"chat_id\":%lld,"
             "\"input_message_content\":{"
             "\"@type\":\"inputMessageVoiceNote\","
             "\"voice_note\":{\"@type\":\"inputFileLocal\",\"path\":\"%s\"},"
             "\"duration\":0%s}}",
             (long long)chat_id, path, cap_buf);
    return (int)_tg_send_raw(c, buf);
}

int tg_send_video_note(tg_client_t *c, int64_t chat_id, const char *path)
{
    char buf[TG_PATH_MAX + 256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"sendMessage\","
             "\"chat_id\":%lld,"
             "\"input_message_content\":{"
             "\"@type\":\"inputMessageVideoNote\","
             "\"video_note\":{\"@type\":\"inputFileLocal\",\"path\":\"%s\"},"
             "\"duration\":0,\"length\":0}}",
             (long long)chat_id, path);
    return (int)_tg_send_raw(c, buf);
}

int tg_send_location(tg_client_t *c, int64_t chat_id, double lat, double lon)
{
    char buf[256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"sendMessage\","
             "\"chat_id\":%lld,"
             "\"input_message_content\":{"
             "\"@type\":\"inputMessageLocation\","
             "\"location\":{"
             "\"@type\":\"location\","
             "\"latitude\":%.6f,"
             "\"longitude\":%.6f,"
             "\"horizontal_accuracy\":0},"
             "\"live_period\":0}}",
             (long long)chat_id, lat, lon);
    return (int)_tg_send_raw(c, buf);
}

int tg_send_contact(tg_client_t *c, int64_t chat_id,
                    const char *phone, const char *first_name,
                    const char *last_name)
{
    char buf[512];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"sendMessage\","
             "\"chat_id\":%lld,"
             "\"input_message_content\":{"
             "\"@type\":\"inputMessageContact\","
             "\"contact\":{"
             "\"@type\":\"contact\","
             "\"phone_number\":\"%s\","
             "\"first_name\":\"%s\","
             "\"last_name\":\"%s\","
             "\"vcard\":\"\","
             "\"user_id\":0}}}",
             (long long)chat_id,
             phone ? phone : "",
             first_name ? first_name : "",
             last_name  ? last_name  : "");
    return (int)_tg_send_raw(c, buf);
}

int tg_send_poll(tg_client_t *c, int64_t chat_id,
                 const char *question, const char **options, int option_count,
                 int is_anonymous)
{
    /* Build options JSON array */
    char opts_buf[TG_TEXT_MAX] = {0};
    int  pos = 0;
    pos += snprintf(opts_buf + pos, sizeof(opts_buf) - (size_t)pos, "[");
    for (int i = 0; i < option_count; i++) {
        if (i > 0)
            pos += snprintf(opts_buf + pos, sizeof(opts_buf) - (size_t)pos, ",");
        pos += snprintf(opts_buf + pos, sizeof(opts_buf) - (size_t)pos,
                        "{\"@type\":\"inputPollOption\","
                        "\"text\":{\"@type\":\"formattedText\","
                        "\"text\":\"%s\",\"entities\":[]}}",
                        options[i]);
    }
    snprintf(opts_buf + pos, sizeof(opts_buf) - (size_t)pos, "]");

    char buf[TG_TEXT_MAX + 1024];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"sendMessage\","
             "\"chat_id\":%lld,"
             "\"input_message_content\":{"
             "\"@type\":\"inputMessagePoll\","
             "\"question\":{\"@type\":\"formattedText\","
             "\"text\":\"%s\",\"entities\":[]},"
             "\"options\":%s,"
             "\"is_anonymous\":%s,"
             "\"type\":{\"@type\":\"pollTypeRegular\","
             "\"allow_multiple_answers\":false},"
             "\"open_period\":0}}",
             (long long)chat_id, question, opts_buf,
             is_anonymous ? "true" : "false");
    return (int)_tg_send_raw(c, buf);
}

int tg_send_dice(tg_client_t *c, int64_t chat_id, const char *emoji)
{
    char buf[256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"sendMessage\","
             "\"chat_id\":%lld,"
             "\"input_message_content\":{"
             "\"@type\":\"inputMessageDice\","
             "\"emoji\":\"%s\","
             "\"clear_draft\":false}}",
             (long long)chat_id, emoji ? emoji : "🎲");
    return (int)_tg_send_raw(c, buf);
}

int tg_send_chat_action(tg_client_t *c, int64_t chat_id, const char *action)
{
    const char *tdtype = _action_to_tdtype(action);
    char buf[256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"sendChatAction\","
             "\"chat_id\":%lld,"
             "\"message_thread_id\":0,"
             "\"action\":{\"@type\":\"%s\"}}",
             (long long)chat_id, tdtype);
    return (int)_tg_send_raw(c, buf);
}

int tg_copy_message(tg_client_t *c, int64_t to_chat_id,
                    int64_t from_chat_id, int64_t msg_id)
{
    char buf[256];
    snprintf(buf, sizeof(buf),
             "{\"@type\":\"forwardMessages\","
             "\"chat_id\":%lld,"
             "\"from_chat_id\":%lld,"
             "\"message_ids\":[%lld],"
             "\"send_copy\":true,"
             "\"remove_caption\":false}",
             (long long)to_chat_id,
             (long long)from_chat_id,
             (long long)msg_id);
    return (int)_tg_send_raw(c, buf);
}
