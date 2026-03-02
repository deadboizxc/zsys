/*
 * zsys_log.h  —  zsys log/terminal pure C API
 *
 * Self-contained: no dependency on zsys_core.h.
 * All functions returning char* heap-allocate; caller must free().
 */

#ifndef ZSYS_LOG_H
#define ZSYS_LOG_H

#ifdef __cplusplus
extern "C" {
#endif

/* Wrap text with ANSI color escape for terminal output.
 * code is an ANSI attribute string, e.g. "31" for red. */
char *zsys_ansi_color(const char *text, const char *code);

/* Format a JSON log line: {"level":"...","message":"...","ts":"..."} */
char *zsys_format_json_log(const char *level, const char *message,
                           const char *ts);

/* Build a Unicode box string around text (╔══╗ style).
 * padding = number of spaces inserted on each side of text. */
char *zsys_print_box_str(const char *text, int padding);

/* Build a separator: ch repeated length times. */
char *zsys_print_separator_str(const char *ch, int length);

/* Build a progress bar string "[###---] current/total (N%)".
 * prefix is an optional label printed before the bar (may be NULL). */
char *zsys_print_progress_str(int current, int total,
                              const char *prefix, int bar_length);

#ifdef __cplusplus
}
#endif

#endif /* ZSYS_LOG_H */
