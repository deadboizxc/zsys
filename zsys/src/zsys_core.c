/**
 * @file zsys_core.c
 * @brief Pure-C core library for zsys — no Python.h dependency.
 *
 * Implements text formatting, HTML escaping/stripping, duration parsing,
 * argument splitting, terminal box/progress rendering, prefix matching,
 * meta comment extraction, and help-text generation.
 *
 * Compiled into libzsys_core (via CMakeLists.txt).
 * Python bindings are provided by _zsys_core.c.
 */
// RU: Чистая C-библиотека zsys без зависимости от Python.h.
//     Текстовые утилиты, форматирование, парсинг длительности, терминальные утилиты.

#include "../include/zsys_core.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>
#include <stdint.h>

/* ════════ Internal Helpers ════════ */

typedef struct {
    char   *data;
    size_t  len;
    size_t  cap;
} Buf;

/**
 * @brief Initialise a dynamic byte buffer.
 * @param b       Pointer to the Buf struct to initialise.
 * @param initial Initial capacity in bytes.
 * @return 1 on success, 0 on allocation failure.
 */
// RU: Инициализировать динамический буфер заданной ёмкости.
static int
buf_init(Buf *b, size_t initial)
{
    b->data = malloc(initial);
    b->len  = 0;
    b->cap  = initial;
    return b->data != NULL;
}

/**
 * @brief Append n bytes from s to the buffer, growing it as needed.
 * @param b Pointer to the buffer.
 * @param s Source data.
 * @param n Number of bytes to append.
 * @return 1 on success, 0 on allocation failure.
 */
// RU: Дописать n байт из s в буфер, расширяя при необходимости.
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

/**
 * @brief Append a single character to the buffer.
 * @param b Pointer to the buffer.
 * @param c Character to append.
 * @return 1 on success, 0 on allocation failure.
 */
// RU: Добавить один символ в буфер.
/**
 * @brief Append a NUL-terminated string to the buffer.
 * @param b Pointer to the buffer.
 * @param s NUL-terminated string to append.
 * @return 1 on success, 0 on allocation failure.
 */
// RU: Добавить C-строку (с нулём) в буфер.
static int buf_writec(Buf *b, char c)        { return buf_write(b, &c, 1); }
static int buf_writes(Buf *b, const char *s) { return buf_write(b, s, strlen(s)); }

/**
 * @brief Detach and return the buffer's internal string, transferring ownership.
 * @param b Pointer to the buffer (invalidated after this call).
 * @return Heap-allocated NUL-terminated string; caller must free().
 */
// RU: Извлечь строку из буфера, передав владение вызывающей стороне.
static char *
buf_finish(Buf *b)
{
    char *r = b->data;
    b->data = NULL;
    return r;   /* caller must free() */
    // RU: вызывающая сторона обязана освободить память через free()
}

/**
 * @brief Release memory held by a buffer without transferring ownership.
 * @param b Pointer to the buffer to free.
 */
// RU: Освободить память буфера без передачи владения.
static void buf_free(Buf *b) { free(b->data); b->data = NULL; }

/**
 * @brief Advance pointer past leading spaces and tabs.
 * @param p Pointer into a C string.
 * @return Pointer to the first non-whitespace character.
 */
// RU: Пропустить ведущие пробелы и символы табуляции.
static const char *
skip_ws(const char *p)
{
    while (*p == ' ' || *p == '\t') p++;
    return p;
}

/* ════════ Memory ════════ */

/**
 * @brief Free a heap pointer returned by any zsys_* function.
 * @param ptr Pointer to free (may be NULL).
 */
// RU: Освободить указатель, возвращённый любой функцией zsys_*.
void zsys_free(char *ptr) { free(ptr); }

/* ════════ Text / HTML ════════ */

/**
 * @brief Escape special HTML characters in a byte string.
 * @param text Input byte string (need not be NUL-terminated).
 * @param len  Number of bytes in text.
 * @return Heap-allocated escaped string, or NULL on allocation failure.
 */
// RU: Экранировать спецсимволы HTML (&, <, >, ").
char *
zsys_escape_html(const char *text, size_t len)
{
    Buf b;
    if (!buf_init(&b, len + 32)) return NULL;
    for (size_t i = 0; i < len; i++) {
        switch (text[i]) {
        case '&':  buf_writes(&b, "&amp;");  break;
        case '<':  buf_writes(&b, "&lt;");   break;
        case '>':  buf_writes(&b, "&gt;");   break;
        case '"':  buf_writes(&b, "&quot;"); break;
        default:   buf_writec(&b, text[i]);  break;
        }
    }
    return buf_finish(&b);
}

