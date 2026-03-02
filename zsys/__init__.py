"""ZSYS - Modular Python Ecosystem.

A flexible framework for building bots, userbots, APIs, storage solutions,
blockchain integrations, and crypto services.  Every subsystem is exposed
as an independent importable package so only the required components need
to be installed.
"""
# RU: ZSYS — модульная экосистема Python.
# RU: Гибкий фреймворк для ботов, юзерботов, API, хранилищ,
# RU: блокчейн-интеграций и крипто-сервисов.

__version__ = "1.0.0"
__author__ = "deadboizxc"

# Core exports
# TODO: Restore when interfaces module exists
# from zsys.core.interfaces import (
#     IClient,
#     IBot,
#     IChat,
#     ChatType,
#     IStorage,
#     ICipher,
#     IBlockchain,
#     IWallet,
# )

__all__ = [
    "__version__",
    "__author__",
    # Interfaces (commented until interfaces module exists)
    # "IClient",
    # "IBot",
    # "IChat",
    # "ChatType",
    # "IStorage",
    # "ICipher",
    # "IBlockchain",
    # "IWallet",
]
