# zsys.telegram.tdlib — план разработки
# (цель: полная миграция zxc_userbot с Pyrogram на TdlibClient)

## Сборка

```bash
# 1. установить TDLib (один раз, ~15 мин)
make build-tdlib

# 2. собрать libtg.so
make build-telegram

# или одной командой:
make telegram

# установить системно:
make install-telegram
```

Если TDLib уже установлен (`/usr/local/lib/libtdjson.so`):
```bash
make build-telegram   # подхватит автоматически
```


## Что это

`libtg` — C обёртка над TDLib с нулевыми внешними зависимостями (кроме TDLib).
Поверх неё — биндинги для Python (ctypes), Go (cgo), Rust (bindgen).
Цель: единый polyglot Telegram API — как Pyrogram/Telethon, но для всех языков через один C слой.

## Текущий статус

### Готово
- `libtg` C ядро: `tg_client.c`, `tg_auth.c`, `tg_dispatch.c`, `tg_message.c`
- `tg.h` — публичный заголовок: lifecycle, filters, message handlers, actions, self info
- Python `TdlibClient` (ctypes), `TdlibConfig`, `Message`, `binding.py`, `router.py`
- CMakeLists.txt для libtg

### Не реализовано
- `tg_user_t` / `tg_chat_t` accessors в C (объявлены в tg.h, но нет impl)
- `tg_get_user()`, `tg_get_chat()`, `tg_get_history()` — async запросы
- `pin_message`, `mute_chat`, `join_chat`, `leave_chat` и др. действия
- Go биндинги к libtg (есть только к libzsys_core)
- Rust биндинги к libtg (аналогично)
- Python высокоуровневые методы: `get_user()`, `get_chat()`, `get_history()`
- Тесты

## Структура zsys.telegram (текущая)

```
zsys/telegram/
├── __init__.py          # реэкспортирует TdlibClient, TdlibConfig, filters, errors, types
└── tdlib/               # единственная реализация (libtg C wrapper)
    ├── c/               # libtg C исходники + CMakeLists
    ├── client.py        # TdlibClient
    ├── config.py        # TdlibConfig
    ├── filters.py       # Filter класс + стандартные фильтры
    ├── errors.py        # FloodWait, RPCError, ...
    ├── types.py         # Message, User, Chat, ChatMember, File
    ├── binding.py       # ctypes → libtg.so
    └── router.py        # attach_router для zsys.modules
```

Реализации pyrogram / aiogram / telethon / telebot **удалены**.



### Message — чего не хватает
| Поле | Статус |
|------|--------|
| `msg.id`, `msg.chat_id`, `msg.text`, `msg.is_out`, `msg.reply_to_id` | ✅ есть |
| `msg.from_user` → User(id, first_name, is_contact, is_bot) | ❌ нет |
| `msg.chat` → Chat(id, type, title, permissions, linked_chat) | ❌ нет |
| `msg.reply_to_message` → полный Message объект | ❌ нет |
| `msg.media`, `msg.caption`, `msg.sender_chat`, `msg.new_chat_members` | ❌ нет |

### Client — чего не хватает
| Метод | Где используется |
|-------|-----------------|
| `get_chat(id)` | admintool, filters |
| `get_users(id)` | admintool, user_info |
| `get_chat_history(chat_id, limit)` | purge, squotes |
| `get_messages(chat_id, msg_id)` | filters, squotes |
| `ban_chat_member / unban_chat_member` | admintool |
| `promote_chat_member` | admintool |
| `set_chat_permissions` | admintool |
| `download_media(file_id)` | squotes |
| `send_sticker(chat_id, sticker)` | squotes |
| `resolve_peer(id)` | admintool, antipm, clear_notifs (raw API) |

### Ошибки
| Тип | Где используется |
|-----|-----------------|
| `FloodWait` | clear_notifs, spam |
| `MessageDeleteForbidden` | purge |
| `RPCError` | purge, squotes |

### Фильтры
| Фильтр | Статус |
|--------|--------|
| `INCOMING, OUTGOING, PRIVATE, GROUP, CHANNEL, TEXT, ...` | ✅ bitmask в C |
| custom filter через `filters.create(lambda ...)` | ❌ нужна Python система |
| `~filter` (NOT), `filter1 & filter2` (AND), `filter1 \| filter2` (OR) | ❌ нет |
| `filters.mentioned`, `filters.me`, `filters.bot`, `filters.contact` | ❌ нет |

### Raw API (admintool, antipm, clear_notifs)
- Используют `pyrogram.raw.functions` для низкоуровневых TDLib вызовов
- Решение: `client.on_raw(update_type)` + методы через TDLib JSON API ✅ (уже есть `tg_on_raw`)

---

## Этапы

### 1. C ядро — user/chat accessors + async queries
Добавить в tg.h + реализовать:
- `tg_user_t` struct + accessors (id, first_name, last_name, username, is_bot, phone)
- `tg_chat_t` struct + accessors (id, title, type, members_count, username)
- `tg_get_user(client, user_id, cb, ud)` — async через TDLib getUser
- `tg_get_chat(client, chat_id, cb, ud)` — async через TDLib getChat
- `tg_get_history(client, chat_id, from_msg_id, limit, cb, ud)` — async
- `tg_pin_message`, `tg_mute_chat`, `tg_join_chat`, `tg_leave_chat`
- Новый `tg_user.c` + `tg_chat.c`

### 2. Python — высокоуровневые методы
- `TdlibClient.get_user(user_id)` → `User`
- `TdlibClient.get_chat(chat_id)` → `Chat`
- `TdlibClient.get_history(chat_id, limit)` → `list[Message]`
- `TdlibClient.pin_message(chat_id, msg_id)` и др.
- `User`, `Chat` dataclasses в `types.py`
- Обновить `binding.py` (новые сигнатуры)

### 3. Go биндинги к libtg
- `zsys/telegram/tdlib/go/tg.go` — cgo обёртка над tg.h
- `TgClient` struct с методами как в Python
- Пример: `examples/go_userbot/`

### 4. Rust биндинги к libtg
- `zsys/telegram/tdlib/rust/` — bindgen из tg.h
- Safe wrappers: `TgClient`, `Message`, `User`, `Chat`
- Пример: `examples/rust_userbot/`

### 5. Тесты + документация
- Python: pytest с mock libtg.so
- Go: unit тесты
- `docs/tdlib.md` — описание архитектуры libtg
