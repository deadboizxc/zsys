# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
"""Hot-path Cython extensions for zsys command router.

Typed Cython implementations of the two innermost dispatch functions.
Serves as the intermediate tier between pure Python and the C extension:

  Tier 1 — C extension ``_zsys_core`` ``match_prefix``  (fastest).
  Tier 2 — Cython ``_router_dispatch.so``                (this file).
  Tier 3 — Pure Python                                   (always available).

Functions
---------
parse_command_c     : Detect prefix, extract command name and arg tail.
check_trigger_c     : Combined prefix+trigger check for message filters.
"""
# RU: Горячие пути маршрутизатора команд на Cython. Промежуточный уровень
# между чистым Python и C-расширением _zsys_core.


cpdef object parse_command_c(str text, list prefixes):
    """Detect a command prefix in *text* and split into components.

    Iterates over *prefixes* in order.  On the first match, returns a
    three-tuple; returns ``None`` if no prefix matched or the command
    name is empty.

    Args:
        text:     Incoming message text.
        prefixes: Ordered list of prefix strings, e.g. ``[".", "!"]``.

    Returns:
        ``(prefix, command_name_lower, arg_tail)`` tuple, or ``None``
        if no prefix matched.

    Example:
        >>> parse_command_c(".ping hello world", ["."])
        (".", "ping", "hello world")

    # RU: Определяет префикс команды в тексте и разбивает на компоненты.
    # RU: Возвращает (prefix, cmd_lower, args) или None если нет совпадения.
    """
    cdef str prefix, stripped, cmd_name, args
    cdef int plen, space_idx

    for prefix in prefixes:
        plen = len(prefix)
        if text[:plen] == prefix:
            stripped = text[plen:]
            if not stripped:
                return None
            space_idx = stripped.find(' ')
            if space_idx == -1:
                return (prefix, stripped.lower(), '')
            cmd_name = stripped[:space_idx].lower()
            args = stripped[space_idx + 1:]
            return (prefix, cmd_name, args)
    return None


cpdef bint check_trigger_c(str text, list prefixes, set trigger_map_keys):
    """Return ``True`` if *text* matches any registered command trigger.

    Combines prefix detection with trigger map lookup in a single Cython
    function to avoid the Python call overhead on every incoming message.

    Args:
        text:             Incoming message text (may be empty).
        prefixes:         List of command prefix strings.
        trigger_map_keys: ``set`` of lower-cased trigger names currently
                          registered in the router.

    Returns:
        ``True`` if the message is a known command, ``False`` otherwise.

    # RU: Возвращает True если текст соответствует зарегистрированной команде.
    # RU: Объединяет проверку префикса и поиск по триггерам в одной функции.
    """
    cdef str prefix, cmd_text
    cdef int plen, space_idx

    if not text:
        return False

    for prefix in prefixes:
        plen = len(prefix)
        if text[:plen] == prefix:
            rest = text[plen:]
            if not rest:
                return False
            space_idx = rest.find(' ')
            if space_idx == -1:
                cmd_text = rest.lower()
            else:
                cmd_text = rest[:space_idx].lower()
            return cmd_text in trigger_map_keys

    return False
