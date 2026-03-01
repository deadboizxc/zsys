/*
 * _zsys_core.c  —  fast C hot paths for zsys
 *
 * Built via setup_core.py; zsys._core provides Python fallbacks.
 *
 * Functions:
 *   escape_html, strip_html, strip_markdown
 *   truncate_text, split_text, get_args
 *   format_bytes, format_duration
 *   format_bold, format_italic, format_code, format_mono,
 *   format_pre, format_link, format_mention
 *   build_help_text, build_modules_list
 *   ansi_color, format_json_log
 *   parse_meta_comments
 *   match_prefix, nested_get
 *   format_exc_html, router_lookup
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>


/* ═══════════════════════════ internal helpers ══════════════════════════════ */

static const char *
skip_ws(const char *p)
{
    while (*p == ' ' || *p == '\t') p++;
    return p;
}

/*
 * Growing byte buffer — avoids realloc churn when building strings.
 */
typedef struct { char *data; Py_ssize_t len, cap; } Buf;

static int
buf_init(Buf *b, Py_ssize_t initial)
{
    b->data = PyMem_Malloc(initial);
    b->len  = 0;
    b->cap  = initial;
    return b->data != NULL;
}

static int
buf_write(Buf *b, const char *s, Py_ssize_t n)
{
    if (b->len + n + 1 > b->cap) {
        Py_ssize_t new_cap = (b->cap + n + 1) * 2;
        char *p = PyMem_Realloc(b->data, new_cap);
        if (!p) return 0;
        b->data = p;
        b->cap  = new_cap;
    }
    memcpy(b->data + b->len, s, n);
    b->len += n;
    return 1;
}

static int  buf_writec(Buf *b, char c)         { return buf_write(b, &c, 1); }
static int  buf_writes(Buf *b, const char *s)  { return buf_write(b, s, (Py_ssize_t)strlen(s)); }

static PyObject *
buf_finish(Buf *b)
{
    PyObject *r = PyUnicode_FromStringAndSize(b->data, b->len);
    PyMem_Free(b->data);
    b->data = NULL;
    return r;
}

static void __attribute__((unused)) buf_free(Buf *b)    { if (b->data) { PyMem_Free(b->data); b->data = NULL; } }

/* Escape text into buf (used by all format_* wrappers). */
static int
buf_escape_html(Buf *b, const char *text, Py_ssize_t len)
{
    for (Py_ssize_t i = 0; i < len; i++) {
        switch ((unsigned char)text[i]) {
            case '&':  buf_writes(b, "&amp;");  break;
            case '<':  buf_writes(b, "&lt;");   break;
            case '>':  buf_writes(b, "&gt;");   break;
            case '"':  buf_writes(b, "&quot;"); break;
            case '\'': buf_writes(b, "&#x27;"); break;
            default:   buf_writec(b, text[i]);  break;
        }
    }
    return 1;
}

/* Wrap text in <tag>…</tag>, optionally HTML-escaping it first. */
static PyObject *
wrap_tag(const char *tag, PyObject *text_obj, int do_escape)
{
    Py_ssize_t  tlen;
    const char *text = PyUnicode_AsUTF8AndSize(text_obj, &tlen);
    if (!text) return NULL;

    Py_ssize_t tag_len = (Py_ssize_t)strlen(tag);
    Buf b;
    if (!buf_init(&b, tlen * 2 + tag_len * 2 + 8)) return PyErr_NoMemory();

    buf_writec(&b, '<');
    buf_write(&b, tag, tag_len);
    buf_writec(&b, '>');
    if (do_escape)
        buf_escape_html(&b, text, tlen);
    else
        buf_write(&b, text, tlen);
    buf_writes(&b, "</");
    buf_write(&b, tag, tag_len);
    buf_writec(&b, '>');
    return buf_finish(&b);
}


/* ════════════════════════════ escape_html ══════════════════════════════════ */

static PyObject *
zsys_escape_html(PyObject *self, PyObject *args)
{
    const char *text; Py_ssize_t len;
    if (!PyArg_ParseTuple(args, "s#", &text, &len)) return NULL;

    Buf b;
    if (!buf_init(&b, len * 2 + 1)) return PyErr_NoMemory();
    buf_escape_html(&b, text, len);
    return buf_finish(&b);
}


/* ════════════════════════════ strip_html ═══════════════════════════════════ */

static PyObject *
zsys_strip_html(PyObject *self, PyObject *args)
{
    const char *text; Py_ssize_t len;
    if (!PyArg_ParseTuple(args, "s#", &text, &len)) return NULL;

    Buf b;
    if (!buf_init(&b, len + 1)) return PyErr_NoMemory();

    int in_tag = 0;
    for (Py_ssize_t i = 0; i < len; i++) {
        char c = text[i];
        if      (c == '<')  { in_tag = 1; continue; }
        else if (c == '>')  { in_tag = 0; continue; }
        else if (in_tag)    continue;

        /* simple entity unescape */
        if (c == '&') {
            #define TRY(ent, repl, skip) \
                if (strncmp(text + i, ent, skip) == 0) { buf_writes(&b, repl); i += skip - 1; continue; }
            TRY("&amp;",  "&",  5)
            TRY("&lt;",   "<",  4)
            TRY("&gt;",   ">",  4)
            TRY("&quot;", "\"", 6)
            TRY("&#39;",  "'",  5)
            TRY("&#x27;", "'",  6)
            #undef TRY
        }
        buf_writec(&b, c);
    }
    return buf_finish(&b);
}


/* ═══════════════════════════ strip_markdown ════════════════════════════════ */
/*
 * Single-pass state machine. Handles:
 *   **bold**, __bold__, *italic*, _italic_,
 *   `code`, ```block```, [text](url)
 */

static PyObject *
zsys_strip_markdown(PyObject *self, PyObject *args)
{
    const char *text; Py_ssize_t len;
    if (!PyArg_ParseTuple(args, "s#", &text, &len)) return NULL;

    Buf b;
    if (!buf_init(&b, len + 1)) return PyErr_NoMemory();

    Py_ssize_t i = 0;
    while (i < len) {
        char c = text[i];

        /* ``` block → drop content */
        if (c == '`' && i + 2 < len && text[i+1] == '`' && text[i+2] == '`') {
            i += 3;
            while (i < len) {
                if (text[i] == '`' && i + 2 < len && text[i+1] == '`' && text[i+2] == '`')
                    { i += 3; break; }
                i++;
            }
            continue;
        }

        /* `inline code` → keep content */
        if (c == '`') {
            i++;
            while (i < len && text[i] != '`') buf_writec(&b, text[i++]);
            if (i < len) i++;
            continue;
        }

        /* **bold** or __bold__ */
        if ((c == '*' || c == '_') && i + 1 < len && text[i+1] == c) {
            char d = c; i += 2;
            while (i < len) {
                if (text[i] == d && i + 1 < len && text[i+1] == d) { i += 2; break; }
                buf_writec(&b, text[i++]);
            }
            continue;
        }

        /* *italic* or _italic_ */
        if (c == '*' || c == '_') {
            char d = c; i++;
            while (i < len && text[i] != d) buf_writec(&b, text[i++]);
            if (i < len) i++;
            continue;
        }

        /* [text](url) → text */
        if (c == '[') {
            i++;
            while (i < len && text[i] != ']') buf_writec(&b, text[i++]);
            if (i < len) i++; /* ] */
            if (i < len && text[i] == '(') {
                i++;
                while (i < len && text[i] != ')') i++;
                if (i < len) i++;
            }
            continue;
        }

        buf_writec(&b, c);
        i++;
    }
    return buf_finish(&b);
}


