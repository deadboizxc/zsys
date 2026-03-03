# -*- coding: utf-8 -*-
"""
zsys._core — C bindings for hot paths.

Uses the compiled ``_zsys_core.so`` extension when available.
Falls back transparently to a pure-Python implementation with an identical API.
"""
# RU: zsys._core — C-биндинги горячих путей.

__all__ = [
    "C_AVAILABLE",
    "escape_html",
    "strip_html",
    "strip_markdown",
    "truncate_text",
    "split_text",
    "get_args",
    "format_bytes",
    "format_duration",
    "format_bold",
    "format_italic",
    "format_code",
    "format_mono",
    "format_pre",
    "format_link",
    "format_mention",
    "format_underline",
    "format_strikethrough",
    "format_spoiler",
    "format_quote",
    "format_preformatted",
    "build_help_text",
    "build_modules_list",
    "ansi_color",
    "format_json_log",
    "parse_meta_comments",
    "match_prefix",
    "nested_get",
    "human_time",
    "parse_duration",
    "print_box_str",
    "print_separator_str",
    "print_table_str",
    "print_progress_str",
    "format_exc_html",
    "router_lookup",
    "get_proc_mem_mb",
    "get_proc_cpu_pct",
    "find_py_modules",
]

C_AVAILABLE: bool = False

try:
    from zsys._core._zsys_core import (
        escape_html,
        strip_html,
        strip_markdown,
        truncate_text,
        split_text,
        get_args,
        format_bytes,
        format_duration,
        format_bold,
        format_italic,
        format_code,
        format_mono,
        format_pre,
        format_link,
        format_mention,
        format_underline,
        format_strikethrough,
        format_spoiler,
        format_quote,
        format_preformatted,
        build_help_text,
        build_modules_list,
        ansi_color,
        format_json_log,
        parse_meta_comments,
        match_prefix,
        nested_get,
        human_time,
        parse_duration,
        print_box_str,
        print_separator_str,
        print_table_str,
        print_progress_str,
        format_exc_html,
        router_lookup,
        get_proc_mem_mb,
        get_proc_cpu_pct,
        find_py_modules,
    )

    C_AVAILABLE = True