/**
 * @brief Strip HTML tags and unescape basic HTML entities from a byte string.
 * @param text Input byte string.
 * @param len  Number of bytes in text.
 * @return Heap-allocated plain-text string, or NULL on allocation failure.
 */
// RU: Удалить HTML-теги и раскодировать базовые HTML-сущности.
char *
zsys_strip_html(const char *text, size_t len)
{
    Buf b;
    if (!buf_init(&b, len + 4)) return NULL;
    int in_tag = 0;
    for (size_t i = 0; i < len; i++) {
        if (text[i] == '<') {
            in_tag = 1;
        } else if (text[i] == '>') {
            in_tag = 0;
        } else if (!in_tag) {
            /* simple entity unescape */
            // RU: Простое раскодирование HTML-сущностей.
            if (text[i] == '&') {
                if (strncmp(text + i, "&amp;",  5) == 0) { buf_writec(&b, '&'); i += 4; }
                else if (strncmp(text + i, "&lt;",   4) == 0) { buf_writec(&b, '<'); i += 3; }
                else if (strncmp(text + i, "&gt;",   4) == 0) { buf_writec(&b, '>'); i += 3; }
                else if (strncmp(text + i, "&quot;", 6) == 0) { buf_writec(&b, '"'); i += 5; }
                else buf_writec(&b, text[i]);
            } else {
                buf_writec(&b, text[i]);
            }
        }
    }
    return buf_finish(&b);
}

/**
 * @brief Truncate text to at most max_chars UTF-8 codepoints, appending suffix if cut.
 * @param text      Input byte string.
 * @param len       Byte length of text.
 * @param max_chars Maximum number of Unicode codepoints to keep.
 * @param suffix    String appended when truncation occurs (may be NULL).
 * @return Heap-allocated result string, or NULL on allocation failure.
 */
// RU: Усечь текст до max_chars кодовых точек UTF-8, добавив суффикс при необходимости.
char *
zsys_truncate_text(const char *text, size_t len, size_t max_chars, const char *suffix)
{
    /* count UTF-8 codepoints */
    // RU: Подсчёт кодовых точек UTF-8.
    size_t chars = 0;
    size_t i = 0;
    size_t cut = len;
    while (i < len) {
        if (chars == max_chars) { cut = i; break; }
        unsigned char c = (unsigned char)text[i];
        if      (c < 0x80) i += 1;
        else if (c < 0xE0) i += 2;
        else if (c < 0xF0) i += 3;
        else               i += 4;
        chars++;
    }
    if (chars <= max_chars) {
        char *r = malloc(len + 1);
        if (!r) return NULL;
        memcpy(r, text, len);
        r[len] = '\0';
        return r;
    }
    size_t suf_len = suffix ? strlen(suffix) : 0;
    char *r = malloc(cut + suf_len + 1);
    if (!r) return NULL;
    memcpy(r, text, cut);
    if (suf_len) memcpy(r + cut, suffix, suf_len);
    r[cut + suf_len] = '\0';
    return r;
}

/**
 * @brief Split text into chunks of at most max_chars UTF-8 codepoints each.
 * @param text      Input byte string.
 * @param len       Byte length of text.
 * @param max_chars Maximum codepoints per chunk (0 defaults to 4096).
 * @return NULL-terminated array of heap-allocated chunk strings, or NULL on failure.
 */
// RU: Разбить текст на части по max_chars кодовых точек UTF-8.
char **
zsys_split_text(const char *text, size_t len, size_t max_chars)
{
    if (max_chars == 0) max_chars = 4096;
    /* worst case: len/1 + 1 chunks */
    // RU: В худшем случае: len/1 + 1 фрагментов.
    size_t cap = len / max_chars + 2;
    char **chunks = calloc(cap + 1, sizeof(char *));
    if (!chunks) return NULL;
    size_t n = 0;
    size_t i = 0;
    while (i < len) {
        size_t start = i;
        size_t chars = 0;
        while (i < len && chars < max_chars) {
            unsigned char c = (unsigned char)text[i];
            if      (c < 0x80) i += 1;
            else if (c < 0xE0) i += 2;
            else if (c < 0xF0) i += 3;
            else               i += 4;
            chars++;
        }
        size_t chunk_len = i - start;
        char *chunk = malloc(chunk_len + 1);
        if (!chunk) { zsys_split_free(chunks); return NULL; }
        memcpy(chunk, text + start, chunk_len);
        chunk[chunk_len] = '\0';
        if (n >= cap) {
            cap *= 2;
            char **tmp = realloc(chunks, (cap + 1) * sizeof(char *));
            if (!tmp) { free(chunk); zsys_split_free(chunks); return NULL; }
            chunks = tmp;
        }
        chunks[n++] = chunk;
    }
    chunks[n] = NULL;
    return chunks;
}

