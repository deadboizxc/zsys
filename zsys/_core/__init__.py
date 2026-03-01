# -*- coding: utf-8 -*-
"""
zsys._core — C-биндинги горячих путей.

При наличии собранного `_zsys_core.so` используем его.
Если нет — прозрачный Python-fallback с идентичным API.
"""

__all__ = [
    "C_AVAILABLE",
    "escape_html", "strip_html", "strip_markdown",
    "truncate_text", "split_text", "get_args",
    "format_bytes", "format_duration",
    "format_bold", "format_italic", "format_code", "format_mono",
    "format_pre", "format_link", "format_mention",
    "format_underline", "format_strikethrough", "format_spoiler",
    "format_quote", "format_preformatted",
    "build_help_text", "build_modules_list",
    "ansi_color", "format_json_log",
    "parse_meta_comments",
    "match_prefix", "nested_get",
    "human_time", "parse_duration",
    "print_box_str", "print_separator_str", "print_table_str", "print_progress_str",
    "format_exc_html", "router_lookup",
    "get_proc_mem_mb", "get_proc_cpu_pct", "find_py_modules",
]

C_AVAILABLE: bool = False

try:
    from zsys._core._zsys_core import (
        escape_html, strip_html, strip_markdown,
        truncate_text, split_text, get_args,
        format_bytes, format_duration,
        format_bold, format_italic, format_code, format_mono,
        format_pre, format_link, format_mention,
        format_underline, format_strikethrough, format_spoiler,
        format_quote, format_preformatted,
        build_help_text, build_modules_list,
        ansi_color, format_json_log,
        parse_meta_comments,
        match_prefix, nested_get,
        human_time, parse_duration,
        print_box_str, print_separator_str, print_table_str, print_progress_str,
        format_exc_html, router_lookup,
        get_proc_mem_mb, get_proc_cpu_pct, find_py_modules,
    )
    C_AVAILABLE = True

