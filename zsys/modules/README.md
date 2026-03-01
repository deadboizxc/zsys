# zsys Unified Module System

Write modules once — they work everywhere: Pyrogram, aiogram, telebot.

**[Русская версия](#единая-система-модулей-zsys)**

## Quick Start

```python
from zsys.modules import command, Context, modules_help

@command("hello", description="Greeting")
async def hello(ctx: Context):
    await ctx.reply(f"Hello, {ctx.user.first_name}!")

modules_help["greet"] = {"hello": "Send a greeting"}
```

## @command Decorator API

```python
@command(
    name="download",           # Command name (required)
    aliases=["dl", "d"],       # Alternative names
    description="Download",    # Description for help
    usage="<url>",             # Usage example
    category="media",          # Category for grouping
    prefix="/",                # Per-command prefix override
    owner_only=True,           # Owner only
    admin_only=False,          # Chat admins only
    private_only=False,        # Private chat only
    group_only=False,          # Groups only
    reply_only=False,          # Requires reply
    media_only=False,          # Requires media
    text_only=False,           # Requires text
)
async def download(ctx: Context):
    ...
```

## Context API

### Properties
```python
ctx.user          # User — sender
ctx.chat          # Chat — chat
ctx.message_id    # int — message ID
ctx.command       # str — command name
ctx.args          # List[str] — arguments
ctx.arg           # str — arguments as string
ctx.has_args      # bool — has arguments?
ctx.is_reply      # bool — is reply?
ctx.is_private    # bool — private chat?
ctx.text          # str — message text
ctx.platform      # str — "pyrogram"/"aiogram"/"telebot"
ctx.raw           # Any — original Message
ctx.client        # Any — original Client
```

### Methods
```python
await ctx.reply(text)              # Reply
await ctx.edit(text)               # Edit
await ctx.delete()                 # Delete
await ctx.get_reply()              # Get reply message
await ctx.download_media()         # Download media
```

### User
```python
ctx.user.id            # int
ctx.user.username      # Optional[str]
ctx.user.first_name    # Optional[str]
ctx.user.last_name     # Optional[str]
ctx.user.full_name     # str
ctx.user.mention       # str — "@user" or "[Name](tg://user?id=)"
ctx.user.html_mention  # str — HTML version
ctx.user.is_bot        # bool
ctx.user.is_premium    # bool
```

### Chat
```python
ctx.chat.id            # int
ctx.chat.type          # str — "private"/"group"/"supergroup"/"channel"
ctx.chat.title         # Optional[str]
ctx.chat.username      # Optional[str]
ctx.chat.is_private    # bool
ctx.chat.is_group      # bool
ctx.chat.is_channel    # bool
ctx.chat.link          # Optional[str]
```

## Module Structure

```python
# mymodule.py
"""
#name: My Module
#description: Module description
#author: deadboizxc
#version: 1.0.0
#requires: aiohttp, pillow
"""

from zsys.modules import command, Context, modules_help

@command("cmd1", description="Command 1", category="utils")
async def cmd1(ctx: Context):
    await ctx.reply("Done!")

@command("cmd2", aliases=["c2"], reply_only=True)
async def cmd2(ctx: Context):
    reply = await ctx.get_reply()
    await ctx.edit(f"Reply from: {reply.from_user.first_name}")

modules_help["mymodule"] = {
    "cmd1": "Description",
    "cmd2": "Requires reply",
}
```

## Migration from @Client.on_message

**Before (platform-specific):**
```python
from pyrogram import Client, filters
from pyrogram.types import Message

@Client.on_message(filters.command("say", ".") & filters.me)
async def say(client: Client, message: Message):
    text = message.text.split(maxsplit=1)[1]
    await message.edit(f"<code>{text}</code>")
```

**After (unified):**
```python
from zsys.modules import command, Context

@command("say", aliases=["s"], text_only=True)
async def say(ctx: Context):
    await ctx.edit(f"<code>{ctx.arg}</code>", parse_mode="html")
```

## Hot Reload

```python
from zsys.modules import start_watcher, stop_watcher

watcher = await start_watcher(client, ["modules", "custom_modules"])
await stop_watcher()
```

On file change in `modules/` or `custom_modules/`:
1. Watcher detects the change
2. Old handlers/commands are unloaded
3. Module is reloaded
4. New handlers/commands are registered

**Requires:** `pip install watchfiles`

## Isolated Router

```python
from zsys.modules import Router

my_router = Router("my_app")

@my_router.command("test")
async def test(ctx):
    await ctx.reply("Test!")

my_router.attach_pyrogram(client, prefix="!")
```

---

---

# Единая система модулей zsys

Пишите модули один раз — работают везде: Pyrogram, aiogram, telebot.

## Быстрый старт

```python
from zsys.modules import command, Context, modules_help

@command("hello", description="Приветствие")
async def hello(ctx: Context):
    await ctx.reply(f"Привет, {ctx.user.first_name}!")

modules_help["greet"] = {"hello": "Отправляет приветствие"}
```

## API декоратора @command

```python
@command(
    name="download",           # Имя команды (обязательно)
    aliases=["dl", "d"],       # Альтернативные имена
    description="Download",    # Описание для help
    usage="<url>",             # Пример использования
    category="media",          # Категория для группировки
    prefix="/",                # Per-command prefix override
    owner_only=True,           # Только владелец
    admin_only=False,          # Только админы чата
    private_only=False,        # Только в личке
    group_only=False,          # Только в группах
    reply_only=False,          # Требует реплай
    media_only=False,          # Требует медиа
    text_only=False,           # Требует текст
)
async def download(ctx: Context):
    ...
```

## Context API

### Свойства
```python
ctx.user          # User — отправитель
ctx.chat          # Chat — чат
ctx.message_id    # int — ID сообщения
ctx.command       # str — имя команды
ctx.args          # List[str] — аргументы
ctx.arg           # str — аргументы строкой
ctx.has_args      # bool — есть аргументы?
ctx.is_reply      # bool — это реплай?
ctx.is_private    # bool — личный чат?
ctx.text          # str — текст сообщения
ctx.platform      # str — "pyrogram"/"aiogram"/"telebot"
ctx.raw           # Any — оригинальный Message
ctx.client        # Any — оригинальный Client
```

### Методы
```python
await ctx.reply(text)              # Ответить
await ctx.edit(text)               # Редактировать
await ctx.delete()                 # Удалить
await ctx.get_reply()              # Получить сообщение-реплай
await ctx.download_media()         # Скачать медиа
```

### User
```python
ctx.user.id            # int
ctx.user.username      # Optional[str]
ctx.user.first_name    # Optional[str]
ctx.user.full_name     # str
ctx.user.mention       # str — "@user" или "[Name](tg://user?id=)"
ctx.user.is_bot        # bool
ctx.user.is_premium    # bool
```

### Chat
```python
ctx.chat.id            # int
ctx.chat.type          # str — "private"/"group"/"supergroup"/"channel"
ctx.chat.title         # Optional[str]
ctx.chat.is_private    # bool
ctx.chat.is_group      # bool
ctx.chat.link          # Optional[str]
```

## Структура модуля

```python
# mymodule.py
"""
#name: My Module
#description: Описание модуля
#author: deadboizxc
#version: 1.0.0
"""

from zsys.modules import command, Context, modules_help

@command("cmd1", description="Команда 1", category="utils")
async def cmd1(ctx: Context):
    await ctx.reply("Готово!")

modules_help["mymodule"] = {"cmd1": "Описание"}
```

## Миграция с @Client.on_message

**До (platform-specific):**
```python
@Client.on_message(filters.command("say", ".") & filters.me)
async def say(client, message):
    text = message.text.split(maxsplit=1)[1]
    await message.edit(f"<code>{text}</code>")
```

**После (unified):**
```python
@command("say", aliases=["s"], text_only=True)
async def say(ctx: Context):
    await ctx.edit(f"<code>{ctx.arg}</code>", parse_mode="html")
```

## Hot Reload

```python
from zsys.modules import start_watcher, stop_watcher

watcher = await start_watcher(client, ["modules", "custom_modules"])
await stop_watcher()
```

**Требуется:** `pip install watchfiles`

## Изолированный роутер

```python
from zsys.modules import Router

my_router = Router("my_app")

@my_router.command("test")
async def test(ctx):
    await ctx.reply("Test!")

my_router.attach_pyrogram(client, prefix="!")
```