/* ════════════════════════════ truncate_text ════════════════════════════════ */

static PyObject *
zsys_truncate_text(PyObject *self, PyObject *args)
{
    PyObject   *text_obj;
    int         max_length = 4096;
    const char *suffix     = "...";
    Py_ssize_t  suffix_len = 3;
    if (!PyArg_ParseTuple(args, "U|iz#", &text_obj, &max_length, &suffix, &suffix_len))
        return NULL;

    if (PyUnicode_GetLength(text_obj) <= max_length) {
        Py_INCREF(text_obj);
        return text_obj;
    }

    PyObject *suffix_obj = PyUnicode_FromStringAndSize(suffix, suffix_len);
    if (!suffix_obj) return NULL;

    Py_ssize_t cut    = max_length - PyUnicode_GetLength(suffix_obj);
    if (cut < 0) cut  = 0;

    PyObject *head   = PyUnicode_Substring(text_obj, 0, cut);
    PyObject *result = head ? PyUnicode_Concat(head, suffix_obj) : NULL;
    Py_XDECREF(head);
    Py_DECREF(suffix_obj);
    return result;
}


/* ════════════════════════════ split_text ═══════════════════════════════════ */

static PyObject *
zsys_split_text(PyObject *self, PyObject *args)
{
    PyObject *text_obj;
    int max_length = 4096;
    if (!PyArg_ParseTuple(args, "U|i", &text_obj, &max_length)) return NULL;

    if (PyUnicode_GetLength(text_obj) <= max_length) {
        PyObject *list = PyList_New(1);
        if (!list) return NULL;
        Py_INCREF(text_obj);
        PyList_SET_ITEM(list, 0, text_obj);
        return list;
    }

    PyObject *result = PyList_New(0);
    if (!result) return NULL;

    PyObject *nl    = PyUnicode_FromString("\n");
    PyObject *lines = PyUnicode_Split(text_obj, nl, -1);
    Py_DECREF(nl);
    if (!lines) { Py_DECREF(result); return NULL; }

    PyObject *current = PyUnicode_FromString("");
    if (!current) { Py_DECREF(lines); Py_DECREF(result); return NULL; }

    Py_ssize_t nlines = PyList_GET_SIZE(lines);
    for (Py_ssize_t i = 0; i < nlines; i++) {
        PyObject  *line = PyList_GET_ITEM(lines, i);
        Py_ssize_t llen = PyUnicode_GetLength(line);
        Py_ssize_t clen = PyUnicode_GetLength(current);

        if (clen + llen + 1 <= max_length) {
            /* current += line + '\n' */
            PyObject *nl_s  = PyUnicode_FromString("\n");
            PyObject *tmp1  = PyUnicode_Concat(current, line);
            Py_DECREF(current);
            PyObject *tmp2  = tmp1 ? PyUnicode_Concat(tmp1, nl_s) : NULL;
            Py_XDECREF(tmp1); Py_DECREF(nl_s);
            if (!tmp2) { Py_DECREF(lines); Py_DECREF(result); return NULL; }
            current = tmp2;
        } else {
            if (PyUnicode_GetLength(current) > 0)
                PyList_Append(result, current);
            Py_DECREF(current);
            current = PyUnicode_FromString("");

            if (llen > max_length) {
                /* hard-split oversized line */
                for (Py_ssize_t pos = 0; pos < llen; pos += max_length) {
                    Py_ssize_t end   = pos + max_length < llen ? pos + max_length : llen;
                    PyObject  *chunk = PyUnicode_Substring(line, pos, end);
                    if (chunk) { PyList_Append(result, chunk); Py_DECREF(chunk); }
                }
            } else {
                PyObject *nl_s = PyUnicode_FromString("\n");
                PyObject *tmp  = PyUnicode_Concat(line, nl_s);
                Py_DECREF(nl_s); Py_DECREF(current);
                current = tmp ? tmp : PyUnicode_FromString("");
            }
        }
    }

    if (PyUnicode_GetLength(current) > 0)
        PyList_Append(result, current);
    Py_DECREF(current);
    Py_DECREF(lines);
    return result;
}


/* ════════════════════════════ get_args ═════════════════════════════════════ */

static PyObject *
zsys_get_args(PyObject *self, PyObject *args)
{
    PyObject *text_obj;
    int max_split = -1;
    if (!PyArg_ParseTuple(args, "U|i", &text_obj, &max_split)) return NULL;

    int actual = (max_split > 0) ? max_split + 1 : -1;
    PyObject *parts = PyUnicode_Split(text_obj, NULL, actual);
    if (!parts) return NULL;

    Py_ssize_t n = PyList_GET_SIZE(parts);
    if (n <= 1) { Py_DECREF(parts); return PyList_New(0); }

    PyObject *result = PyList_GetSlice(parts, 1, n);
    Py_DECREF(parts);
    return result;
}


/* ════════════════════════════ format_bytes ═════════════════════════════════ */

static PyObject *
zsys_format_bytes(PyObject *self, PyObject *args)
{
    long long size;
    if (!PyArg_ParseTuple(args, "L", &size)) return NULL;

    static const char *units[] = {"B", "KB", "MB", "GB", "TB", "PB"};
    double val = (double)size;
    int    idx = 0;
    while (val >= 1024.0 && idx < 5) { val /= 1024.0; idx++; }

    char buf[32];
    snprintf(buf, sizeof(buf), "%.1f %s", val, units[idx]);
    return PyUnicode_FromString(buf);
}


/* ═══════════════════════════ format_duration ═══════════════════════════════ */

static PyObject *
zsys_format_duration(PyObject *self, PyObject *args)
{
    double seconds;
    if (!PyArg_ParseTuple(args, "d", &seconds)) return NULL;

    long long total = (long long)seconds;
    int h = (int)(total / 3600);
    int m = (int)((total % 3600) / 60);
    int s = (int)(total % 60);

    char buf[32];
    if      (h > 0) snprintf(buf, sizeof(buf), "%dh %dm %ds", h, m, s);
    else if (m > 0) snprintf(buf, sizeof(buf), "%dm %ds",      m, s);
    else            snprintf(buf, sizeof(buf), "%ds",             s);
    return PyUnicode_FromString(buf);
}


/* ════════════════════════════ HTML formatters ══════════════════════════════ */

