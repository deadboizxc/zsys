# -*- coding: utf-8 -*-
"""
#name: Help
#description: Show help for all modules and commands
#author: deadboizxc
#version: 1.0.0

Unified help system - displays registered commands and modules.
"""

from zsys.modules import (
    command,
    Context,
    modules_help,
    get_modules_help,
    get_default_router,
)


@command(
    "help",
    aliases=["h", "?"],
    description="Show help for modules",
    usage="[module_name]",
    category="system",
)
async def help_cmd(ctx: Context):
    """Show help for modules and commands."""
    router = get_default_router()

    if ctx.has_args:
        # Show help for specific module
        module_name = ctx.args[0].lower()

        # Check modules_help dict first
        if module_name in modules_help:
            help_data = modules_help[module_name]
            lines = [f"📖 <b>{module_name}</b>\n"]

            for cmd, desc in help_data.items():
                # Parse command format: "cmd [args]*" -> cmd, args, required
                parts = cmd.split("[", 1)
                cmd_name = parts[0].strip()
                args = f"[{parts[1]}" if len(parts) > 1 else ""
                lines.append(f"  <code>.{cmd_name}</code> {args}\n    {desc}")

            await ctx.edit("\n".join(lines), parse_mode="html")
            return

        # Check router commands
        cmd_obj = router.get_command(module_name)
        if cmd_obj:
            aliases = ", ".join(cmd_obj.aliases) if cmd_obj.aliases else "нет"
            text = (
                f"📖 <b>{cmd_obj.name}</b>\n\n"
                f"📝 {cmd_obj.description or 'Нет описания'}\n"
                f"📦 Категория: {cmd_obj.category}\n"
                f"🔄 Алиасы: {aliases}\n"
                f"💡 Использование: <code>.{cmd_obj.name} {cmd_obj.usage}</code>"
            )
            await ctx.edit(text, parse_mode="html")
            return

        await ctx.edit(
            f"❌ Модуль или команда <code>{module_name}</code> не найдена",
            parse_mode="html",
        )
        return

    # Show all modules/commands
    lines = ["📚 <b>Справка по модулям</b>\n"]

    # From modules_help dict
    if modules_help:
        lines.append("<b>📦 Модули:</b>")
        for module_name in sorted(modules_help.keys()):
            cmd_count = len(modules_help[module_name])
            lines.append(f"  • <code>{module_name}</code> ({cmd_count} команд)")

    # From router
    categories = get_modules_help()
    if categories:
        lines.append("\n<b>🔧 Категории команд:</b>")
        for category, commands in sorted(categories.items()):
            cmd_names = ", ".join(f".{c.name}" for c in commands[:5])
            if len(commands) > 5:
                cmd_names += f" (+{len(commands) - 5})"
            lines.append(f"  • <b>{category}</b>: {cmd_names}")

    lines.append("\n💡 <code>.help [модуль]</code> - подробнее о модуле")

    await ctx.edit("\n".join(lines), parse_mode="html")


@command(
    "modules",
    aliases=["mods"],
    description="List all loaded modules",
    category="system",
)
async def modules_cmd(ctx: Context):
    """List all registered modules."""
    if not modules_help:
        await ctx.edit("📦 Модулей не загружено")
        return

    lines = ["📦 <b>Загруженные модули:</b>\n"]

    # Count total commands
    total_cmds = sum(len(cmds) for cmds in modules_help.values())

    for name in sorted(modules_help.keys()):
        cmd_count = len(modules_help[name])
        lines.append(f"  • <code>{name}</code> ({cmd_count})")

    lines.append(f"\n📊 Всего: {len(modules_help)} модулей, {total_cmds} команд")

    await ctx.edit("\n".join(lines), parse_mode="html")


modules_help["help"] = {
    "help [module]": "Show module help",
    "modules": "List all loaded modules",
}
