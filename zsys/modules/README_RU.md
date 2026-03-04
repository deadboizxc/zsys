[🇬🇧 English](README.md) | [🇷🇺 Русский](README_RU.md)

# Единая система модулей zsys

Пишите модули один раз — они работают везде: Pyrogram, aiogram, telebot.

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
    prefix="/",                # Переопределение префикса для команды
    owner_only=True,           # Только владелец
    admin_only=False,          # Только администраторы чата
    private_only=False,        # Только в личке
    group_only=False,          # Только в группах
    reply_only=False,          # Требует ответа на сообщение
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
ctx.is_reply      # bool — это ответ на сообщение?
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
await ctx.get_reply()              # Получить сообщение-ответ
await ctx.download_media()         # Скачать медиа
```

### User
```python
ctx.user.id            # int
ctx.user.username      # Optional[str]
ctx.user.first_name    # Optional[str]
ctx.user.last_name     # Optional[str]
ctx.user.full_name     # str
ctx.user.mention       # str — "@user" или "[Name](tg://user?id=)"
ctx.user.html_mention  # str — HTML-версия
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

## Структура модуля

```python
# mymodule.py
"""
#name: My Module
#description: Описание модуля
#author: deadboizxc
#version: 1.0.0
#requires: aiohttp, pillow
"""

from zsys.modules import command, Context, modules_help

@command("cmd1", description="Команда 1", category="utils")
async def cmd1(ctx: Context):
    await ctx.reply("Готово!")

@command("cmd2", aliases=["c2"], reply_only=True)
async def cmd2(ctx: Context):
    reply = await ctx.get_reply()
    await ctx.edit(f"Ответ от: {reply.from_user.first_name}")

modules_help["mymodule"] = {
    "cmd1": "Описание",
    "cmd2": "Требует ответа на сообщение",
}
```

## Миграция с @Client.on_message

**До (привязка к платформе):**
```python
from pyrogram import Client, filters
from pyrogram.types import Message

@Client.on_message(filters.command("say", ".") & filters.me)
async def say(client: Client, message: Message):
    text = message.text.split(maxsplit=1)[1]
    await message.edit(f"<code>{text}</code>")
```

**После (унифицированный):**
```python
from zsys.modules import command, Context

@command("say", aliases=["s"], text_only=True)
async def say(ctx: Context):
    await ctx.edit(f"<code>{ctx.arg}</code>", parse_mode="html")
```

## Горячая перезагрузка

```python
from zsys.modules import start_watcher, stop_watcher

watcher = await start_watcher(client, ["modules", "custom_modules"])
await stop_watcher()
```

При изменении файла в `modules/` или `custom_modules/`:
1. Наблюдатель обнаруживает изменение
2. Старые обработчики/команды выгружаются
3. Модуль перезагружается
4. Новые обработчики/команды регистрируются

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