except ImportError:
    import html as _html
    import re as _re
    import json as _json

    def escape_html(text: str) -> str:
        """Escape HTML special characters in a string.

        Args:
            text: Input string to escape.

        Returns:
            String with &, <, >, and " replaced by HTML entities.
        """
        # RU: Экранировать HTML-спецсимволы в строке.
        return _html.escape(text, quote=True)

    def strip_html(text: str) -> str:
        """Remove HTML tags from a string and unescape HTML entities.

        Args:
            text: HTML-formatted string.

        Returns:
            Plain text with all tags removed and entities decoded.
        """
        # RU: Удалить HTML-теги из строки и раскодировать HTML-сущности.
        return _html.unescape(_re.sub(r"<[^>]+>", "", text))

    def strip_markdown(text: str) -> str:
        """Remove Markdown formatting syntax from a string.

        Args:
            text: Markdown-formatted string.

        Returns:
            Plain text with code blocks, bold, italic, and link syntax removed.
        """
        # RU: Удалить Markdown-форматирование из строки.
        text = _re.sub(r"```[\s\S]*?```", "", text)
        text = _re.sub(r"`(.+?)`", r"\1", text)
        text = _re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = _re.sub(r"__(.+?)__", r"\1", text)
        text = _re.sub(r"\*(.+?)\*", r"\1", text)
        text = _re.sub(r"_(.+?)_", r"\1", text)
        text = _re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
        return text

    def truncate_text(text: str, max_length: int = 4096, suffix: str = "...") -> str:
        """Truncate text to a maximum length, appending a suffix when cut.

        Args:
            text: Input string.
            max_length: Maximum allowed length including the suffix.
            suffix: String appended when truncation occurs.

        Returns:
            Original text if within limit, otherwise truncated text with suffix.
        """
        # RU: Обрезать текст до максимальной длины, добавив суффикс.
        if len(text) <= max_length:
            return text
        return text[: max_length - len(suffix)] + suffix

    def split_text(text: str, max_length: int = 4096) -> list:
        """Split text into chunks that each fit within max_length characters.

        Args:
            text: Input string to split.
            max_length: Maximum character count per chunk.

        Returns:
            List of text chunks preserving line boundaries where possible.
        """
        # RU: Разбить текст на части, каждая не превышающая max_length символов.
        if len(text) <= max_length:
            return [text]
        chunks, current = [], ""
        for line in text.split("\n"):
            if len(current) + len(line) + 1 <= max_length:
                current += line + "\n"
            else:
                if current:
                    chunks.append(current)
                if len(line) > max_length:
                    for i in range(0, len(line), max_length):
                        chunks.append(line[i : i + max_length])
                    current = ""
                else:
                    current = line + "\n"
        if current:
            chunks.append(current)
        return chunks

    def get_args(text: str, max_split: int = -1) -> list:
        """Extract command arguments from a command string, skipping the command name.

        Args:
            text: Full command string including the command name as the first word.
            max_split: Maximum number of splits; -1 means unlimited.

        Returns:
            List of argument strings (everything after the first word).
        """
        # RU: Извлечь аргументы команды из строки, пропустив имя команды.
        parts = text.split(maxsplit=max_split + 1 if max_split > 0 else -1)
        return parts[1:] if len(parts) > 1 else []

    def format_bytes(size: int) -> str:
        """Format a byte count as a human-readable string with an appropriate unit.

        Args:
            size: Number of bytes.

        Returns:
            Human-readable string such as "1.5 MB" or "300.0 KB".
        """
        # RU: Форматировать количество байт в читаемую строку с единицей измерения.
        val = float(size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if val < 1024.0:
                return f"{val:.1f} {unit}"
            val /= 1024.0
        return f"{val:.1f} PB"

    def format_duration(seconds: float) -> str:
        """Format a duration in seconds as a compact human-readable string.

        Args:
            seconds: Duration in seconds.

        Returns:
            Formatted string such as "1h 2m 3s", "5m 30s", or "45s".
        """
        # RU: Форматировать длительность в секундах в читаемую строку.
        total = int(seconds)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h}h {m}m {s}s"
        if m > 0:
            return f"{m}m {s}s"
        return f"{s}s"

    def format_bold(text: str, escape: bool = True) -> str:
        """Wrap text in HTML bold tags for Telegram HTML mode.

        Args:
            text: Text to format.
            escape: If True, HTML-escape the text before wrapping.

        Returns:
            HTML string with text wrapped in <b>...</b>.
        """
        # RU: Обернуть текст в HTML-теги жирного шрифта для Telegram.
        return f"<b>{escape_html(text) if escape else text}</b>"

    def format_italic(text: str, escape: bool = True) -> str:
        """Wrap text in HTML italic tags for Telegram HTML mode.

        Args:
            text: Text to format.
            escape: If True, HTML-escape the text before wrapping.

        Returns:
            HTML string with text wrapped in <i>...</i>.
        """
        # RU: Обернуть текст в HTML-теги курсива для Telegram.
        return f"<i>{escape_html(text) if escape else text}</i>"

    def format_code(text: str, escape: bool = False) -> str:
        """Wrap text in HTML code tags for Telegram HTML mode.

        Args:
            text: Text to format.
            escape: If True, HTML-escape the text before wrapping.

        Returns:
            HTML string with text wrapped in <code>...</code>.
        """
        # RU: Обернуть текст в HTML-теги кода для Telegram.
        return f"<code>{escape_html(text) if escape else text}</code>"

    def format_mono(text: str, escape: bool = True) -> str:
        """Wrap text in HTML monospace code tags for Telegram HTML mode.

        Args:
            text: Text to format.
            escape: If True, HTML-escape the text before wrapping.

        Returns:
            HTML string with text wrapped in <code>...</code>.
        """
        # RU: Обернуть текст в HTML-теги моноширинного шрифта для Telegram.
        return f"<code>{escape_html(text) if escape else text}</code>"

    def format_pre(text: str, language: str = None, escape: bool = False) -> str:
        """Wrap text in an HTML pre block, optionally with a language class.

        Args:
            text: Text to format.
            language: Optional language identifier for syntax highlighting.
            escape: If True, HTML-escape the text before wrapping.

        Returns:
            HTML <pre> block, with nested <code class="language-X"> when language is set.
        """
        # RU: Обернуть текст в HTML-блок pre, опционально с указанием языка.
        body = escape_html(text) if escape else text
        if language:
            return f'<pre><code class="language-{language}">{body}</code></pre>'
        return f"<pre>{body}</pre>"

    def format_link(text: str, url: str, escape: bool = True) -> str:
        """Format a clickable HTML hyperlink for Telegram HTML mode.

        Args:
            text: Display text of the link.
            url: Target URL.
            escape: If True, HTML-escape the display text.

        Returns:
            HTML anchor tag string.
        """
        # RU: Сформировать HTML-гиперссылку для Telegram.
        t = escape_html(text) if escape else text
        return f'<a href="{url}">{t}</a>'

    def format_mention(text: str, user_id: int, escape: bool = True) -> str:
        """Format a Telegram user mention link using the tg://user scheme.

        Args:
            text: Display name for the mention.
            user_id: Telegram numeric user ID.
            escape: If True, HTML-escape the display name.

        Returns:
            HTML anchor tag pointing to tg://user?id=<user_id>.
        """
        # RU: Сформировать ссылку-упоминание пользователя Telegram.
        t = escape_html(text) if escape else text
        return f'<a href="tg://user?id={user_id}">{t}</a>'

    def build_help_text(module_name: str, commands: dict, prefix: str) -> str:
        """Build formatted HTML help text for a bot module.

        Args:
            module_name: Name of the module to display in the header.
            commands: Mapping of "command [args]" strings to their descriptions.
            prefix: Command prefix character (e.g. ".").

        Returns:
            HTML-formatted help string listing all commands with descriptions.
        """
        # RU: Сформировать HTML-текст помощи для модуля бота.
        lines = [f"<b>Help for |{module_name}|</b>\n<b>Usage:</b>"]
        for cmd, desc in commands.items():
            parts = cmd.split(maxsplit=1)
            cmd_name = parts[0]
            args = f" <code>{parts[1]}</code>" if len(parts) > 1 else ""
            lines.append(f"<code>{prefix}{cmd_name}</code>{args} — <i>{desc}</i>")
        return "\n".join(lines)

    def build_modules_list(modules: dict) -> str:
        """Build a formatted HTML list of all currently loaded modules.

        Args:
            modules: Mapping of module names to their command dictionaries.

        Returns:
            HTML-formatted string listing each module and its command count.
        """
        # RU: Сформировать HTML-список загруженных модулей.
        if not modules:
            return "<b>Нет загруженных модулей</b>"
        lines = ["<b>Загруженные модули:</b>"]
        for name in sorted(modules.keys()):
            cnt = len(modules[name]) if isinstance(modules[name], dict) else 0
            lines.append(f"• <code>{name}</code> ({cnt} команд)")
        return "\n".join(lines)

    def ansi_color(text: str, code: str) -> str:
        """Wrap text with ANSI escape codes for terminal color output.

        Args:
            text: Text to colorize.
            code: ANSI color/style code (e.g. "31" for red, "1" for bold).

        Returns:
            String with ANSI escape sequences prepended and a reset appended.
        """
        # RU: Обернуть текст ANSI-кодами для цветного вывода в терминал.
        return f"\033[{code}m{text}\033[0m"

    def format_json_log(level: str, message: str, ts: str) -> str:
        """Serialize a log entry as a JSON string.

        Args:
            level: Log severity level (e.g. "INFO", "ERROR").
            message: Human-readable log message.
            ts: Timestamp string.

        Returns:
            JSON string with keys: level, message, ts.
        """
        # RU: Сериализовать запись лога в JSON-строку.
        return _json.dumps(
            {"level": level, "message": message, "ts": ts}, ensure_ascii=False
        )

    _META_RE = _re.compile(
        r"^ *# *meta: *([^\s=]+) *= *(.*?) *$", _re.MULTILINE | _re.IGNORECASE
    )
    _LEGACY_RE = _re.compile(r"^ *# *meta +(\S+) *: *(.*?)\s*$", _re.MULTILINE)
    _AT_RE = _re.compile(r"^ *# *@(\S+) +(.*?) *$", _re.MULTILINE)

    def parse_meta_comments(code: str) -> dict:
        """Parse meta-comment annotations from Python source code.

        Supports three annotation formats:
          - ``# meta: key = value``
          - ``# meta key: value``
          - ``# @key value``

        Args:
            code: Python source code string to scan.

        Returns:
            Dictionary mapping annotation keys (lowercased) to their values.
        """
        # RU: Разобрать мета-комментарии из исходного кода Python.
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
        """Check whether a message text starts with a known prefix and a registered trigger.

        Args:
            text: Raw message text to test.
            prefixes: List of command prefix strings (e.g. [".", "!"]).
            trigger_set: Set of registered command trigger names.

        Returns:
            True if the text matches prefix + known trigger, False otherwise.
        """
        # RU: Проверить, начинается ли текст с известного префикса и зарегистрированного триггера.
        if not text:
            return False
        for p in prefixes:
            if text.startswith(p):
                rest = text[len(p) :]
                word = rest.split()[0].lower() if rest.split() else ""
                if word in trigger_set:
                    return True
                break
        return False

    def nested_get(d: dict, key: str):
        """Retrieve a string value from a nested dict using a dot-separated key path.

        Args:
            d: Source dictionary, potentially nested.
            key: Dot-separated path string (e.g. "a.b.c").

        Returns:
            The string value at the path, or None if any segment is missing or
            the final value is not a string.
        """
        # RU: Получить строковое значение из вложенного словаря по пути с точками.
        current = d
        for part in key.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
            if current is None:
                return None
        return current if isinstance(current, str) else None

    def format_underline(text: str) -> str:
        """Wrap text in HTML underline tags for Telegram HTML mode.

        Args:
            text: Text to underline.

        Returns:
            HTML string with text wrapped in <u>...</u>.
        """
        # RU: Обернуть текст в HTML-теги подчёркивания для Telegram.
        return f"<u>{text}</u>"

    def format_strikethrough(text: str) -> str:
        """Wrap text in HTML strikethrough tags for Telegram HTML mode.

        Args:
            text: Text to strike through.

        Returns:
            HTML string with text wrapped in <s>...</s>.
        """
        # RU: Обернуть текст в HTML-теги зачёркивания для Telegram.
        return f"<s>{text}</s>"

    def format_spoiler(text: str) -> str:
        """Wrap text in Telegram spoiler tags to hide it until tapped.

        Args:
            text: Text to hide as a spoiler.

        Returns:
            String wrapped in <tg-spoiler>...</tg-spoiler>.
        """
        # RU: Обернуть текст в Telegram-теги спойлера.
        return f"<tg-spoiler>{text}</tg-spoiler>"

    def format_quote(text: str) -> str:
        """Wrap text in HTML blockquote tags for Telegram HTML mode.

        Args:
            text: Text to quote.

        Returns:
            HTML string with text wrapped in <blockquote>...</blockquote>.
        """
        # RU: Обернуть текст в HTML-теги цитаты для Telegram.
        return f"<blockquote>{text}</blockquote>"

    def format_preformatted(text: str) -> str:
        """Wrap text in HTML pre tags without a language annotation.

        Args:
            text: Preformatted text to wrap.

        Returns:
            HTML string with text wrapped in <pre>...</pre>.
        """
        # RU: Обернуть текст в HTML-теги предформатированного блока.
        return f"<pre>{text}</pre>"

    def human_time(seconds: int, short: bool = True) -> str:
        """Format a duration in seconds as a human-readable Russian time string.

        Args:
            seconds: Duration in seconds (negative values are clamped to 0).
            short: If True, use abbreviated labels (дн./ч./мин./сек.);
                   if False, use full Russian word forms with correct plurals.

        Returns:
            Space-joined string of time components (e.g. "2 ч. 5 мин. 30 сек.").
        """
        # RU: Форматировать длительность в читаемую строку на русском языке.
        seconds = max(0, int(seconds))
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        def _ru_plural(n: int, forms) -> str:
            """Choose the correct Russian plural form for a given number.

            Args:
                n: The integer to select the form for.
                forms: Tuple of three word forms (singular, few, many).

            Returns:
                The grammatically correct form string for n.
            """
            # RU: Выбрать правильную форму русского слова для числа n.
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
            if days:
                parts.append(f"{days} дн.")
            if hours:
                parts.append(f"{hours} ч.")
            if minutes:
                parts.append(f"{minutes} мин.")
            if secs or not parts:
                parts.append(f"{secs} сек.")
        else:
            if days:
                parts.append(f"{days} {_ru_plural(days, ('день', 'дня', 'дней'))}")
            if hours:
                parts.append(f"{hours} {_ru_plural(hours, ('час', 'часа', 'часов'))}")
            if minutes:
                parts.append(
                    f"{minutes} {_ru_plural(minutes, ('минута', 'минуты', 'минут'))}"
                )
            if secs or not parts:
                parts.append(
                    f"{secs} {_ru_plural(secs, ('секунда', 'секунды', 'секунд'))}"
                )
        return " ".join(parts)

    def parse_duration(text: str):
        """Parse a compact duration string into a total number of seconds.

        Recognized unit suffixes: s (seconds), m (minutes), h (hours),
        d (days), w (weeks). Example: "1h30m" → 5400.

        Args:
            text: Duration string containing one or more value+unit pairs.

        Returns:
            Total duration in seconds as an integer, or None if no valid units found.
        """
        # RU: Разобрать строку длительности в общее количество секунд.
        import re as _re2

        units = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
        matches = _re2.compile(r"(\d+)([smhdw])").findall(text.lower())
        if not matches:
            return None
        total = sum(int(v) * units[u] for v, u in matches)
        return total if total > 0 else None

    def print_box_str(text: str, padding: int = 2) -> str:
        """Render multi-line text surrounded by a Unicode double-line box border.

        Args:
            text: Text to enclose; newlines create separate rows inside the box.
            padding: Number of space characters to add on each side of each line.

        Returns:
            Multi-line string forming a box drawn with ╔═╗/╚═╝/║ characters.
        """
        # RU: Отобразить текст в рамке из символов Юникода.
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
        """Generate a horizontal separator line of repeated characters.

        Args:
            char: Character to repeat.
            length: Total length of the separator.

        Returns:
            String of char repeated length times.
        """
        # RU: Создать горизонтальную разделительную линию из повторяющихся символов.
        return char * length

    def print_table_str(headers: list, rows: list) -> str:
        """Render a list of rows as a Unicode box-drawing table.

        Args:
            headers: List of column header strings.
            rows: List of row lists; each inner list provides cell values.

        Returns:
            Multi-line string with a Unicode table including header and separator rows.
        """
        # RU: Отобразить строки данных в виде таблицы с символами Юникода.
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        top = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
        sep = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
        bot = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"
        hdr = (
            "│"
            + "│".join(
                f" {str(h).ljust(col_widths[i])} " for i, h in enumerate(headers)
            )
            + "│"
        )
        lines = [top, hdr, sep]
        for row in rows:
            lines.append(
                "│"
                + "│".join(
                    f" {str(row[i] if i < len(row) else '').ljust(col_widths[i])} "
                    for i in range(len(headers))
                )
                + "│"
            )
        lines.append(bot)
        return "\n".join(lines)

    def print_progress_str(
        current: int, total: int, prefix: str = "Progress", length: int = 40
    ) -> str:
        """Render a text progress bar string.

        Args:
            current: Current progress value.
            total: Maximum progress value.
            prefix: Label displayed before the bar.
            length: Number of characters in the bar itself.

        Returns:
            Progress bar string like "Progress: |████░░░░| 50.0% (5/10)".
        """
        # RU: Отобразить текстовый индикатор прогресса.
        if total <= 0:
            total = 1
        percent = 100.0 * current / total
        filled = int(length * current / total)
        filled = max(0, min(filled, length))
        bar = "█" * filled + "░" * (length - filled)
        return f"{prefix}: |{bar}| {percent:.1f}% ({current}/{total})"

    def format_exc_html(
        error_type: str,
        error_text: str,
        cause_type: str = "",
        cause_text: str = "",
        suffix: str = "",
        max_length: int = 4000,
    ) -> str:
        """Format an exception as an HTML message suitable for sending via Telegram.

        Args:
            error_type: Exception class name (e.g. "ValueError").
            error_text: Exception message text.
            cause_type: Optional chained exception class name.
            cause_text: Optional chained exception message.
            suffix: Optional additional note appended in bold.
            max_length: Maximum total length; the message is truncated if exceeded.

        Returns:
            HTML-formatted error string ready for Telegram HTML parse mode.
        """
        # RU: Форматировать исключение в HTML-сообщение для отправки через Telegram.
        import html as _h

        def _e(s):
            """HTML-escape a string using the locally imported html module.

            Args:
                s: String to escape.

            Returns:
                HTML-escaped string.
            """
            # RU: Экранировать строку HTML с помощью локально импортированного модуля html.
            return _h.escape(s)

        msg = f"<b>Error!</b>\n<code>{_e(error_type)}: {_e(error_text)}</code>"
        if cause_type:
            msg += (
                f"\n<b>Caused by:</b> <code>{_e(cause_type)}: {_e(cause_text)}</code>"
            )
        if suffix:
            msg += f"\n\n<b>{_e(suffix)}</b>"
        if max_length > 0 and len(msg) > max_length:
            msg = msg[: max_length - 3] + "..."
        return msg

    def router_lookup(trigger_map: dict, trigger: str):
        """Look up a command handler in the router trigger map by trigger name.

        Args:
            trigger_map: Dictionary mapping lowercase trigger strings to command objects.
            trigger: Trigger name to look up (case-insensitive).

        Returns:
            Command object if found, or None if the trigger is not registered.
        """
        # RU: Найти обработчик команды в карте триггеров роутера.
        return trigger_map.get(trigger.lower())

    def get_proc_mem_mb() -> float:
        """Get the current process resident memory usage in megabytes.

        Returns:
            RSS memory in MB rounded to two decimal places, or 0.0 on error.
        """
        # RU: Получить объём резидентной памяти текущего процесса в мегабайтах.
        try:
            import os
            import psutil

            p = psutil.Process(os.getpid())
            return round(p.memory_info().rss / 1024 / 1024, 2)
        except Exception:
            return 0.0

    def get_proc_cpu_pct() -> float:
        """Get the current process CPU usage as a percentage.

        Returns:
            CPU usage percentage as a float, or 0.0 on error.
        """
        # RU: Получить загрузку CPU текущего процесса в процентах.
        try:
            import os
            import psutil

            return psutil.Process(os.getpid()).cpu_percent()
        except Exception:
            return 0.0

    def find_py_modules(path: str) -> list:
        """Find all Python module names (non-private .py files) in a directory.

        Args:
            path: Directory path to scan.

        Returns:
            Sorted list of module name strings (filenames without .py extension),
            or an empty list if the directory does not exist or is unreadable.
        """
        # RU: Найти имена всех Python-модулей (не приватных .py-файлов) в директории.
        import os

        try:
            return sorted(
                f[:-3]
                for f in os.listdir(path)
                if f.endswith(".py") and not f.startswith("_")
            )
        except OSError:
            return []