static PyObject *
zsys_format_bold(PyObject *self, PyObject *args)
{
    PyObject *text; int escape = 1;
    if (!PyArg_ParseTuple(args, "U|p", &text, &escape)) return NULL;
    return wrap_tag("b", text, escape);
}

static PyObject *
zsys_format_italic(PyObject *self, PyObject *args)
{
    PyObject *text; int escape = 1;
    if (!PyArg_ParseTuple(args, "U|p", &text, &escape)) return NULL;
    return wrap_tag("i", text, escape);
}

static PyObject *
zsys_format_code(PyObject *self, PyObject *args)
{
    PyObject *text; int escape = 0;
    if (!PyArg_ParseTuple(args, "U|p", &text, &escape)) return NULL;
    return wrap_tag("code", text, escape);
}

static PyObject *
zsys_format_mono(PyObject *self, PyObject *args)
{
    PyObject *text; int escape = 1;
    if (!PyArg_ParseTuple(args, "U|p", &text, &escape)) return NULL;
    return wrap_tag("code", text, escape);
}

static PyObject *
zsys_format_pre(PyObject *self, PyObject *args)
{
    PyObject   *text_obj;
    const char *lang   = NULL;
    int         escape = 0;
    if (!PyArg_ParseTuple(args, "U|zp", &text_obj, &lang, &escape)) return NULL;

    Py_ssize_t  tlen;
    const char *text = PyUnicode_AsUTF8AndSize(text_obj, &tlen);
    if (!text) return NULL;

    Buf b;
    if (!buf_init(&b, tlen + 64)) return PyErr_NoMemory();

    if (lang && *lang) {
        buf_writes(&b, "<pre><code class=\"language-");
        buf_writes(&b, lang);
        buf_writes(&b, "\">");
    } else {
        buf_writes(&b, "<pre>");
    }

    if (escape)
        buf_escape_html(&b, text, tlen);
    else
        buf_write(&b, text, tlen);

    buf_writes(&b, lang && *lang ? "</code></pre>" : "</pre>");
    return buf_finish(&b);
}

static PyObject *
zsys_format_link(PyObject *self, PyObject *args)
{
    PyObject   *text_obj;
    const char *url;
    int         escape = 1;
    if (!PyArg_ParseTuple(args, "Us|p", &text_obj, &url, &escape)) return NULL;

    Py_ssize_t  tlen;
    const char *text = PyUnicode_AsUTF8AndSize(text_obj, &tlen);
    if (!text) return NULL;

    Buf b;
    if (!buf_init(&b, tlen * 2 + strlen(url) + 16)) return PyErr_NoMemory();

    buf_writes(&b, "<a href=\"");
    buf_writes(&b, url);
    buf_writes(&b, "\">");
    if (escape) buf_escape_html(&b, text, tlen); else buf_write(&b, text, tlen);
    buf_writes(&b, "</a>");
    return buf_finish(&b);
}

static PyObject *
zsys_format_mention(PyObject *self, PyObject *args)
{
    PyObject  *text_obj;
    long long  user_id;
    int        escape = 1;
    if (!PyArg_ParseTuple(args, "UL|p", &text_obj, &user_id, &escape)) return NULL;

    Py_ssize_t  tlen;
    const char *text = PyUnicode_AsUTF8AndSize(text_obj, &tlen);
    if (!text) return NULL;

    char url[64];
    snprintf(url, sizeof(url), "tg://user?id=%lld", user_id);

    Buf b;
    if (!buf_init(&b, tlen * 2 + 64)) return PyErr_NoMemory();

    buf_writes(&b, "<a href=\"");
    buf_writes(&b, url);
    buf_writes(&b, "\">");
    if (escape) buf_escape_html(&b, text, tlen); else buf_write(&b, text, tlen);
    buf_writes(&b, "</a>");
    return buf_finish(&b);
}


/* ═══════════════════════════ build_help_text ═══════════════════════════════ */
/*
 * build_help_text(module_name, commands: dict[str,str], prefix) -> str
 *
 *   <b>Help for |name|</b>
 *   <b>Usage:</b>
 *   <code>.cmd</code> <code>args</code> — <i>desc</i>
 */

static PyObject *
zsys_build_help_text(PyObject *self, PyObject *args)
{
    PyObject   *mod_name_obj, *commands_dict;
    const char *prefix;
    if (!PyArg_ParseTuple(args, "UOs", &mod_name_obj, &commands_dict, &prefix))
        return NULL;
    if (!PyDict_Check(commands_dict)) {
        PyErr_SetString(PyExc_TypeError, "commands must be a dict");
        return NULL;
    }

    Py_ssize_t  mlen;
    const char *mname = PyUnicode_AsUTF8AndSize(mod_name_obj, &mlen);
    if (!mname) return NULL;

    Py_ssize_t prefix_len = (Py_ssize_t)strlen(prefix);

    Buf b;
    if (!buf_init(&b, 256)) return PyErr_NoMemory();

    buf_writes(&b, "<b>Help for |");
    buf_write(&b, mname, mlen);
    buf_writes(&b, "|</b>\n<b>Usage:</b>");

    PyObject *key, *val;
    Py_ssize_t pos = 0;
    while (PyDict_Next(commands_dict, &pos, &key, &val)) {
        const char *cmd  = PyUnicode_AsUTF8(key);
        const char *desc = PyUnicode_AsUTF8(val);
        if (!cmd || !desc) continue;

        const char *sp = strchr(cmd, ' ');
        buf_writes(&b, "\n<code>");
        buf_write(&b, prefix, prefix_len);
        if (sp) {
            buf_write(&b, cmd, sp - cmd);
            buf_writes(&b, "</code> <code>");
            buf_writes(&b, sp + 1);
        } else {
            buf_writes(&b, cmd);
        }
        buf_writes(&b, "</code> — <i>");
        buf_writes(&b, desc);
        buf_writes(&b, "</i>");
    }

    return buf_finish(&b);
}


/* ══════════════════════════ build_modules_list ═════════════════════════════ */
/*
 * build_modules_list(modules: dict[str, dict]) -> str
 *
 *   <b>Загруженные модули:</b>
 *   • <code>name</code> (N команд)
 */

static PyObject *
zsys_build_modules_list(PyObject *self, PyObject *args)
{
    PyObject *modules_dict;
    if (!PyArg_ParseTuple(args, "O", &modules_dict)) return NULL;
    if (!PyDict_Check(modules_dict)) {
        PyErr_SetString(PyExc_TypeError, "modules must be a dict");
        return NULL;
    }

    if (PyDict_Size(modules_dict) == 0)
        return PyUnicode_FromString("<b>Нет загруженных модулей</b>");

    PyObject *keys = PyDict_Keys(modules_dict);
    if (!keys) return NULL;
    if (PyList_Sort(keys) < 0) { Py_DECREF(keys); return NULL; }

    Buf b;
    if (!buf_init(&b, 256)) { Py_DECREF(keys); return PyErr_NoMemory(); }
    buf_writes(&b, "<b>Загруженные модули:</b>");

    Py_ssize_t n = PyList_GET_SIZE(keys);
    for (Py_ssize_t i = 0; i < n; i++) {
        PyObject   *name_obj  = PyList_GET_ITEM(keys, i);
        const char *name      = PyUnicode_AsUTF8(name_obj);
        PyObject   *cmds      = PyDict_GetItem(modules_dict, name_obj);
        Py_ssize_t  cnt       = cmds && PyDict_Check(cmds) ? PyDict_Size(cmds) : 0;
        if (!name) continue;

        char count_str[32];
        snprintf(count_str, sizeof(count_str), " (%zd команд)", cnt);

        buf_writes(&b, "\n• <code>");
        buf_writes(&b, name);
        buf_writes(&b, "</code>");
        buf_writes(&b, count_str);
    }

    Py_DECREF(keys);
    return buf_finish(&b);
}


