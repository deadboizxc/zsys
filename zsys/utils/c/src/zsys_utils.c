/**
 * @file zsys_utils.c
 * @brief Pure-C utilities library for zsys — text formatting, HTML helpers.
 *
 * Extracted from zsys_core.  Self-contained, no external dependencies.
 *
 * Compiled into libzsys_utils (via CMakeLists.txt).
 */
// RU: Утилиты zsys — текст, HTML, форматирование, парсинг.

#include "zsys_utils.h"
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
