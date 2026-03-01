/*
 * zsys_core.h  —  zsys pure C API
 *
 * Platform-independent, no Python.h dependency.
 * Used by all language bindings (Python, Go, Rust, Kotlin/JNI).
 *
 * Memory: functions returning char* use zsys_free() to release.
 *         Functions writing to caller-supplied buf never allocate.
 */

#ifndef ZSYS_CORE_H
#define ZSYS_CORE_H

#include <stddef.h>   /* size_t */
#include <stdint.h>   /* int64_t */

#ifdef __cplusplus
extern "C" {
#endif

/* ── version ────────────────────────────────────────────────────────────── */

#define ZSYS_VERSION_MAJOR 1
#define ZSYS_VERSION_MINOR 0
#define ZSYS_VERSION_PATCH 0

/* ── memory ─────────────────────────────────────────────────────────────── */

/* Free a string returned by any zsys_* function. */
void zsys_free(char *ptr);


/* ── text / HTML ─────────────────────────────────────────────────────────── */

/* Escape HTML special chars: & < > "  */
char *zsys_escape_html(const char *text, size_t len);

/* Strip all HTML tags; unescape entities. */
char *zsys_strip_html(const char *text, size_t len);

/* Truncate UTF-8 text to max_chars codepoints, append suffix if truncated. */
char *zsys_truncate_text(const char *text, size_t len,
                         size_t max_chars, const char *suffix);

/* Split text into chunks of at most max_chars codepoints each.
 * Returns NULL-terminated array of char*. Free with zsys_split_free(). */
char **zsys_split_text(const char *text, size_t len, size_t max_chars);
void   zsys_split_free(char **chunks);

/* Extract whitespace-split args after the first word.
 * max_split==-1 means unlimited.
 * Returns NULL-terminated array; free with zsys_split_free(). */
char **zsys_get_args(const char *text, size_t len, int max_split);

/* Format byte count as human-readable string: "1.5 KB", "3.2 MB". */
char *zsys_format_bytes(int64_t size);

/* Format seconds as "1h 2m 3s". */
char *zsys_format_duration(double seconds);

/* Format seconds as Russian human time: "1 ч. 30 мин." (short=1) or long. */
char *zsys_human_time(long seconds, int short_fmt);

/* Parse duration string "30m", "1h30m" → seconds. Returns -1 on error. */
long zsys_parse_duration(const char *text);


/* ── HTML formatters ─────────────────────────────────────────────────────── */

char *zsys_format_bold(const char *text, size_t len, int escape);
char *zsys_format_italic(const char *text, size_t len, int escape);
char *zsys_format_code(const char *text, size_t len, int escape);
char *zsys_format_pre(const char *text, size_t len,
                      const char *lang, int escape);
char *zsys_format_link(const char *text, size_t tlen,
                       const char *url,  size_t ulen, int escape);
char *zsys_format_mention(const char *text, size_t len,
                          int64_t user_id, int escape);
char *zsys_format_underline(const char *text, size_t len);
char *zsys_format_strikethrough(const char *text, size_t len);
char *zsys_format_spoiler(const char *text, size_t len);
char *zsys_format_quote(const char *text, size_t len);


/* ── error formatting ────────────────────────────────────────────────────── */

/* Build HTML error message from extracted exception fields.
 * Any of cause_type/cause_text/suffix may be NULL or "".
 * Truncates to max_length bytes (0 = no limit). */
char *zsys_format_exc_html(
    const char *error_type, size_t et_len,
    const char *error_text, size_t etx_len,
    const char *cause_type, size_t ct_len,
    const char *cause_text, size_t ctx_len,
    const char *suffix,     size_t sf_len,
    size_t      max_length
);


/* ── logging / terminal ──────────────────────────────────────────────────── */

/* Wrap text with ANSI color escape for terminal output. */
char *zsys_ansi_color(const char *text, const char *code);

/* Format a JSON log line: {"level":"...", "message":"...", "ts":"..."} */
char *zsys_format_json_log(const char *level, const char *message,
                           const char *ts);

/* Build a box string around text (╔══╗ style). padding = spaces each side. */
char *zsys_print_box_str(const char *text, int padding);

/* Build a separator: char repeated length times. */
char *zsys_print_separator_str(const char *ch, int length);

/* Build a progress bar string. */
char *zsys_print_progress_str(int current, int total,
                              const char *prefix, int bar_length);


/* ── routing / prefix matching ───────────────────────────────────────────── */

/* Returns 1 if text starts with one of the prefixes and the rest matches
 * one of the triggers (case-insensitive ASCII). prefixes and triggers are
 * NULL-terminated arrays of C strings. */
int zsys_match_prefix(const char *text,
                      const char **prefixes, int n_prefixes,
                      const char **triggers, int n_triggers);


/* ── meta comment parser ─────────────────────────────────────────────────── */

/* Parse module meta comments from Python source code.
 * Returns key=value pairs as flat NULL-terminated array:
 *   { "name", "afk", "description", "AFK module", NULL }
 * Free with zsys_meta_free(). */
char **zsys_parse_meta_comments(const char *source, size_t len);
void   zsys_meta_free(char **pairs);


/* ── help text builder ───────────────────────────────────────────────────── */

/* Build a help text for a module.
 * cmds is NULL-terminated array of alternating "cmd_name", "cmd_desc" pairs.
 * prefix is the command prefix (e.g. "."). */
char *zsys_build_help_text(const char *module_name,
                           const char **cmds, /* name, desc, name, desc, NULL */
                           const char *prefix);

#ifdef __cplusplus
}
#endif

#endif /* ZSYS_CORE_H */