/* ════════════════════════════ ansi_color ═══════════════════════════════════ */
/* ansi_color(text, code) → "\033[{code}m{text}\033[0m" */

static PyObject *
zsys_ansi_color(PyObject *self, PyObject *args)
{
    const char *text, *code; Py_ssize_t tlen;
    if (!PyArg_ParseTuple(args, "s#s", &text, &tlen, &code)) return NULL;

    Buf b;
    if (!buf_init(&b, tlen + strlen(code) + 12)) return PyErr_NoMemory();

    buf_writes(&b, "\033[");
    buf_writes(&b, code);
    buf_writec(&b, 'm');
    buf_write(&b, text, tlen);
    buf_writes(&b, "\033[0m");
    return buf_finish(&b);
}


/* ═══════════════════════════ format_json_log ═══════════════════════════════ */
/* format_json_log(level, message, ts) → {"level":…,"message":…,"ts":…} */

static PyObject *
zsys_format_json_log(PyObject *self, PyObject *args)
{
    const char *level, *message, *ts;
    if (!PyArg_ParseTuple(args, "sss", &level, &message, &ts)) return NULL;

    Py_ssize_t msg_len = (Py_ssize_t)strlen(message);
    Buf b;
    if (!buf_init(&b, msg_len + 128)) return PyErr_NoMemory();

    buf_writes(&b, "{\"level\": \"");
    buf_writes(&b, level);
    buf_writes(&b, "\", \"message\": \"");

    for (Py_ssize_t i = 0; i < msg_len; i++) {
        unsigned char c = (unsigned char)message[i];
        if      (c == '\\') buf_writes(&b, "\\\\");
        else if (c == '"')  buf_writes(&b, "\\\"");
        else if (c == '\n') buf_writes(&b, "\\n");
        else if (c == '\r') buf_writes(&b, "\\r");
        else if (c == '\t') buf_writes(&b, "\\t");
        else if (c < 0x20) {
            char esc[8];
            snprintf(esc, sizeof(esc), "\\u%04x", c);
            buf_writes(&b, esc);
        } else {
            buf_writec(&b, (char)c);
        }
    }

    buf_writes(&b, "\", \"ts\": \"");
    buf_writes(&b, ts);
    buf_writes(&b, "\"}");
    return buf_finish(&b);
}


/* ═══════════════════════════ parse_meta_comments ═══════════════════════════ */
/*
 * Three formats, single pass:
 *   # meta: key=value
 *   # meta key: value   (legacy)
 *   # @key value        (loader)
 */

static int
add_meta(PyObject *dict, const char *key, Py_ssize_t klen,
         const char *val, Py_ssize_t vlen, int overwrite)
{
    if (klen <= 0) return 1;

    char kbuf[128];
    if (klen >= (Py_ssize_t)sizeof(kbuf)) klen = (Py_ssize_t)sizeof(kbuf) - 1;
    for (Py_ssize_t i = 0; i < klen; i++)
        kbuf[i] = (char)tolower((unsigned char)key[i]);
    kbuf[klen] = '\0';

    /* trim trailing spaces from value */
    while (vlen > 0 && (val[vlen-1] == ' ' || val[vlen-1] == '\t')) vlen--;

    PyObject *k = PyUnicode_FromStringAndSize(kbuf, klen);
    if (!k) return 0;

    if (!overwrite && PyDict_GetItem(dict, k) != NULL) { Py_DECREF(k); return 1; }

    PyObject *v  = PyUnicode_FromStringAndSize(val, vlen);
    int       ok = (v != NULL) ? (PyDict_SetItem(dict, k, v) == 0) : 0;
    Py_XDECREF(v);
    Py_DECREF(k);
    return ok;
}

static PyObject *
zsys_parse_meta_comments(PyObject *self, PyObject *args)
{
    const char *code; Py_ssize_t code_len;
    if (!PyArg_ParseTuple(args, "s#", &code, &code_len)) return NULL;

    PyObject   *result = PyDict_New();
    if (!result) return NULL;

    const char *p   = code;
    const char *end = code + code_len;

    while (p < end) {
        p = skip_ws(p);
        if (p >= end || *p != '#') goto next_line;
        p++; p = skip_ws(p);

        /* # meta: key=value */
        if (strncasecmp(p, "meta:", 5) == 0) {
            p += 5; p = skip_ws(p);
            const char *key = p;
            Py_ssize_t  klen = 0;
            while (p < end && *p != '=' && *p != '\n') { p++; klen++; }
            while (klen > 0 && (key[klen-1] == ' ' || key[klen-1] == '\t')) klen--;
            if (*p != '=') goto next_line;
            p++; p = skip_ws(p);
            const char *val = p;
            while (p < end && *p != '\n' && *p != '\r') p++;
            add_meta(result, key, klen, val, p - val, 1);
            goto next_line;
        }

        /* # meta key: value  (legacy) */
        if (strncasecmp(p, "meta", 4) == 0 && (p[4] == ' ' || p[4] == '\t')) {
            p += 4; p = skip_ws(p);
            const char *key = p;
            Py_ssize_t  klen = 0;
            while (p < end && *p != ':' && *p != '\n' && *p != ' ' && *p != '\t')
                { p++; klen++; }
            p = skip_ws(p);
            if (*p != ':') goto next_line;
            p++; p = skip_ws(p);
            const char *val = p;
            while (p < end && *p != '\n' && *p != '\r') p++;
            add_meta(result, key, klen, val, p - val, 0);
            goto next_line;
        }

        /* # @key value  (loader) */
        if (*p == '@') {
            p++;
            const char *key = p;
            Py_ssize_t  klen = 0;
            while (p < end && *p != ' ' && *p != '\t' && *p != '\n') { p++; klen++; }
            p = skip_ws(p);
            const char *val = p;
            while (p < end && *p != '\n' && *p != '\r') p++;
            add_meta(result, key, klen, val, p - val, 0);
            goto next_line;
        }

    next_line:
        while (p < end && *p != '\n') p++;
        if (p < end) p++;
    }

    return result;
}


/* ════════════════════════════ match_prefix ═════════════════════════════════ */

