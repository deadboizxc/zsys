/*
 * zsys_utils.h  —  zsys text / formatting utilities C API
 *
 * Self-contained module extracted from zsys_core.
 * No Python.h dependency.  No external deps.
 *
 * Memory: functions returning char* must be freed with zsys_free().
 *         Functions returning char** must be freed with zsys_split_free().
 */

#ifndef ZSYS_UTILS_H
#define ZSYS_UTILS_H

#include <stddef.h>   /* size_t */
#include <stdint.h>   /* int64_t */

#ifdef __cplusplus
extern "C" {
#endif

/* ── memory ─────────────────────────────────────────────────────────────── */

/** Free a string returned by any zsys_* function. */
void zsys_free(char *ptr);

/* ── text / HTML ─────────────────────────────────────────────────────────── */

/** Escape HTML special chars: & < > " */
char *zsys_escape_html(const char *text, size_t len);

/** Strip all HTML tags; unescape basic entities. */
char *zsys_strip_html(const char *text, size_t len);

/** Truncate UTF-8 text to max_chars codepoints; append suffix if truncated. */
char *zsys_truncate_text(const char *text, size_t len,
                         size_t max_chars, const char *suffix);

/** Split text into chunks of at most max_chars codepoints each.
 *  Returns NULL-terminated array of char*.  Free with zsys_split_free(). */
char **zsys_split_text(const char *text, size_t len, size_t max_chars);

/** Free a NULL-terminated array returned by zsys_split_text or zsys_get_args. */
void   zsys_split_free(char **chunks);

/** Extract whitespace-split args after the first word.
 *  max_split == -1 means unlimited.
 *  Returns NULL-terminated array; free with zsys_split_free(). */
char **zsys_get_args(const char *text, size_t len, int max_split);

/** Format byte count as human-readable string: "1.5 KB", "3.2 MB". */
char *zsys_format_bytes(int64_t size);

/** Format seconds as "1h 2m 3s". */
char *zsys_format_duration(double seconds);

/** Format seconds as Russian human time: "1 ч. 30 мин." (short_fmt=1) or long. */
char *zsys_human_time(long seconds, int short_fmt);

/** Parse duration string "30m", "1h30m" → seconds.  Returns -1 on error. */
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

#ifdef __cplusplus
}
#endif

#endif /* ZSYS_UTILS_H */
