"""
Pyrogram-specific router attachment.

Extracts the pyrogram attachment logic from zsys.modules.Router into a
standalone function, keeping zsys.modules platform-independent.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, List, Union

from zsys._core import match_prefix as _c_match_prefix, C_AVAILABLE as _C_AVAILABLE

if TYPE_CHECKING:
    from pyrogram import Client as PyrogramClient
    from zsys.modules.router import Router


def attach_router(
    router: "Router",
    client: "PyrogramClient",
    prefix: Union[str, List[str]] = ".",
    owner_only: bool = True,
) -> None:
    """
    Attach a zsys Router to a Pyrogram client with dynamic command lookup.

    Commands are looked up at runtime, so hot reload works automatically.

    Args:
        router: zsys Router instance
        client: Pyrogram Client instance
        prefix: Command prefix(es)
        owner_only: If True, only handle messages from self
    """
    # RU: Подключить zsys Router к Pyrogram-клиенту с динамическим поиском команд.
    from pyrogram import filters
    from pyrogram.handlers import MessageHandler
    from zsys.telegram.pyrogram.context import PyrogramContext

    prefixes = [prefix] if isinstance(prefix, str) else prefix
    router._prefixes = prefixes
    router._attached_clients.append(client)

    # The trigger set is rebuilt automatically on hot reload
    # RU: Набор триггеров перестраивается при горячей перезагрузке
    def _get_trigger_set():
        """Return the current set of registered trigger names.

        Returns:
            Set of trigger name strings from the router's trigger map.
        """
        # RU: Вернуть текущий набор зарегистрированных триггеров.
        return set(router._trigger_map.keys())

    if _C_AVAILABLE:

        def dynamic_command_filter(_, __, message):
            """Filter messages that match a known command prefix and trigger (C-accelerated).

            Args:
                _: Unused filter argument.
                __: Unused client argument.
                message: Incoming Pyrogram message.

            Returns:
                True if the message matches a registered command.
            """
            # RU: Фильтр сообщений, соответствующих известному префиксу и триггеру (C-ускорение).
            text = message.text or message.caption or ""
            return _c_match_prefix(text, prefixes, _get_trigger_set())
    else:

        def dynamic_command_filter(_, __, message):
            """Filter messages that match a known command prefix and trigger (Python fallback).

            Args:
                _: Unused filter argument.
                __: Unused client argument.
                message: Incoming Pyrogram message.

            Returns:
                True if the message matches a registered command.
            """
            # RU: Фильтр сообщений, соответствующих известному префиксу и триггеру (Python-резерв).
            text = message.text or message.caption or ""
            if not text:
                return False
            for p in prefixes:
                if text.startswith(p):
                    cmd_text = (
                        text[len(p) :].split()[0].lower() if text[len(p) :] else ""
                    )
                    if cmd_text in router._trigger_map:
                        return True
            for trigger, cmd in router._trigger_map.items():
                if cmd.prefix:
                    cmd_prefixes = (
                        [cmd.prefix] if isinstance(cmd.prefix, str) else cmd.prefix
                    )
                    for p in cmd_prefixes:
                        if text.startswith(p):
                            cmd_text = (
                                text[len(p) :].split()[0].lower()
                                if text[len(p) :]
                                else ""
                            )
                            if cmd_text == trigger:
                                return True
            return False

    base_filter = filters.create(dynamic_command_filter, "DynamicCommand")
    if owner_only:
        base_filter = base_filter & filters.me

    async def _pyrogram_handler(client, message):
        """Handle an incoming Pyrogram message and dispatch it to the matching command.

        Args:
            client: Pyrogram Client instance.
            message: Incoming Pyrogram Message object.
        """
        # RU: Обработать входящее сообщение Pyrogram и передать его нужной команде.
        text = message.text or message.caption or ""
        if not text:
            return

        parts = text.split(maxsplit=1)
        cmd_part = parts[0]

        matched = False
        for p in prefixes:
            if cmd_part.startswith(p):
                cmd_part = cmd_part[len(p) :]
                matched = True
                break

        if not matched:
            for trigger, cmd_candidate in router._trigger_map.items():
                if cmd_candidate.prefix:
                    cmd_pxs = (
                        [cmd_candidate.prefix]
                        if isinstance(cmd_candidate.prefix, str)
                        else cmd_candidate.prefix
                    )
                    for p in cmd_pxs:
                        if cmd_part.startswith(p):
                            candidate = cmd_part[len(p) :].lower()
                            if candidate == trigger:
                                cmd_part = candidate
                                matched = True
                                break
                if matched:
                    break

        if not matched:
            return

        cmd = router.get_command(cmd_part)
        if not cmd:
            return

        if cmd.reply_only and not message.reply_to_message:
            await message.edit_text(router._messages["reply_required"])
            return

        if cmd.media_only:
            has_media = (
                message.photo
                or message.video
                or message.document
                or message.animation
                or message.audio
                or message.voice
                or message.video_note
                or message.sticker
                or (
                    message.reply_to_message
                    and (
                        message.reply_to_message.photo
                        or message.reply_to_message.video
                        or message.reply_to_message.document
                        or message.reply_to_message.animation
                    )
                )
            )
            if not has_media:
                await message.edit_text(router._messages["media_required"])
                return

        if cmd.text_only and not (len(parts) > 1 and parts[1].strip()):
            await message.edit_text(
                router._messages["text_required"].format(cmd=cmd.name, usage=cmd.usage)
            )
            return

        if cmd.extra_filters:
            try:
                if asyncio.iscoroutinefunction(cmd.extra_filters):
                    if not await cmd.extra_filters(client, message):
                        return
                elif callable(cmd.extra_filters):
                    result = cmd.extra_filters(client, message)
                    if asyncio.iscoroutine(result):
                        if not await result:
                            return
                    elif not result:
                        return
            except Exception:
                pass

        args = parts[1].split() if len(parts) > 1 else []
        ctx = PyrogramContext(client, message, command=cmd.name, args=args)

        if cmd.private_only and not ctx.chat.is_private:
            return
        if cmd.group_only and ctx.chat.is_private:
            return

        try:
            await cmd.handler(ctx)
        except Exception as e:
            await ctx.reply(router._messages["error"].format(error=e))

    handler = MessageHandler(_pyrogram_handler, base_filter)
    client.add_handler(handler)
    router._handler = handler


__all__ = ["attach_router"]