/**
 * @brief Free a NULL-terminated array of strings produced by zsys_split_text or zsys_get_args.
 * @param chunks NULL-terminated array to free (may be NULL).
 */
// RU: Освободить NULL-terminated массив строк от zsys_split_text / zsys_get_args.
void
zsys_split_free(char **chunks)
{
    if (!chunks) return;
    for (int i = 0; chunks[i]; i++) free(chunks[i]);
    free(chunks);
}

/**
 * @brief Extract positional arguments from a command string, skipping the first word.
 * @param text      Full command string (e.g. "/cmd arg1 arg2").
 * @param len       Byte length of text.
 * @param max_split Maximum number of splits (-1 for unlimited).
 * @return NULL-terminated array of heap-allocated argument strings, or NULL on failure.
 */
// RU: Извлечь позиционные аргументы из строки команды, пропустив первое слово.
char **
zsys_get_args(const char *text, size_t len, int max_split)
{
    /* skip first word */
    // RU: Пропустить первое слово (имя команды).
    size_t i = 0;
    while (i < len && text[i] != ' ') i++;
    while (i < len && text[i] == ' ') i++;
    const char *rest = text + i;
    size_t rlen = len - i;

    size_t cap = 16;
    char **args = calloc(cap + 1, sizeof(char *));
    if (!args) return NULL;
    size_t n = 0;
    size_t j = 0;
    while (j < rlen) {
        while (j < rlen && rest[j] == ' ') j++;
        if (j >= rlen) break;
        if (max_split >= 0 && (int)n >= max_split) {
            /* rest as single arg */
            // RU: Оставшийся текст — один аргумент целиком.
            size_t alen = rlen - j;
            char *a = malloc(alen + 1);
            if (!a) { zsys_split_free(args); return NULL; }
            memcpy(a, rest + j, alen);
            a[alen] = '\0';
            if (n >= cap) { cap *= 2; char **t = realloc(args, (cap+1)*sizeof(char*)); if(!t){free(a);zsys_split_free(args);return NULL;} args=t; }
            args[n++] = a;
            break;
        }
        size_t start = j;
        while (j < rlen && rest[j] != ' ') j++;
        size_t alen = j - start;
        char *a = malloc(alen + 1);
        if (!a) { zsys_split_free(args); return NULL; }
        memcpy(a, rest + start, alen);
        a[alen] = '\0';
        if (n >= cap) { cap *= 2; char **t = realloc(args, (cap+1)*sizeof(char*)); if(!t){free(a);zsys_split_free(args);return NULL;} args=t; }
        args[n++] = a;
    }
    args[n] = NULL;
    return args;
}

/**
 * @brief Format a byte count as a human-readable string (B, KB, MB, …).
 * @param size Signed byte count.
 * @return Heap-allocated formatted string, or NULL on allocation failure.
 */
// RU: Форматировать размер в байтах в читаемый вид (Б, КБ, МБ, …).
char *
zsys_format_bytes(int64_t size)
{
    char buf[64];
    const char *units[] = {"B", "KB", "MB", "GB", "TB", "PB"};
    int u = 0;
    double s = (double)(size < 0 ? -size : size);
    int neg = size < 0;
    while (s >= 1024.0 && u < 5) { s /= 1024.0; u++; }
    if (u == 0)
        snprintf(buf, sizeof(buf), "%s%lld %s", neg ? "-" : "", (long long)(size < 0 ? -size : size), units[0]);
    else
        snprintf(buf, sizeof(buf), "%s%.1f %s", neg ? "-" : "", s, units[u]);
    char *r = malloc(strlen(buf) + 1);
    if (r) strcpy(r, buf);
    return r;
}

/**
 * @brief Format a duration in seconds as "Xh Xm Xs".
 * @param seconds Duration in seconds (floating-point).
 * @return Heap-allocated formatted string, or NULL on allocation failure.
 */