static PyObject *
zsys_match_prefix(PyObject *self, PyObject *args)
{
    PyObject *text_obj, *prefixes_obj, *trigger_set_obj;
    if (!PyArg_ParseTuple(args, "UOO", &text_obj, &prefixes_obj, &trigger_set_obj))
        return NULL;

    Py_ssize_t  text_len;
    const char *text = PyUnicode_AsUTF8AndSize(text_obj, &text_len);
    if (!text) return NULL;
    if (text_len == 0) Py_RETURN_FALSE;

    PyObject  *fast = PySequence_Fast(prefixes_obj, "prefixes must be a list");
    if (!fast) return NULL;
    Py_ssize_t n    = PySequence_Fast_GET_SIZE(fast);

    for (Py_ssize_t i = 0; i < n; i++) {
        PyObject   *pobj   = PySequence_Fast_GET_ITEM(fast, i);
        Py_ssize_t  plen;
        const char *prefix = PyUnicode_AsUTF8AndSize(pobj, &plen);
        if (!prefix) { Py_DECREF(fast); return NULL; }
        if (plen > text_len || strncmp(text, prefix, (size_t)plen) != 0) continue;

        const char *rest     = text + plen;
        Py_ssize_t  rest_len = text_len - plen;
        if (rest_len == 0) continue;

        Py_ssize_t wlen = 0;
        while (wlen < rest_len && rest[wlen] != ' ' && rest[wlen] != '\t') wlen++;

        char *lower = PyMem_Malloc(wlen + 1);
        if (!lower) { Py_DECREF(fast); return PyErr_NoMemory(); }
        for (Py_ssize_t j = 0; j < wlen; j++)
            lower[j] = (char)tolower((unsigned char)rest[j]);
        lower[wlen] = '\0';

        PyObject *word  = PyUnicode_FromStringAndSize(lower, wlen);
        PyMem_Free(lower);
        if (!word) { Py_DECREF(fast); return NULL; }

        int found = PySet_Contains(trigger_set_obj, word);
        Py_DECREF(word);
        Py_DECREF(fast);

        if (found == 1) Py_RETURN_TRUE;
        if (found < 0)  return NULL;
        break;
    }

    Py_DECREF(fast);
    Py_RETURN_FALSE;
}


/* ════════════════════════════ nested_get ═══════════════════════════════════ */

static PyObject *
zsys_nested_get(PyObject *self, PyObject *args)
{
    PyObject   *d;
    const char *key;
    if (!PyArg_ParseTuple(args, "Os", &d, &key)) return NULL;
    if (!PyDict_Check(d)) Py_RETURN_NONE;

    PyObject   *current = d;
    Py_INCREF(current);

    const char *p = key;
    while (*p) {
        const char *dot     = strchr(p, '.');
        Py_ssize_t  seg_len = dot ? (dot - p) : (Py_ssize_t)strlen(p);

        PyObject *seg = PyUnicode_FromStringAndSize(p, seg_len);
        if (!seg) { Py_DECREF(current); return NULL; }

        if (!PyDict_Check(current)) {
            Py_DECREF(seg); Py_DECREF(current); Py_RETURN_NONE;
        }

        PyObject *next = PyDict_GetItemWithError(current, seg);
        Py_DECREF(seg); Py_DECREF(current);

        if (!next) {
            if (PyErr_Occurred()) return NULL;
            Py_RETURN_NONE;
        }

        current = next;
        Py_INCREF(current);
        p = dot ? dot + 1 : p + seg_len;
    }

    if (!PyUnicode_Check(current)) { Py_DECREF(current); Py_RETURN_NONE; }
    return current;
}


/* ═══════════════════════════ format_underline ══════════════════════════════ */

static PyObject *
zsys_format_underline(PyObject *self, PyObject *args)
{
    PyObject *text;
    if (!PyArg_ParseTuple(args, "U", &text)) return NULL;
    return wrap_tag("u", text, 0);
}

/* ═════════════════════════ format_strikethrough ════════════════════════════ */

static PyObject *
zsys_format_strikethrough(PyObject *self, PyObject *args)
{
    PyObject *text;
    if (!PyArg_ParseTuple(args, "U", &text)) return NULL;
    return wrap_tag("s", text, 0);
}

/* ════════════════════════════ format_spoiler ═══════════════════════════════ */

static PyObject *
zsys_format_spoiler(PyObject *self, PyObject *args)
{
    PyObject *text;
    if (!PyArg_ParseTuple(args, "U", &text)) return NULL;
    return wrap_tag("tg-spoiler", text, 0);
}

/* ════════════════════════════ format_quote ═════════════════════════════════ */

static PyObject *
zsys_format_quote(PyObject *self, PyObject *args)
{
    PyObject *text;
    if (!PyArg_ParseTuple(args, "U", &text)) return NULL;
    return wrap_tag("blockquote", text, 0);
}

/* ══════════════════════════ format_preformatted ════════════════════════════ */

static PyObject *
zsys_format_preformatted(PyObject *self, PyObject *args)
{
    PyObject *text;
    if (!PyArg_ParseTuple(args, "U", &text)) return NULL;
    return wrap_tag("pre", text, 0);
}

/* ════════════════════════════ human_time ═══════════════════════════════════ */

/* Russian plural form: 0=singular(1), 1=few(2-4), 2=many(5+) */
static int
ru_plural(int n)
{
    int n10 = n % 10, n100 = n % 100;
    if (n10 == 1 && n100 != 11) return 0;
    if (n10 >= 2 && n10 <= 4 && (n100 < 10 || n100 >= 20)) return 1;
    return 2;
}

static PyObject *
zsys_human_time(PyObject *self, PyObject *args)
{
    int seconds, short_fmt = 1;
    if (!PyArg_ParseTuple(args, "i|p", &seconds, &short_fmt)) return NULL;
    if (seconds < 0) seconds = 0;

    int days    = seconds / 86400;
    int hours   = (seconds % 86400) / 3600;
    int minutes = (seconds % 3600) / 60;
    int secs    = seconds % 60;

    Buf b;
    if (!buf_init(&b, 128)) return PyErr_NoMemory();

    int has_any = 0;
    char tmp[32];

    if (short_fmt) {
        if (days) {
            snprintf(tmp, sizeof(tmp), "%d ", days);
            buf_writes(&b, tmp);
            buf_writes(&b, "дн. ");
            has_any = 1;
        }
        if (hours) {
            snprintf(tmp, sizeof(tmp), "%d ", hours);
            buf_writes(&b, tmp);
            buf_writes(&b, "ч. ");
            has_any = 1;
        }
        if (minutes) {
            snprintf(tmp, sizeof(tmp), "%d ", minutes);
            buf_writes(&b, tmp);
            buf_writes(&b, "мин. ");
            has_any = 1;
        }
        if (secs || !has_any) {
            snprintf(tmp, sizeof(tmp), "%d ", secs);
            buf_writes(&b, tmp);
            buf_writes(&b, "сек.");
            has_any = 1;
        }
        /* trim trailing space */
        while (b.len > 0 && b.data[b.len - 1] == ' ') b.len--;
    } else {
        static const char *day_forms[3]  = { "день",    "дня",     "дней"    };
        static const char *hr_forms[3]   = { "час",     "часа",    "часов"   };
        static const char *min_forms[3]  = { "минута",  "минуты",  "минут"   };
        static const char *sec_forms[3]  = { "секунда", "секунды", "секунд"  };

        if (days) {
            snprintf(tmp, sizeof(tmp), "%d ", days);
            buf_writes(&b, tmp);
            buf_writes(&b, day_forms[ru_plural(days)]);
            has_any = 1;
        }
        if (hours) {
            if (has_any) buf_writec(&b, ' ');
            snprintf(tmp, sizeof(tmp), "%d ", hours);
            buf_writes(&b, tmp);
            buf_writes(&b, hr_forms[ru_plural(hours)]);
            has_any = 1;
        }
        if (minutes) {
            if (has_any) buf_writec(&b, ' ');
            snprintf(tmp, sizeof(tmp), "%d ", minutes);
            buf_writes(&b, tmp);
            buf_writes(&b, min_forms[ru_plural(minutes)]);
            has_any = 1;
        }
        if (secs || !has_any) {
            if (has_any) buf_writec(&b, ' ');
            snprintf(tmp, sizeof(tmp), "%d ", secs);
            buf_writes(&b, tmp);
            buf_writes(&b, sec_forms[ru_plural(secs)]);
        }
    }

    return buf_finish(&b);
}

