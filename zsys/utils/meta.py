"""Meta-comment parser for extracting metadata from source code.

Supports two formats:
1. New format:  # meta: key=value
2. Legacy format: # meta key: value
"""
# RU: Парсер мета-комментариев для извлечения метаданных из исходного кода.
# RU: Поддерживает новый формат (# meta: key=value) и устаревший (# meta key: value).
# RU: При наличии C-расширения делегирует парсинг ему для максимальной скорости.

import re
from typing import Dict

__all__ = ["parse_meta_comments", "extract_docstring_meta"]

try:
    from zsys._core import parse_meta_comments as _c_parse_meta, C_AVAILABLE as _C
except ImportError:
    _C = False

# Compile regex once at module load (используются только при C_AVAILABLE=False)
# RU: Компиляция регулярных выражений на этапе загрузки модуля экономит время на повторных вызовах.
META_COMMENT_REGEX = re.compile(
    r"^ *# *meta: *([^\s=]+) *= *(.*?) *$", re.MULTILINE | re.IGNORECASE
)

LEGACY_META_REGEX = re.compile(r"^ *# *meta +(\S+) *: *(.*?)\s*$", re.MULTILINE)


def parse_meta_comments(code: str) -> Dict[str, str]:
    """Extract meta-information from special comments in source code.

    Supports two comment formats:

    - New:    ``# meta: key=value``
    - Legacy: ``# meta key: value``

    When available, delegates to the faster C extension.

    Args:
        code: Source code as a string to scan for meta-comments.

    Returns:
        Dictionary mapping lowercased key names to their string values.
        New-format keys take precedence over legacy-format keys.

    Raises:
        Nothing — returns an empty dict when no meta-comments are found.
    """
    # RU: При наличии C-расширения делегирует ему парсинг для ускорения на больших файлах.
    if _C:
        return _c_parse_meta(code)
    meta: Dict[str, str] = {}
    for match in META_COMMENT_REGEX.finditer(code):
        meta[match.group(1).lower()] = match.group(2).strip()
    for match in LEGACY_META_REGEX.finditer(code):
        key = match.group(1).lower()
        if key not in meta:
            meta[key] = match.group(2).strip()
    return meta


def extract_docstring_meta(code: str) -> Dict[str, str]:
    """
    Extract metadata from module docstring.

    Looks for key-value pairs in format:
    Key: Value

    Args:
        code: Source code as string

    Returns:
        Dictionary with extracted metadata

    Examples:
        >>> code = '''
        ... \"\"\"
        ... Module description.
        ...
        ... Author: John Doe
        ... Version: 1.0.0
        ... \"\"\"
        ... '''
        >>> extract_docstring_meta(code)
        {'author': 'John Doe', 'version': '1.0.0'}
    """
    # RU: Ищет первый докстринг в файле и извлекает из него пары «ключ: значение».
    meta: Dict[str, str] = {}

    # Find docstring
    docstring_match = re.search(r"^(\'\'\'|\"\"\")(.*?)\1", code, re.DOTALL)
    if not docstring_match:
        return meta

    docstring = docstring_match.group(2)

    # Extract key-value pairs
    for line in docstring.split("\n"):
        match = re.match(r"^\s*(\w+):\s*(.+?)\s*$", line)
        if match:
            key = match.group(1).lower()
            value = match.group(2)
            meta[key] = value

    return meta