// RU: Форматировать длительность в секундах в вид «Xч Xмин Xсек».
char *
zsys_format_duration(double seconds)
{
    char buf[64];
    int s = (int)seconds;
    int h = s / 3600; s %= 3600;
    int m = s / 60;   s %= 60;
    if (h > 0)       snprintf(buf, sizeof(buf), "%dh %dm %ds", h, m, s);
    else if (m > 0)  snprintf(buf, sizeof(buf), "%dm %ds", m, s);
    else             snprintf(buf, sizeof(buf), "%ds", s);
    char *r = malloc(strlen(buf) + 1);
    if (r) strcpy(r, buf);
    return r;
}

/**
 * @brief Format a duration in seconds as a human-readable Russian string.
 * @param seconds   Duration in whole seconds.
 * @param short_fmt Non-zero for abbreviated form, 0 for full word form.
 * @return Heap-allocated formatted string, or NULL on allocation failure.
 */
// RU: Форматировать длительность в секундах в читаемый русский текст.
char *
zsys_human_time(long seconds, int short_fmt)
{
    char buf[128];
    long s = seconds;
    long h = s / 3600; s %= 3600;
    long m = s / 60;   s %= 60;
    if (short_fmt) {
        if (h > 0)      snprintf(buf, sizeof(buf), "%ld ч. %ld мин.", h, m);
        else if (m > 0) snprintf(buf, sizeof(buf), "%ld мин. %ld сек.", m, s);
        else            snprintf(buf, sizeof(buf), "%ld сек.", s);
    } else {
        if (h > 0)      snprintf(buf, sizeof(buf), "%ld часов %ld минут %ld секунд", h, m, s);
        else if (m > 0) snprintf(buf, sizeof(buf), "%ld минут %ld секунд", m, s);
        else            snprintf(buf, sizeof(buf), "%ld секунд", s);
    }
    char *r = malloc(strlen(buf) + 1);
    if (r) strcpy(r, buf);
    return r;
}

/**
 * @brief Parse a human duration string such as "1d2h3m4s" into total seconds.
 * @param text NUL-terminated duration string.
 * @return Total seconds, or -1 on parse error.
 */
// RU: Разобрать строку вида «1d2h3m4s» в общее количество секунд.
long
zsys_parse_duration(const char *text)
{
    long total = 0;
    long cur   = 0;
    const char *p = text;
    while (*p) {
        if (*p >= '0' && *p <= '9') {
            cur = cur * 10 + (*p - '0');
        } else {
            switch (*p) {
            case 'd': total += cur * 86400; cur = 0; break;
            case 'h': total += cur * 3600;  cur = 0; break;
            case 'm': total += cur * 60;    cur = 0; break;
            case 's': total += cur;         cur = 0; break;
            default:  if (*p != ' ') return -1;
            }
        }
        p++;
    }
    total += cur; /* bare number treated as seconds */
    // RU: Число без суффикса считается секундами.
    return total;
}

/* ════════ HTML Formatters ════════ */

/**
 * @brief Wrap text between an opening and a closing HTML tag.
 * @param tag_open  Opening tag string (e.g. "<b>").
 * @param tag_close Closing tag string (e.g. "</b>").
 * @param text      Content to wrap.
 * @param len       Byte length of text.
 * @param escape    Non-zero to HTML-escape text before wrapping.
 * @return Heap-allocated wrapped string, or NULL on allocation failure.
 */
// RU: Обернуть текст в открывающий и закрывающий HTML-теги.
static char *
wrap_tag(const char *tag_open, const char *tag_close,
         const char *text, size_t len, int escape)
{
    Buf b;
    if (!buf_init(&b, len + 32)) return NULL;
    buf_writes(&b, tag_open);
    if (escape) {
        char *esc = zsys_escape_html(text, len);
        if (!esc) { buf_free(&b); return NULL; }
        buf_writes(&b, esc);
        free(esc);
    } else {
        buf_write(&b, text, len);
    }
    buf_writes(&b, tag_close);
    return buf_finish(&b);
}

/**
 * @brief Wrap text in HTML bold tags (<b>…</b>).
 * @param text   Content text.
 * @param len    Byte length of text.
 * @param escape Non-zero to HTML-escape the content.
 * @return Heap-allocated string, or NULL on failure.
 */
// RU: Обернуть текст в <b>…</b>.
char *zsys_format_bold(const char *text, size_t len, int escape)
    { return wrap_tag("<b>", "</b>", text, len, escape); }
/**
 * @brief Wrap text in HTML italic tags (<i>…</i>).
 * @param text   Content text.
 * @param len    Byte length of text.
 * @param escape Non-zero to HTML-escape the content.
 * @return Heap-allocated string, or NULL on failure.
 */