/* ════════════════════════════ parse_duration ═══════════════════════════════ */

static PyObject *
zsys_parse_duration(PyObject *self, PyObject *args)
{
    const char *text;
    if (!PyArg_ParseTuple(args, "s", &text)) return NULL;

    long total = 0;
    int found = 0;
    const char *p = text;

    while (*p) {
        if (!isdigit((unsigned char)*p)) { p++; continue; }
        long val = 0;
        while (isdigit((unsigned char)*p)) { val = val * 10 + (*p - '0'); p++; }
        if (!*p) Py_RETURN_NONE;  /* trailing number with no unit */
        char unit = (char)tolower((unsigned char)*p++);
        long mult;
        switch (unit) {
            case 's': mult = 1;       break;
            case 'm': mult = 60;      break;
            case 'h': mult = 3600;    break;
            case 'd': mult = 86400;   break;
            case 'w': mult = 604800;  break;
            default:  Py_RETURN_NONE;
        }
        total += val * mult;
        found = 1;
    }
    if (!found) Py_RETURN_NONE;
    return PyLong_FromLong(total);
}

/* ════════════════════════════ print_box_str ════════════════════════════════ */

static PyObject *
zsys_print_box_str(PyObject *self, PyObject *args)
{
    PyObject *text_obj;
    int padding = 2;
    if (!PyArg_ParseTuple(args, "U|i", &text_obj, &padding)) return NULL;

    PyObject *nl = PyUnicode_FromString("\n");
    if (!nl) return NULL;
    PyObject *lines = PyUnicode_Split(text_obj, nl, -1);
    Py_DECREF(nl);
    if (!lines) return NULL;

    Py_ssize_t n_lines = PyList_GET_SIZE(lines);

    /* Find max line length in code points */
    Py_ssize_t max_len = 0;
    for (Py_ssize_t i = 0; i < n_lines; i++) {
        Py_ssize_t l = PyUnicode_GetLength(PyList_GET_ITEM(lines, i));
        if (l > max_len) max_len = l;
    }

    Py_ssize_t inner_width = max_len + 2 * padding;

    Buf b;
    if (!buf_init(&b, 256 + n_lines * (inner_width * 4 + 32))) {
        Py_DECREF(lines);
        return PyErr_NoMemory();
    }

    /* Top border: ╔═══╗ */
    buf_writes(&b, "╔");
    for (Py_ssize_t i = 0; i < inner_width; i++) buf_writes(&b, "═");
    buf_writes(&b, "╗\n");

    /* Content rows */
    for (Py_ssize_t i = 0; i < n_lines; i++) {
        PyObject *line = PyList_GET_ITEM(lines, i);
        Py_ssize_t line_len = PyUnicode_GetLength(line);
        Py_ssize_t utf8_len;
        const char *utf8 = PyUnicode_AsUTF8AndSize(line, &utf8_len);
        if (!utf8) { Py_DECREF(lines); buf_free(&b); return NULL; }

        buf_writes(&b, "║");
        for (int p = 0; p < padding; p++) buf_writec(&b, ' ');
        buf_write(&b, utf8, utf8_len);
        for (Py_ssize_t p = 0; p < inner_width - padding - line_len; p++) buf_writec(&b, ' ');
        buf_writes(&b, "║\n");
    }

    /* Bottom border: ╚═══╝ */
    buf_writes(&b, "╚");
    for (Py_ssize_t i = 0; i < inner_width; i++) buf_writes(&b, "═");
    buf_writes(&b, "╝");

    Py_DECREF(lines);
    return buf_finish(&b);
}

/* ═══════════════════════════ print_separator_str ═══════════════════════════ */

static PyObject *
zsys_print_separator_str(PyObject *self, PyObject *args)
{
    PyObject *char_obj = NULL;
    int length = 60;
    if (!PyArg_ParseTuple(args, "|Oi", &char_obj, &length)) return NULL;

    const char *ch = "═";
    if (char_obj && char_obj != Py_None) {
        ch = PyUnicode_AsUTF8(char_obj);
        if (!ch) return NULL;
    }

    Py_ssize_t ch_len = (Py_ssize_t)strlen(ch);
    Buf b;
    if (!buf_init(&b, ch_len * length + 1)) return PyErr_NoMemory();
    for (int i = 0; i < length; i++) buf_write(&b, ch, ch_len);
    return buf_finish(&b);
}

/* ════════════════════════════ print_table_str ══════════════════════════════ */

