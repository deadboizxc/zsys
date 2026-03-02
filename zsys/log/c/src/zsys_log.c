/**
 * @file zsys_log.c
 * @brief Pure-C logging and terminal-formatting functions for zsys/log.
 *
 * Self-contained — no dependency on zsys_core.c.
 * Implements: zsys_ansi_color, zsys_format_json_log, zsys_print_box_str,
 *             zsys_print_separator_str, zsys_print_progress_str.
 *
 * All returned char* are heap-allocated; caller must free().
 */

#include "zsys_log.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* ── internal dynamic buffer ──────────────────────────────────────────────── */

typedef struct {
    char   *data;
    size_t  len;
    size_t  cap;
} Buf;

static int
buf_init(Buf *b, size_t initial)
{
    b->data = malloc(initial);
    b->len  = 0;
    b->cap  = initial;
    return b->data != NULL;
}

static int
buf_write(Buf *b, const char *s, size_t n)
{
    if (b->len + n + 1 > b->cap) {
        size_t new_cap = (b->cap + n + 1) * 2;
        char *p = realloc(b->data, new_cap);
        if (!p) return 0;
        b->data = p;
        b->cap  = new_cap;
    }
    memcpy(b->data + b->len, s, n);
    b->len += n;
    b->data[b->len] = '\0';
    return 1;
}

static int buf_writec(Buf *b, char c)        { return buf_write(b, &c, 1); }
static int buf_writes(Buf *b, const char *s) { return buf_write(b, s, strlen(s)); }

static char *
buf_finish(Buf *b)
{
    char *r = b->data;
    b->data = NULL;
    return r;   /* caller must free() */
}

/* ── public API ───────────────────────────────────────────────────────────── */

char *
zsys_ansi_color(const char *text, const char *code)
{
    Buf b;
    size_t tlen = strlen(text);
    size_t clen = strlen(code);
    if (!buf_init(&b, tlen + clen + 16)) return NULL;
    buf_writes(&b, "\033[");
    buf_writes(&b, code);
    buf_writec(&b, 'm');
    buf_writes(&b, text);
    buf_writes(&b, "\033[0m");
    return buf_finish(&b);
}

char *
zsys_format_json_log(const char *level, const char *message, const char *ts)
{
    Buf b;
    if (!buf_init(&b, 256)) return NULL;
    buf_writes(&b, "{\"level\":\"");
    buf_writes(&b, level   ? level   : "");
    buf_writes(&b, "\",\"message\":\"");
    const char *p = message ? message : "";
    while (*p) {
        if      (*p == '"')  buf_writes(&b, "\\\"");
        else if (*p == '\\') buf_writes(&b, "\\\\");
        else if (*p == '\n') buf_writes(&b, "\\n");
        else if (*p == '\r') buf_writes(&b, "\\r");
        else                 buf_writec(&b, *p);
        p++;
    }
    buf_writes(&b, "\",\"ts\":\"");
    buf_writes(&b, ts ? ts : "");
    buf_writes(&b, "\"}");
    return buf_finish(&b);
}

char *
zsys_print_box_str(const char *text, int padding)
{
    size_t tlen  = strlen(text);
    size_t width = tlen + (size_t)padding * 2 + 2;
    Buf b;
    if (!buf_init(&b, width * 4 + 32)) return NULL;
    /* top border */
    buf_writes(&b, "╔");
    for (size_t i = 0; i < width; i++) buf_writes(&b, "═");
    buf_writes(&b, "╗\n║");
    for (int i = 0; i < padding; i++) buf_writec(&b, ' ');
    buf_writes(&b, text);
    for (int i = 0; i < padding; i++) buf_writec(&b, ' ');
    buf_writes(&b, "║\n╚");
    for (size_t i = 0; i < width; i++) buf_writes(&b, "═");
    buf_writes(&b, "╝");
    return buf_finish(&b);
}

char *
zsys_print_separator_str(const char *ch, int length)
{
    size_t clen = strlen(ch);
    char *r = malloc(clen * (size_t)length + 1);
    if (!r) return NULL;
    for (int i = 0; i < length; i++) memcpy(r + (size_t)i * clen, ch, clen);
    r[clen * (size_t)length] = '\0';
    return r;
}

char *
zsys_print_progress_str(int current, int total,
                        const char *prefix, int bar_length)
{
    if (total <= 0) total = 1;
    int filled = (int)((double)current / total * bar_length);
    if (filled > bar_length) filled = bar_length;
    Buf b;
    if (!buf_init(&b, (size_t)bar_length + 64)) return NULL;
    if (prefix && *prefix) {
        buf_writes(&b, prefix);
        buf_writec(&b, ' ');
    }
    buf_writec(&b, '[');
    for (int i = 0; i < filled; i++)          buf_writec(&b, '#');
    for (int i = filled; i < bar_length; i++) buf_writec(&b, '-');
    buf_writec(&b, ']');
    char pct[32];
    snprintf(pct, sizeof(pct), " %d/%d (%.0f%%)",
             current, total, (double)current / total * 100.0);
    buf_writes(&b, pct);
    return buf_finish(&b);
}