// RU: Обернуть текст в <i>…</i>.
char *zsys_format_italic(const char *text, size_t len, int escape)
    { return wrap_tag("<i>", "</i>", text, len, escape); }
/**
 * @brief Wrap text in HTML inline-code tags (<code>…</code>).
 * @param text   Content text.
 * @param len    Byte length of text.
 * @param escape Non-zero to HTML-escape the content.
 * @return Heap-allocated string, or NULL on failure.
 */
// RU: Обернуть текст в <code>…</code>.
char *zsys_format_code(const char *text, size_t len, int escape)
    { return wrap_tag("<code>", "</code>", text, len, escape); }
/**
 * @brief Wrap text in HTML underline tags (<u>…</u>).
 * @param text Content text.
 * @param len  Byte length of text.
 * @return Heap-allocated string, or NULL on failure.
 */
// RU: Обернуть текст в <u>…</u>.
char *zsys_format_underline(const char *text, size_t len)
    { return wrap_tag("<u>", "</u>", text, len, 0); }
/**
 * @brief Wrap text in HTML strikethrough tags (<s>…</s>).
 * @param text Content text.
 * @param len  Byte length of text.
 * @return Heap-allocated string, or NULL on failure.
 */
// RU: Обернуть текст в <s>…</s> (зачёркнутый).
char *zsys_format_strikethrough(const char *text, size_t len)
    { return wrap_tag("<s>", "</s>", text, len, 0); }
/**
 * @brief Wrap text in spoiler tags (<spoiler>…</spoiler>).
 * @param text Content text.
 * @param len  Byte length of text.
 * @return Heap-allocated string, or NULL on failure.
 */
// RU: Обернуть текст в <spoiler>…</spoiler>.
char *zsys_format_spoiler(const char *text, size_t len)
    { return wrap_tag("<spoiler>", "</spoiler>", text, len, 0); }
/**
 * @brief Wrap text in HTML blockquote tags (<blockquote>…</blockquote>).
 * @param text Content text.
 * @param len  Byte length of text.
 * @return Heap-allocated string, or NULL on failure.
 */
// RU: Обернуть текст в <blockquote>…</blockquote>.
char *zsys_format_quote(const char *text, size_t len)
    { return wrap_tag("<blockquote>", "</blockquote>", text, len, 0); }

/**
 * @brief Wrap text in a <pre> block, optionally with a language class.
 * @param text   Content text.
 * @param len    Byte length of text.
 * @param lang   Language identifier for syntax highlighting (may be NULL or "").
 * @param escape Non-zero to HTML-escape the content.
 * @return Heap-allocated HTML string, or NULL on allocation failure.
 */
// RU: Обернуть текст в <pre> (с указанием языка для подсветки синтаксиса).
char *
zsys_format_pre(const char *text, size_t len, const char *lang, int escape)
{
    Buf b;
    if (!buf_init(&b, len + 64)) return NULL;
    if (lang && *lang) {
        buf_writes(&b, "<pre><code class=\"language-");
        buf_writes(&b, lang);
        buf_writes(&b, "\">");
    } else {
        buf_writes(&b, "<pre>");
    }
    if (escape) {
        char *esc = zsys_escape_html(text, len);
        if (!esc) { buf_free(&b); return NULL; }
        buf_writes(&b, esc);
        free(esc);
    } else {
        buf_write(&b, text, len);
    }
    if (lang && *lang) buf_writes(&b, "</code></pre>");
    else               buf_writes(&b, "</pre>");
    return buf_finish(&b);
}

/**
 * @brief Build an HTML hyperlink <a href="url">text</a>.
 * @param text   Link label text.
 * @param tlen   Byte length of text.
 * @param url    Target URL.
 * @param ulen   Byte length of url.
 * @param escape Non-zero to HTML-escape the label text.
 * @return Heap-allocated HTML anchor string, or NULL on allocation failure.
 */
// RU: Создать HTML-ссылку <a href="url">text</a>.
char *
zsys_format_link(const char *text, size_t tlen,
                 const char *url,  size_t ulen, int escape)
{
    Buf b;
    if (!buf_init(&b, tlen + ulen + 32)) return NULL;
    buf_writes(&b, "<a href=\"");
    buf_write(&b, url, ulen);
    buf_writes(&b, "\">");
    if (escape) {
        char *esc = zsys_escape_html(text, tlen);
        if (!esc) { buf_free(&b); return NULL; }
        buf_writes(&b, esc);
        free(esc);
    } else {
        buf_write(&b, text, tlen);
    }
    buf_writes(&b, "</a>");
    return buf_finish(&b);
}