static PyObject *
zsys_print_table_str(PyObject *self, PyObject *args)
{
    PyObject *headers_obj, *rows_obj;
    if (!PyArg_ParseTuple(args, "OO", &headers_obj, &rows_obj)) return NULL;

    if (!PyList_Check(headers_obj) || !PyList_Check(rows_obj)) {
        PyErr_SetString(PyExc_TypeError, "headers and rows must be lists");
        return NULL;
    }

    Py_ssize_t n_cols = PyList_GET_SIZE(headers_obj);
    Py_ssize_t n_rows = PyList_GET_SIZE(rows_obj);

    Py_ssize_t *col_widths = (Py_ssize_t *)PyMem_Malloc(n_cols * sizeof(Py_ssize_t));
    if (!col_widths) return PyErr_NoMemory();

    /* Init from header widths */
    for (Py_ssize_t c = 0; c < n_cols; c++) {
        PyObject *h = PyList_GET_ITEM(headers_obj, c);
        col_widths[c] = PyUnicode_Check(h) ? PyUnicode_GetLength(h) : 0;
    }

    /* Expand from cell widths */
    for (Py_ssize_t r = 0; r < n_rows; r++) {
        PyObject *row = PyList_GET_ITEM(rows_obj, r);
        if (!PyList_Check(row)) continue;
        Py_ssize_t row_len = PyList_GET_SIZE(row);
        for (Py_ssize_t c = 0; c < n_cols && c < row_len; c++) {
            PyObject *cell_str = PyObject_Str(PyList_GET_ITEM(row, c));
            if (!cell_str) { PyMem_Free(col_widths); return NULL; }
            Py_ssize_t clen = PyUnicode_GetLength(cell_str);
            if (clen > col_widths[c]) col_widths[c] = clen;
            Py_DECREF(cell_str);
        }
    }

    /* Estimate buffer: each box char is 3 bytes in UTF-8 */
    Py_ssize_t row_width = 1;
    for (Py_ssize_t c = 0; c < n_cols; c++) row_width += col_widths[c] * 4 + 12;
    Buf b;
    if (!buf_init(&b, (n_rows + 4) * (row_width + 4))) {
        PyMem_Free(col_widths);
        return PyErr_NoMemory();
    }

    /* Top: ┌───┬───┐ */
    buf_writes(&b, "┌");
    for (Py_ssize_t c = 0; c < n_cols; c++) {
        for (Py_ssize_t i = 0; i < col_widths[c] + 2; i++) buf_writes(&b, "─");
        buf_writes(&b, c < n_cols - 1 ? "┬" : "┐");
    }
    buf_writec(&b, '\n');

    /* Header: │ h1 │ h2 │ */
    buf_writes(&b, "│");
    for (Py_ssize_t c = 0; c < n_cols; c++) {
        PyObject *h = PyList_GET_ITEM(headers_obj, c);
        Py_ssize_t utf8_len = 0;
        const char *utf8 = PyUnicode_Check(h) ? PyUnicode_AsUTF8AndSize(h, &utf8_len) : NULL;
        Py_ssize_t hlen = utf8 ? PyUnicode_GetLength(h) : 0;
        buf_writec(&b, ' ');
        if (utf8) buf_write(&b, utf8, utf8_len);
        for (Py_ssize_t i = hlen; i < col_widths[c]; i++) buf_writec(&b, ' ');
        buf_writes(&b, " │");
    }
    buf_writec(&b, '\n');

    /* Separator: ├───┼───┤ */
    buf_writes(&b, "├");
    for (Py_ssize_t c = 0; c < n_cols; c++) {
        for (Py_ssize_t i = 0; i < col_widths[c] + 2; i++) buf_writes(&b, "─");
        buf_writes(&b, c < n_cols - 1 ? "┼" : "┤");
    }
    buf_writec(&b, '\n');

    /* Data rows */
    for (Py_ssize_t r = 0; r < n_rows; r++) {
        PyObject *row = PyList_GET_ITEM(rows_obj, r);
        buf_writes(&b, "│");
        for (Py_ssize_t c = 0; c < n_cols; c++) {
            PyObject *cell_str = NULL;
            if (PyList_Check(row) && c < PyList_GET_SIZE(row))
                cell_str = PyObject_Str(PyList_GET_ITEM(row, c));
            Py_ssize_t clen = cell_str ? PyUnicode_GetLength(cell_str) : 0;
            Py_ssize_t utf8_len = 0;
            const char *utf8 = cell_str ? PyUnicode_AsUTF8AndSize(cell_str, &utf8_len) : NULL;
            buf_writec(&b, ' ');
            if (utf8) buf_write(&b, utf8, utf8_len);
            for (Py_ssize_t i = clen; i < col_widths[c]; i++) buf_writec(&b, ' ');
            buf_writes(&b, " │");
            Py_XDECREF(cell_str);
        }
        buf_writec(&b, '\n');
    }

    /* Bottom: └───┴───┘ */
    buf_writes(&b, "└");
    for (Py_ssize_t c = 0; c < n_cols; c++) {
        for (Py_ssize_t i = 0; i < col_widths[c] + 2; i++) buf_writes(&b, "─");
        buf_writes(&b, c < n_cols - 1 ? "┴" : "┘");
    }

    PyMem_Free(col_widths);
    return buf_finish(&b);
}

/* ═══════════════════════════ print_progress_str ════════════════════════════ */

static PyObject *
zsys_print_progress_str(PyObject *self, PyObject *args)
{
    int current, total, length = 40;
    const char *prefix = "Progress";
    if (!PyArg_ParseTuple(args, "ii|si", &current, &total, &prefix, &length)) return NULL;
    if (total <= 0) total = 1;
    if (length <= 0) length = 1;

    double percent = 100.0 * current / total;
    int filled = (int)((double)length * current / total);
    if (filled > length) filled = length;
    if (filled < 0) filled = 0;

    Buf b;
    if (!buf_init(&b, (Py_ssize_t)(strlen(prefix) + length * 4 + 64))) return PyErr_NoMemory();

    buf_writes(&b, prefix);
    buf_writes(&b, ": |");
    for (int i = 0; i < filled; i++) buf_writes(&b, "█");
    for (int i = filled; i < length; i++) buf_writes(&b, "░");

    char tmp[64];
    snprintf(tmp, sizeof(tmp), "| %.1f%% (%d/%d)", percent, current, total);
    buf_writes(&b, tmp);

    return buf_finish(&b);
}


/* ════════════════ format_exc_html ══════════════════════════════════════════
 *
 * format_exc_html(error_type, error_text,
 *                 cause_type="", cause_text="",
 *                 suffix="", max_length=4000) -> str
 *
 * Builds HTML error message from already-extracted exception fields.
 * HTML escaping is done internally — caller passes raw strings.
 * ════════════════════════════════════════════════════════════════════════════ */

static PyObject *
zsys_format_exc_html(PyObject *self, PyObject *args)
{
    const char *error_type = NULL;   Py_ssize_t et_len  = 0;
    const char *error_text = NULL;   Py_ssize_t etx_len = 0;
    const char *cause_type = "";     Py_ssize_t ct_len  = 0;
    const char *cause_text = "";     Py_ssize_t ctx_len = 0;
    const char *suffix     = "";     Py_ssize_t sf_len  = 0;
    Py_ssize_t max_length  = 4000;

    if (!PyArg_ParseTuple(args, "s#s#|s#s#s#n",
            &error_type, &et_len,
            &error_text, &etx_len,
            &cause_type, &ct_len,
            &cause_text, &ctx_len,
            &suffix,     &sf_len,
            &max_length))
        return NULL;

    Buf b;
    buf_init(&b, 256);

    buf_writes(&b, "<b>Error!</b>\n<code>");
    buf_escape_html(&b, error_type, et_len);
    buf_writes(&b, ": ");
    buf_escape_html(&b, error_text, etx_len);
    buf_writes(&b, "</code>");

    if (ct_len > 0) {
        buf_writes(&b, "\n<b>Caused by:</b> <code>");
        buf_escape_html(&b, cause_type, ct_len);
        buf_writes(&b, ": ");
        buf_escape_html(&b, cause_text, ctx_len);
        buf_writes(&b, "</code>");
    }

    if (sf_len > 0) {
        buf_writes(&b, "\n\n<b>");
        buf_escape_html(&b, suffix, sf_len);
        buf_writes(&b, "</b>");
    }

    /* truncate if needed */
    if (max_length > 0 && b.len > max_length) {
        b.data[max_length - 3] = '.';
        b.data[max_length - 2] = '.';
        b.data[max_length - 1] = '.';
        b.len = max_length;
    }

    return buf_finish(&b);
}


