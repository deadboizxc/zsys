# -*- coding: utf-8 -*-
"""
zsys.modules.examples - Примеры унифицированных модулей.

Эти модули работают на любой платформе:
- Pyrogram (zxc_userbot)
- Aiogram (боты)
- Telebot (боты)

Импорт модулей:
    from zsys.modules.examples import say, ping
"""

from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent

__all__ = ["EXAMPLES_DIR"]
