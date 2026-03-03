# -*- coding: utf-8 -*-
"""
#name: Say
#description: Send text without userbot processing
#author: deadboizxc
#version: 1.0.0

Unified say module - works on all platforms.

Example usage:
    .say Hello world    -> <code>Hello world</code>
    .say !Reply text    -> Reply with <code>Reply text</code>
"""

from zsys.modules import command, Context, modules_help


@command(
    "say",
    aliases=["s"],
    description="Send text without processing",
    usage="<text>",
    category="utils",
    text_only=True,  # Requires text argument
)
async def say_cmd(ctx: Context):
    """Send text as code block."""
    text = ctx.arg

    # Reply mode with !
    if ctx.is_reply and text.startswith("!"):
        text = text[1:].strip()
        await ctx.delete()
        await ctx.reply(f"<code>{text}</code>", parse_mode="html")
    else:
        await ctx.edit(f"<code>{text}</code>", parse_mode="html")


# Module help registration
modules_help["say"] = {
    "say [text]*": "Send text as code block",
    "say ![text]*": "Reply with text as code block (delete original)",
}