/* ════════════════ router_lookup ═════════════════════════════════════════════
 *
 * router_lookup(trigger_map: dict, trigger: str) -> Any | None
 *
 * Lowercases trigger in C (tolower, ASCII), then does PyDict_GetItem.
 * Equivalent to: trigger_map.get(trigger.lower())
 * ════════════════════════════════════════════════════════════════════════════ */

static PyObject *
zsys_router_lookup(PyObject *self, PyObject *args)
{
    PyObject *trigger_map = NULL;
    const char *trigger_utf8 = NULL;
    Py_ssize_t trigger_len   = 0;

    if (!PyArg_ParseTuple(args, "O!s#",
            &PyDict_Type, &trigger_map,
            &trigger_utf8, &trigger_len))
        return NULL;

    /* lowercase into stack buffer (most triggers < 64 chars) */
    char stack_buf[64];
    char *lower = stack_buf;
    char *heap  = NULL;

    if (trigger_len + 1 > (Py_ssize_t)sizeof(stack_buf)) {
        heap  = (char *)PyMem_Malloc(trigger_len + 1);
        if (!heap) return PyErr_NoMemory();
        lower = heap;
    }

    for (Py_ssize_t i = 0; i < trigger_len; i++)
        lower[i] = (char)tolower((unsigned char)trigger_utf8[i]);
    lower[trigger_len] = '\0';

    PyObject *key = PyUnicode_FromStringAndSize(lower, trigger_len);
    if (heap) PyMem_Free(heap);
    if (!key) return NULL;

    PyObject *result = PyDict_GetItemWithError(trigger_map, key);
    Py_DECREF(key);

    if (result) {
        Py_INCREF(result);
        return result;
    }
    if (PyErr_Occurred()) return NULL;

    Py_RETURN_NONE;
}


/* ════════════════════════════ method table ═════════════════════════════════ */

static PyMethodDef ZsysMethods[] = {
    { "escape_html",       zsys_escape_html,        METH_VARARGS, "escape_html(text) -> str" },
    { "strip_html",        zsys_strip_html,         METH_VARARGS, "strip_html(text) -> str" },
    { "strip_markdown",    zsys_strip_markdown,     METH_VARARGS, "strip_markdown(text) -> str" },
    { "truncate_text",     zsys_truncate_text,      METH_VARARGS, "truncate_text(text, max_length=4096, suffix='...') -> str" },
    { "split_text",        zsys_split_text,         METH_VARARGS, "split_text(text, max_length=4096) -> list[str]" },
    { "get_args",          zsys_get_args,           METH_VARARGS, "get_args(text, max_split=-1) -> list[str]" },
    { "format_bytes",      zsys_format_bytes,       METH_VARARGS, "format_bytes(size: int) -> str" },
    { "format_duration",   zsys_format_duration,    METH_VARARGS, "format_duration(seconds: float) -> str" },
    { "format_bold",       zsys_format_bold,        METH_VARARGS, "format_bold(text, escape=True) -> str" },
    { "format_italic",     zsys_format_italic,      METH_VARARGS, "format_italic(text, escape=True) -> str" },
    { "format_code",       zsys_format_code,        METH_VARARGS, "format_code(text, escape=False) -> str" },
    { "format_mono",       zsys_format_mono,        METH_VARARGS, "format_mono(text, escape=True) -> str" },
    { "format_pre",        zsys_format_pre,         METH_VARARGS, "format_pre(text, language=None, escape=False) -> str" },
    { "format_link",       zsys_format_link,        METH_VARARGS, "format_link(text, url, escape=True) -> str" },
    { "format_mention",    zsys_format_mention,     METH_VARARGS, "format_mention(text, user_id, escape=True) -> str" },
    { "build_help_text",   zsys_build_help_text,    METH_VARARGS, "build_help_text(module_name, commands, prefix) -> str" },
    { "build_modules_list",zsys_build_modules_list, METH_VARARGS, "build_modules_list(modules) -> str" },
    { "ansi_color",        zsys_ansi_color,         METH_VARARGS, "ansi_color(text, code) -> str" },
    { "format_json_log",   zsys_format_json_log,    METH_VARARGS, "format_json_log(level, message, ts) -> str" },
    { "parse_meta_comments", zsys_parse_meta_comments, METH_VARARGS, "parse_meta_comments(code) -> dict" },
    { "match_prefix",      zsys_match_prefix,       METH_VARARGS, "match_prefix(text, prefixes, trigger_set) -> bool" },
    { "nested_get",        zsys_nested_get,         METH_VARARGS, "nested_get(d, key) -> str | None" },
    { "format_underline",     zsys_format_underline,     METH_VARARGS, "format_underline(text) -> str" },
    { "format_strikethrough", zsys_format_strikethrough, METH_VARARGS, "format_strikethrough(text) -> str" },
    { "format_spoiler",       zsys_format_spoiler,       METH_VARARGS, "format_spoiler(text) -> str" },
    { "format_quote",         zsys_format_quote,         METH_VARARGS, "format_quote(text) -> str" },
    { "format_preformatted",  zsys_format_preformatted,  METH_VARARGS, "format_preformatted(text) -> str" },
    { "human_time",           zsys_human_time,           METH_VARARGS, "human_time(seconds, short=True) -> str" },
    { "parse_duration",       zsys_parse_duration,       METH_VARARGS, "parse_duration(text) -> int | None" },
    { "print_box_str",        zsys_print_box_str,        METH_VARARGS, "print_box_str(text, padding=2) -> str" },
    { "print_separator_str",  zsys_print_separator_str,  METH_VARARGS, "print_separator_str(char='═', length=60) -> str" },
    { "print_table_str",      zsys_print_table_str,      METH_VARARGS, "print_table_str(headers, rows) -> str" },
    { "print_progress_str",   zsys_print_progress_str,   METH_VARARGS, "print_progress_str(current, total, prefix='Progress', length=40) -> str" },
    { "format_exc_html",      zsys_format_exc_html,      METH_VARARGS, "format_exc_html(error_type, error_text, cause_type='', cause_text='', suffix='', max_length=4000) -> str" },
    { "router_lookup",        zsys_router_lookup,        METH_VARARGS, "router_lookup(trigger_map, trigger) -> Any | None" },
    { NULL, NULL, 0, NULL }
};

static struct PyModuleDef zsys_core_module = {
    PyModuleDef_HEAD_INIT,
    "_zsys_core",
    "zsys C core — hot paths: text, HTML, i18n, router",
    -1,
    ZsysMethods
};

PyMODINIT_FUNC
PyInit__zsys_core(void)
{
    return PyModule_Create(&zsys_core_module);
}