/**
 * @brief Build an inline Telegram mention link for a user ID.
 * @param text    Display name of the user.
 * @param len     Byte length of text.
 * @param user_id Telegram user ID.
 * @param escape  Non-zero to HTML-escape the display name.
 * @return Heap-allocated HTML anchor string, or NULL on allocation failure.
 */
// RU: Создать inline-упоминание пользователя Telegram по user_id.
char *
zsys_format_mention(const char *text, size_t len, int64_t user_id, int escape)
{
    char url[64];
    snprintf(url, sizeof(url), "tg://user?id=%lld", (long long)user_id);
    return zsys_format_link(text, len, url, strlen(url), escape);
}

/* ════════ Error Formatting ════════ */

/**
 * @brief Format an exception (and optional cause) as an HTML string.
 * @param error_type  Exception class name.
 * @param et_len      Byte length of error_type.
 * @param error_text  Exception message.
 * @param etx_len     Byte length of error_text.
 * @param cause_type  Cause exception class name (may be NULL).
 * @param ct_len      Byte length of cause_type.
 * @param cause_text  Cause exception message (may be NULL).
 * @param ctx_len     Byte length of cause_text.
 * @param suffix      Additional text appended after the error (may be NULL).
 * @param sf_len      Byte length of suffix.
 * @param max_length  If non-zero, truncate result to this many bytes.
 * @return Heap-allocated HTML string, or NULL on allocation failure.
 */
// RU: Форматировать исключение (и его причину) в HTML-строку для вывода.
char *
zsys_format_exc_html(
    const char *error_type, size_t et_len,
    const char *error_text, size_t etx_len,
    const char *cause_type, size_t ct_len,
    const char *cause_text, size_t ctx_len,
    const char *suffix,     size_t sf_len,
    size_t      max_length)
{
    Buf b;
    if (!buf_init(&b, 256)) return NULL;

    buf_writes(&b, "<b>");
    if (error_type && et_len > 0) buf_write(&b, error_type, et_len);
    buf_writes(&b, "</b>");
    if (error_text && etx_len > 0) {
        buf_writes(&b, ": <code>");
        char *esc = zsys_escape_html(error_text, etx_len);
        if (esc) { buf_writes(&b, esc); free(esc); }
        buf_writes(&b, "</code>");
    }
    if (cause_type && ct_len > 0) {
        buf_writes(&b, "\n<b>Caused by: ");
        buf_write(&b, cause_type, ct_len);
        buf_writes(&b, "</b>");
        if (cause_text && ctx_len > 0) {
            buf_writes(&b, ": <code>");
            char *esc = zsys_escape_html(cause_text, ctx_len);
            if (esc) { buf_writes(&b, esc); free(esc); }
            buf_writes(&b, "</code>");
        }
    }
    if (suffix && sf_len > 0) {
        buf_writec(&b, '\n');
        buf_write(&b, suffix, sf_len);
    }

    char *result = buf_finish(&b);
    if (max_length > 0 && strlen(result) > max_length) {
        result[max_length] = '\0';
    }
    return result;
}

/* ════════ Logging / Terminal ════════ */

/**
 * @brief Wrap text with ANSI escape codes for terminal colour.
 * @param text The string to colour.
 * @param code ANSI colour/attribute code (e.g. "31" for red).
 * @return Heap-allocated ANSI-coloured string, or NULL on allocation failure.
 */
// RU: Обернуть текст ANSI-последовательностями для цветного вывода в терминале.
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

/**
 * @brief Produce a single-line JSON log entry with level, message, and timestamp.
 * @param level   Log level string (e.g. "INFO").
 * @param message Log message (special JSON characters are escaped).
 * @param ts      ISO-8601 timestamp string.
 * @return Heap-allocated JSON string, or NULL on allocation failure.
 */
