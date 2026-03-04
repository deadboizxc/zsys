# -*- coding: utf-8 -*-
"""
#name: Ping
#description: Check bot/userbot latency
#author: deadboizxc
#version: 1.0.0

Unified ping module - works on all platforms.
"""

import time

from zsys.modules import Context, command, modules_help


@command(
    "ping",
    aliases=["p"],
    description="Check latency",
    category="utils",
)
async def ping_cmd(ctx: Context):
    """Measure and display response latency."""
    start = time.perf_counter()
    msg = await ctx.reply("🏓 Pong!")  # noqa: F841
    end = time.perf_counter()

    latency_ms = (end - start) * 1000
    await ctx.edit(
        f"🏓 <b>Pong!</b>\n⚡ <code>{latency_ms:.2f}ms</code>", parse_mode="html"
    )


@command(
    "pong",
    description="Reply with Ping",
    category="utils",
)
async def pong_cmd(ctx: Context):
    """Reply with ping."""
    await ctx.reply("🏓 Ping!")


modules_help["ping"] = {
    "ping": "Check response latency",
    "pong": "Reply with Ping!",
}