except ImportError:
    import html as _html
    import re as _re
    import json as _json

    def escape_html(text: str) -> str:
        return _html.escape(text, quote=True)

    def strip_html(text: str) -> str:
        return _html.unescape(_re.sub(r'<[^>]+>', '', text))

    def strip_markdown(text: str) -> str:
        text = _re.sub(r'```[\s\S]*?```', '', text)
        text = _re.sub(r'`(.+?)`', r'\1', text)
        text = _re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = _re.sub(r'__(.+?)__', r'\1', text)
        text = _re.sub(r'\*(.+?)\*', r'\1', text)
        text = _re.sub(r'_(.+?)_', r'\1', text)
        text = _re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        return text

    def truncate_text(text: str, max_length: int = 4096, suffix: str = "...") -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

    def split_text(text: str, max_length: int = 4096) -> list:
        if len(text) <= max_length:
            return [text]
        chunks, current = [], ""
        for line in text.split('\n'):
            if len(current) + len(line) + 1 <= max_length:
                current += line + '\n'
            else:
                if current:
                    chunks.append(current)
                if len(line) > max_length:
                    for i in range(0, len(line), max_length):
                        chunks.append(line[i:i + max_length])
                    current = ""
                else:
                    current = line + '\n'
        if current:
            chunks.append(current)
        return chunks

    def get_args(text: str, max_split: int = -1) -> list:
        parts = text.split(maxsplit=max_split + 1 if max_split > 0 else -1)
        return parts[1:] if len(parts) > 1 else []

    def format_bytes(size: int) -> str:
        val = float(size)
        for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
            if val < 1024.0:
                return f"{val:.1f} {unit}"
            val /= 1024.0
        return f"{val:.1f} PB"

    def format_duration(seconds: float) -> str:
        total = int(seconds)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        if h > 0: return f"{h}h {m}m {s}s"
        if m > 0: return f"{m}m {s}s"
        return f"{s}s"

    def format_bold(text: str, escape: bool = True) -> str:
        return f"<b>{escape_html(text) if escape else text}</b>"

    def format_italic(text: str, escape: bool = True) -> str:
        return f"<i>{escape_html(text) if escape else text}</i>"

    def format_code(text: str, escape: bool = False) -> str:
        return f"<code>{escape_html(text) if escape else text}</code>"

    def format_mono(text: str, escape: bool = True) -> str:
        return f"<code>{escape_html(text) if escape else text}</code>"

    def format_pre(text: str, language: str = None, escape: bool = False) -> str:
        body = escape_html(text) if escape else text
        if language:
            return f'<pre><code class="language-{language}">{body}</code></pre>'
        return f"<pre>{body}</pre>"

    def format_link(text: str, url: str, escape: bool = True) -> str:
        t = escape_html(text) if escape else text
        return f'<a href="{url}">{t}</a>'

    def format_mention(text: str, user_id: int, escape: bool = True) -> str:
        t = escape_html(text) if escape else text
        return f'<a href="tg://user?id={user_id}">{t}</a>'

    def build_help_text(module_name: str, commands: dict, prefix: str) -> str:
        lines = [f"<b>Help for |{module_name}|</b>\n<b>Usage:</b>"]
        for cmd, desc in commands.items():
            parts = cmd.split(maxsplit=1)
            cmd_name = parts[0]
            args = f" <code>{parts[1]}</code>" if len(parts) > 1 else ""
            lines.append(f"<code>{prefix}{cmd_name}</code>{args} — <i>{desc}</i>")
        return "\n".join(lines)

    def build_modules_list(modules: dict) -> str:
        if not modules:
            return "<b>Нет загруженных модулей</b>"
        lines = ["<b>Загруженные модули:</b>"]
        for name in sorted(modules.keys()):
            cnt = len(modules[name]) if isinstance(modules[name], dict) else 0
            lines.append(f"• <code>{name}</code> ({cnt} команд)")
        return "\n".join(lines)

    def ansi_color(text: str, code: str) -> str:
        return f"\033[{code}m{text}\033[0m"

    def format_json_log(level: str, message: str, ts: str) -> str:
        return _json.dumps({"level": level, "message": message, "ts": ts},
                           ensure_ascii=False)

    _META_RE     = _re.compile(r"^ *# *meta: *([^\s=]+) *= *(.*?) *$", _re.MULTILINE | _re.IGNORECASE)
    _LEGACY_RE   = _re.compile(r"^ *# *meta +(\S+) *: *(.*?)\s*$", _re.MULTILINE)
    _AT_RE       = _re.compile(r"^ *# *@(\S+) +(.*?) *$", _re.MULTILINE)

    def parse_meta_comments(code: str) -> dict:
        meta = {}
        for m in _META_RE.finditer(code):
            meta[m.group(1).lower()] = m.group(2).strip()
        for m in _LEGACY_RE.finditer(code):
            k = m.group(1).lower()
            if k not in meta:
                meta[k] = m.group(2).strip()
        for m in _AT_RE.finditer(code):
            k = m.group(1).lower()
            if k not in meta:
                meta[k] = m.group(2).strip()
        return meta

    def match_prefix(text: str, prefixes: list, trigger_set: set) -> bool:
        if not text:
            return False
        for p in prefixes:
            if text.startswith(p):
                rest = text[len(p):]
                word = rest.split()[0].lower() if rest.split() else ""
                if word in trigger_set:
                    return True
                break
        return False

    def nested_get(d: dict, key: str):
        current = d
        for part in key.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
            if current is None:
                return None
        return current if isinstance(current, str) else None

    def format_underline(text: str) -> str:
        return f"<u>{text}</u>"

    def format_strikethrough(text: str) -> str:
        return f"<s>{text}</s>"

    def format_spoiler(text: str) -> str:
        return f"<tg-spoiler>{text}</tg-spoiler>"

    def format_quote(text: str) -> str:
        return f"<blockquote>{text}</blockquote>"

    def format_preformatted(text: str) -> str:
        return f"<pre>{text}</pre>"

    def human_time(seconds: int, short: bool = True) -> str:
        seconds = max(0, int(seconds))
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        def _ru_plural(n: int, forms) -> str:
            n10, n100 = n % 10, n % 100
            if n10 == 1 and n100 != 11:
                idx = 0
            elif 2 <= n10 <= 4 and not (10 <= n100 <= 20):
                idx = 1
            else:
                idx = 2
            return forms[idx]

        parts = []
        if short:
            if days:    parts.append(f"{days} дн.")
            if hours:   parts.append(f"{hours} ч.")
            if minutes: parts.append(f"{minutes} мин.")
            if secs or not parts: parts.append(f"{secs} сек.")
        else:
            if days:    parts.append(f"{days} {_ru_plural(days, ('день','дня','дней'))}")
            if hours:   parts.append(f"{hours} {_ru_plural(hours, ('час','часа','часов'))}")
            if minutes: parts.append(f"{minutes} {_ru_plural(minutes, ('минута','минуты','минут'))}")
            if secs or not parts:
                parts.append(f"{secs} {_ru_plural(secs, ('секунда','секунды','секунд'))}")
        return " ".join(parts)

    def parse_duration(text: str):
        import re as _re2
        units = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
        matches = _re2.compile(r"(\d+)([smhdw])").findall(text.lower())
        if not matches:
            return None
        total = sum(int(v) * units[u] for v, u in matches)
        return total if total > 0 else None

    def print_box_str(text: str, padding: int = 2) -> str:
        lines = text.split("\n")
        max_len = max(len(line) for line in lines)
        inner = max_len + padding * 2
        top = "╔" + "═" * inner + "╗"
        bot = "╚" + "═" * inner + "╝"
        rows = [top]
        for line in lines:
            pad_r = inner - padding - len(line)
            rows.append("║" + " " * padding + line + " " * pad_r + "║")
        rows.append(bot)
        return "\n".join(rows)

    def print_separator_str(char: str = "═", length: int = 60) -> str:
        return char * length

    def print_table_str(headers: list, rows: list) -> str:
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        top = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
        sep = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
        bot = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"
        hdr = "│" + "│".join(f" {str(h).ljust(col_widths[i])} " for i, h in enumerate(headers)) + "│"
        lines = [top, hdr, sep]
        for row in rows:
            lines.append("│" + "│".join(f" {str(row[i] if i < len(row) else '').ljust(col_widths[i])} " for i in range(len(headers))) + "│")
        lines.append(bot)
        return "\n".join(lines)

    def print_progress_str(current: int, total: int, prefix: str = "Progress", length: int = 40) -> str:
        if total <= 0: total = 1
        percent = 100.0 * current / total
        filled = int(length * current / total)
        filled = max(0, min(filled, length))
        bar = "█" * filled + "░" * (length - filled)
        return f"{prefix}: |{bar}| {percent:.1f}% ({current}/{total})"

    def format_exc_html(
        error_type: str, error_text: str,
        cause_type: str = "", cause_text: str = "",
        suffix: str = "", max_length: int = 4000
    ) -> str:
        import html as _h
        def _e(s): return _h.escape(s)
        msg = f"<b>Error!</b>\n<code>{_e(error_type)}: {_e(error_text)}</code>"
        if cause_type:
            msg += f"\n<b>Caused by:</b> <code>{_e(cause_type)}: {_e(cause_text)}</code>"
        if suffix:
            msg += f"\n\n<b>{_e(suffix)}</b>"
        if max_length > 0 and len(msg) > max_length:
            msg = msg[:max_length - 3] + "..."
        return msg

    def router_lookup(trigger_map: dict, trigger: str):
        return trigger_map.get(trigger.lower())

    def get_proc_mem_mb() -> float:
        try:
            import os, psutil
            p = psutil.Process(os.getpid())
            return round(p.memory_info().rss / 1024 / 1024, 2)
        except Exception:
            return 0.0

    def get_proc_cpu_pct() -> float:
        try:
            import os, psutil
            return psutil.Process(os.getpid()).cpu_percent()
        except Exception:
            return 0.0

    def find_py_modules(path: str) -> list:
        import os
        try:
            return sorted(
                f[:-3] for f in os.listdir(path)
                if f.endswith(".py") and not f.startswith("_")
            )
        except OSError:
            return []