// RU: Сформировать однострочную JSON-запись лога с уровнем, сообщением и временем.
char *
zsys_format_json_log(const char *level, const char *message, const char *ts)
{
    Buf b;
    if (!buf_init(&b, 256)) return NULL;
    buf_writes(&b, "{\"level\":\"");
    buf_writes(&b, level   ? level   : "");
    buf_writes(&b, "\",\"message\":\"");
    /* escape message for JSON */
    // RU: Экранировать специальные символы сообщения для JSON.
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

/**
 * @brief Render a Unicode box around a single-line text string.
 * @param text    Text to enclose.
 * @param padding Number of space characters inserted on each side of the text.
 * @return Heap-allocated multi-line box string, or NULL on allocation failure.
 */
// RU: Нарисовать Unicode-рамку вокруг однострочного текста.
char *
zsys_print_box_str(const char *text, int padding)
{
    size_t tlen = strlen(text);
    size_t width = tlen + padding * 2 + 2;
    Buf b;
    if (!buf_init(&b, width * 4 + 32)) return NULL;
    /* top border */
    // RU: Верхняя граница рамки.
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

/**
 * @brief Build a separator string by repeating a character (or multi-byte sequence) n times.
 * @param ch     Repeated character or UTF-8 sequence.
 * @param length Number of repetitions.
 * @return Heap-allocated separator string, or NULL on allocation failure.
 */
// RU: Создать разделитель повторением символа (или UTF-8 последовательности) n раз.
char *
zsys_print_separator_str(const char *ch, int length)
{
    size_t clen = strlen(ch);
    char *r = malloc(clen * length + 1);
    if (!r) return NULL;
    for (int i = 0; i < length; i++) memcpy(r + i * clen, ch, clen);
    r[clen * length] = '\0';
    return r;
}

/**
 * @brief Render a text progress bar as a string.
 * @param current    Current progress value.
 * @param total      Total (100%) value.
 * @param prefix     Optional label printed before the bar (may be NULL or "").
 * @param bar_length Number of characters in the bar body.
 * @return Heap-allocated progress string "[###---] N/M (X%)", or NULL on failure.
 */
// RU: Отрисовать текстовый прогресс-бар «[###---] N/M (X%)».
char *
zsys_print_progress_str(int current, int total,
                        const char *prefix, int bar_length)
{
    if (total <= 0) total = 1;
    int filled = (int)((double)current / total * bar_length);
    if (filled > bar_length) filled = bar_length;
    Buf b;
    if (!buf_init(&b, bar_length + 64)) return NULL;
    if (prefix && *prefix) {
        buf_writes(&b, prefix);
        buf_writec(&b, ' ');
    }
    buf_writec(&b, '[');
    for (int i = 0; i < filled; i++)            buf_writec(&b, '#');
    for (int i = filled; i < bar_length; i++)   buf_writec(&b, '-');
    buf_writec(&b, ']');
    char pct[32];
    snprintf(pct, sizeof(pct), " %d/%d (%.0f%%)",
             current, total, (double)current / total * 100.0);
    buf_writes(&b, pct);
    return buf_finish(&b);
}

/* ════════ Routing ════════ */

/**
 * @brief Test whether text starts with any of the given prefixes followed by any trigger word.
 * @param text        Input message text.
 * @param prefixes    Array of prefix strings (e.g. {"/", "!"}).
 * @param n_prefixes  Length of the prefixes array.
 * @param triggers    Array of trigger/command words to match after the prefix.
 * @param n_triggers  Length of the triggers array.
 * @return 1 if a match is found, 0 otherwise.
 */
// RU: Проверить, начинается ли текст с любого из префиксов, за которым следует слово-триггер.
int
zsys_match_prefix(const char *text,
                  const char **prefixes, int n_prefixes,
                  const char **triggers, int n_triggers)
{
    if (!text || !*text) return 0;
    size_t tlen = strlen(text);
    for (int pi = 0; pi < n_prefixes; pi++) {
        const char *pfx = prefixes[pi];
        size_t plen = strlen(pfx);
        if (tlen <= plen) continue;
        if (strncmp(text, pfx, plen) != 0) continue;
        /* match trigger after prefix (case-insensitive) */
        // RU: Сопоставить слово-триггер после префикса без учёта регистра.
        const char *rest = text + plen;
        for (int ti = 0; ti < n_triggers; ti++) {
            const char *trg = triggers[ti];
            size_t trlen = strlen(trg);
            if (strlen(rest) < trlen) continue;
            size_t match = 1;
            for (size_t i = 0; i < trlen; i++) {
                if (tolower((unsigned char)rest[i]) != tolower((unsigned char)trg[i])) {
                    match = 0; break;
                }
            }
            if (match) {
                char next = rest[trlen];
                if (next == '\0' || next == ' ') return 1;
            }
        }
    }
    return 0;
}

/* ════════ Meta Comment Parser ════════ */

/**
 * @brief Extract key–value metadata from Python-style comment lines in source text.
 *
 * Recognises lines of the form:
 *   # @key: value
 *   # key: value
 *   ## @key: value
 *
 * @param source Source text to scan.
 * @param len    Byte length of source.
 * @return NULL-terminated flat array [key0, val0, key1, val1, …, NULL],
 *         or NULL on allocation failure.
 */
// RU: Извлечь пары ключ–значение из строк комментариев в исходном тексте.
char **
zsys_parse_meta_comments(const char *source, size_t len)
{
    size_t cap = 16;
    char **pairs = calloc(cap + 1, sizeof(char *));
    if (!pairs) return NULL;
    size_t n = 0;

    const char *p   = source;
    const char *end = source + len;

    while (p < end) {
        /* find start of line */
        // RU: Найти начало строки.
        const char *line = p;
        while (p < end && *p != '\n') p++;
        size_t llen = (size_t)(p - line);
        if (p < end) p++; /* skip newline character */
        // RU: Пропустить символ новой строки.

        const char *lp = skip_ws(line);
        /* check for: # @key: value  OR  # key: value  OR  ## @key: value */
        // RU: Допустимые форматы: # @ключ: значение, # ключ: значение, ## @ключ: значение.
        if (*lp != '#') continue;
        lp++;
        if (*lp == '#') lp++;
        lp = skip_ws(lp);
        if (*lp == '@') lp++;
        /* read key */
        // RU: Читать ключ до символа ':' или пробела.
        const char *kstart = lp;
        while (*lp && *lp != ':' && *lp != ' ' && lp < line + llen) lp++;
        if (*lp != ':') continue;
        size_t klen = (size_t)(lp - kstart);
        if (klen == 0) continue;
        lp++; /* skip : */
        lp = skip_ws(lp);
        /* read value until end of line */
        // RU: Читать значение до конца строки (без завершающих пробелов).
        const char *vstart = lp;
        const char *vend   = line + llen;
        while (vend > vstart && (*(vend-1) == ' ' || *(vend-1) == '\r' || *(vend-1) == '\t'))
            vend--;
        size_t vlen = (size_t)(vend - vstart);

        char *key = malloc(klen + 1);
        char *val = malloc(vlen + 1);
        if (!key || !val) { free(key); free(val); zsys_meta_free(pairs); return NULL; }
        memcpy(key, kstart, klen); key[klen] = '\0';
        memcpy(val, vstart, vlen); val[vlen] = '\0';

        if (n + 2 > cap) {
            cap *= 2;
            char **tmp = realloc(pairs, (cap + 1) * sizeof(char *));
            if (!tmp) { free(key); free(val); zsys_meta_free(pairs); return NULL; }
            pairs = tmp;
        }
        pairs[n++] = key;
        pairs[n++] = val;
    }
    pairs[n] = NULL;
    return pairs;
}

/**
 * @brief Free a flat key–value array returned by zsys_parse_meta_comments.
 * @param pairs NULL-terminated array to free (may be NULL).
 */
// RU: Освободить массив пар ключ–значение от zsys_parse_meta_comments.
void
zsys_meta_free(char **pairs)
{
    if (!pairs) return;
    for (int i = 0; pairs[i]; i++) free(pairs[i]);
    free(pairs);
}

/* ════════ Help Text Builder ════════ */

/**
 * @brief Build an HTML help text listing commands with their descriptions.
 * @param module_name Module or plugin name displayed as a bold header.
 * @param cmds        NULL-terminated flat array of [cmd, description, cmd, description, …].
 * @param prefix      Command prefix prepended before each command (may be NULL or "").
 * @return Heap-allocated HTML string, or NULL on allocation failure.
 */
// RU: Собрать HTML-текст справки: заголовок модуля и список команд с описаниями.
char *
zsys_build_help_text(const char *module_name,
                     const char **cmds,
                     const char *prefix)
{
    Buf b;
    if (!buf_init(&b, 256)) return NULL;
    buf_writes(&b, "<b>");
    buf_writes(&b, module_name ? module_name : "");
    buf_writes(&b, "</b>\n");
    if (!cmds) return buf_finish(&b);
    for (int i = 0; cmds[i] && cmds[i+1]; i += 2) {
        buf_writes(&b, "  ");
        if (prefix && *prefix) buf_writes(&b, prefix);
        buf_writes(&b, "<code>");
        buf_writes(&b, cmds[i]);
        buf_writes(&b, "</code> — ");
        buf_writes(&b, cmds[i+1]);
        buf_writec(&b, '\n');
    }
    return buf_finish(&b);
}
