"""
zsys.telegram.tdlib  —  Python bindings for libtg (TDLib C wrapper).

Provides TdlibClient and TdlibConfig as a drop-in alternative to
PyrogramClient / AiogramClient, with the same zsys IClient interface.

The actual Telegram protocol work is handled by libtg.so (C).
Python only manages high-level orchestration and module routing.

Example::

    from zsys.telegram.tdlib import TdlibClient, TdlibConfig

    cfg = TdlibConfig(api_id=123456, api_hash="abc123")
    client = TdlibClient(cfg)
    await client.start()
    await client.idle()
"""

from zsys.telegram.tdlib.config import TdlibConfig
from zsys.telegram.tdlib.client import TdlibClient

__all__ = ["TdlibClient", "TdlibConfig"]
