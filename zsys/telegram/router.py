"""attach_router — connect zsys.modules @command() handlers to TdlibClient.

Mirrors the pattern from zsys.telegram.pyrogram.router but works with
TdlibClient instead of pyrogram.Client.
"""
# RU: Подключение zsys.modules роутера к TdlibClient.

from __future__ import annotations

from typing import TYPE_CHECKING

from zsys.telegram.binding import TG_FILTER_INCOMING, TG_FILTER_TEXT

if TYPE_CHECKING:
    from zsys.modules.router import Router
    from zsys.telegram.client import TdlibClient


def attach_router(router: "Router", client: "TdlibClient", prefix: str = ".") -> None:
    """Connect all @command() handlers from router to client.

    Registers a single TG_FILTER_INCOMING | TG_FILTER_TEXT handler that
    checks the message text against the router's prefix+trigger table and
    dispatches to the correct @command() function.

    Args:
        router: The zsys default router (get_default_router()).
        client: The TdlibClient instance.
        prefix: Command prefix character(s). Default ".".
    """
    # RU: Регистрируем один хендлер — он роутит команды через zsys.modules.
    from zsys.modules.context.base import BaseContext

    filters = TG_FILTER_INCOMING | TG_FILTER_TEXT

    async def _dispatch(cl: "TdlibClient", msg) -> None:
        text = msg.text or ""
        if not text.startswith(prefix):
            return

        # Strip prefix, extract command (first word)
        body = text[len(prefix) :]
        trigger = body.split()[0].lower() if body.split() else ""
        if not trigger:
            return

        handler_id = router.lookup(trigger)
        if handler_id < 0:
            return

        fn = router.get_handler_fn(handler_id)
        if fn is None:
            return

        ctx = BaseContext(
            client=cl,
            message=msg,
            trigger=trigger,
            args=body.split()[1:],
        )
        await fn(ctx)

    client.on_message(filters)(_dispatch)


__all__ = ["attach_router"]
