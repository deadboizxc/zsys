[🇬🇧 English](STRUCTURE.md) | [🇷🇺 Русский](STRUCTURE_RU.md)

# Архитектура и структура ZSYS

## Проект создан согласно требованиям модульной архитектуры

Этот документ описывает архитектуру и структуру проекта ZSYS согласно изначальным требованиям.

## 🎯 Основные принципы

### 1. Core (zsys/core) — Максимальная абстракция

**Ключевое правило**: Core НЕ знает о внешних сервисах и библиотеках.

#### Core включает:
- **Interfaces (Protocol-based)** — абстрактные интерфейсы
- **Base Models** — базовые модели данных
- **Helpers** — конфигурация, логирование, исключения

#### Что НЕ делает core:
- ❌ Не импортирует Telegram-библиотеки (Pyrogram, Aiogram, Telethon)
- ❌ Не импортирует Storage-библиотеки (Redis, PostgreSQL)
- ❌ Не импортирует Crypto-библиотеки (cryptography)
- ❌ Не импортирует Blockchain-библиотеки (web3)

### 2. Modules (zsys-[feature]) — Реализации

Модули наследуют от интерфейсов core и реализуют конкретные методы.

Каждый модуль устанавливается опционально:
```bash
pip install zsys[telegram-pyrogram]
pip install zsys[storage-redis]
pip install zsys[crypto]
```

### 3. Service Registration (опционально)

Можно использовать ServiceRegistry для dependency injection.

## 📂 Структура проекта

```
zsys/
│
├── __init__.py                 # Главный модуль (экспортирует core)
├── pyproject.toml              # Конфигурация проекта и зависимости
├── README.md                   # Документация
├── QUICKSTART.md               # Быстрый старт
├── STRUCTURE.md                # Этот файл
├── LICENSE                     # MIT License
├── .gitignore                  # Git ignore
│
├── core/                       # ⭐ ЯДРО — чистые абстракции
│   ├── __init__.py            # Экспорты всех интерфейсов и моделей
│   │
│   ├── interfaces/            # Protocol-based интерфейсы
│   │   ├── __init__.py       # Экспорты всех интерфейсов
│   │   ├── client.py         # IClient — базовый клиент
│   │   ├── bot.py            # IBot — интерфейс бота
│   │   ├── userbot.py        # IUserBot — интерфейс юзербота
│   │   ├── chat.py           # IChat — интерфейс чата
│   │   ├── storage.py        # IStorage — интерфейс хранилища
│   │   ├── cipher.py         # ICipher — интерфейс шифрования
│   │   ├── blockchain.py     # IBlockchain — интерфейс блокчейна
│   │   └── wallet.py         # IWallet — интерфейс кошелька
│   │
│   ├── models/                # Базовые модели
│   │   ├── __init__.py
│   │   ├── base_user.py      # BaseUser — модель пользователя
│   │   ├── base_chat.py      # BaseChat — модель чата
│   │   ├── base_client.py    # BaseClient — модель клиента
│   │   ├── base_message.py   # BaseMessage — модель сообщения
│   │   ├── base_wallet.py    # BaseWallet — модель кошелька
│   │   └── base_transaction.py # BaseTransaction — модель транзакции
│   │
│   ├── config/                # Конфигурация
│   │   ├── __init__.py
│   │   └── base.py           # BaseConfig — базовая конфигурация
│   │
│   ├── logging/               # Логирование
│   │   └── __init__.py       # Logger — простой логгер
│   │
│   └── exceptions/            # Исключения
│       └── __init__.py       # ZsysError и подклассы
│
├── telegram/                   # 📱 Telegram-модули
│   ├── __init__.py
│   │
│   ├── pyrogram/              # Реализация Pyrogram (userbots)
│   │   ├── __init__.py
│   │   └── client.py         # PyrogramClient: IUserBot
│   │
│   ├── aiogram/               # Реализация Aiogram (bots)
│   │   ├── __init__.py
│   │   └── bot.py            # AiogramBot: IBot
│   │
│   └── telethon/              # Реализация Telethon (userbots)
│       ├── __init__.py
│       └── client.py         # TelethonClient: IUserBot
│
├── storage/                    # 💾 Модули хранилищ
│   ├── __init__.py
│   ├── sqlite.py              # SQLiteStorage: IStorage
│   ├── redis.py               # RedisStorage: IStorage
│   └── memory.py              # MemoryStorage: IStorage
│
├── crypto/                     # 🔐 Crypto-модули
│   ├── __init__.py
│   ├── aes.py                 # AESCipher: ICipher
│   ├── rsa.py                 # RSACipher: ICipher
│   └── ecc.py                 # ECCCipher: ICipher
│
├── blockchain/                 # ⛓️ Blockchain-модули
│   ├── __init__.py
│   ├── simple_chain.py        # SimpleBlockchain: IBlockchain
│   └── evm_chain.py           # EVMChain: IBlockchain
│                              # EVMWallet: IWallet
│
└── examples/                   # 📘 Примеры использования
    ├── pyrogram_userbot_example.py
    ├── aiogram_bot_example.py
    ├── crypto_example.py
    ├── blockchain_example.py
    └── storage_example.py
```

## 🔌 Интерфейсы Core

### IClient
Базовый интерфейс клиента для всех платформ.

```python
from typing import Protocol

class IClient(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def send_message(self, chat_id: int | str, text: str, **kwargs): ...
    @property
    def is_running(self) -> bool: ...
```

### IBot
Интерфейс для обычных ботов (Telegram Bot API, Discord bots).

```python
class IBot(IClient, Protocol):
    def command(self, commands: str | list[str]) -> Callable: ...
    def message_handler(self, **filters) -> Callable: ...
    async def delete_message(self, chat_id: int | str, message_id: int) -> bool: ...
```

### IUserBot
Интерфейс для юзерботов (Pyrogram, Telethon).

```python
class IUserBot(IClient, Protocol):
    def on_message(self, filters=None) -> Callable: ...
    async def edit_message_text(self, chat_id, message_id, text, **kwargs): ...
    async def forward_messages(self, chat_id, from_chat_id, message_ids, **kwargs): ...
    async def download_media(self, message, file_name=None, **kwargs) -> str: ...
```

### IStorage
Интерфейс хранилища (SQLite, Redis, Memory).

```python
class IStorage(Protocol):
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def get(self, key: str) -> Optional[Any]: ...
    async def set(self, key: str, value: Any, expire: int | None = None) -> None: ...
    async def delete(self, key: str) -> bool: ...
    async def exists(self, key: str) -> bool: ...
    async def clear(self) -> None: ...
    async def keys(self, pattern: str = "*") -> list[str]: ...
```

### ICipher
Интерфейс шифрования (AES, RSA, ECC).

```python
class ICipher(Protocol):
    def encrypt(self, data: bytes) -> bytes: ...
    def decrypt(self, data: bytes) -> bytes: ...
    def encrypt_string(self, text: str, encoding: str = "utf-8") -> bytes: ...
    def decrypt_string(self, data: bytes, encoding: str = "utf-8") -> str: ...
```

### IBlockchain
Интерфейс блокчейна.

```python
class IBlockchain(Protocol):
    def add_block(self, data: Any) -> Any: ...
    def validate_chain(self) -> bool: ...
    def get_balance(self, address: str) -> float: ...
    def get_block(self, index: int) -> Optional[Any]: ...
    @property
    def chain(self) -> list[Any]: ...
    @property
    def latest_block(self) -> Any: ...
```

### IWallet
Интерфейс криптокошелька.

```python
class IWallet(Protocol):
    @property
    def address(self) -> str: ...
    @property
    def private_key(self) -> str: ...
    @property
    def balance(self) -> float: ...
    def create_transaction(self, to: str, amount: float, **kwargs) -> Any: ...
    def sign_transaction(self, transaction: Any) -> Any: ...
    async def send_transaction(self, transaction: Any) -> str: ...
    async def get_transaction(self, tx_hash: str) -> Optional[Any]: ...
```

## 📦 Опциональные зависимости

Структура `pyproject.toml`:

```toml
[project.optional-dependencies]
# Telegram
telegram-pyrogram = ["pyrogram>=2.0.0", "tgcrypto>=1.2.0"]
telegram-aiogram = ["aiogram>=3.0.0"]
telegram-telethon = ["telethon>=1.36.0"]
telegram = ["zsys[telegram-pyrogram]", "zsys[telegram-aiogram]", "zsys[telegram-telethon]"]

# Storage
storage-redis = ["redis>=5.0.0"]
storage-postgres = ["asyncpg>=0.29.0", "sqlalchemy>=2.0.0"]
storage = ["zsys[storage-redis]", "zsys[storage-postgres]"]

# Crypto
crypto = ["cryptography>=42.0.0"]

# Blockchain
blockchain = ["web3>=6.15.0", "eth-account>=0.11.0"]

# All features
all = ["zsys[telegram]", "zsys[storage]", "zsys[crypto]", "zsys[blockchain]"]
```

## 🚀 Использование

### Базовая установка (только core)
```bash
pip install zsys
```

Доступны только интерфейсы и модели:
```python
from zsys.core.interfaces import IBot, IStorage
from zsys.core.models import BaseUser, BaseChat
```

### Установка с модулями
```bash
# Telegram
pip install zsys[telegram-pyrogram]

# Storage
pip install zsys[storage-redis]

# Crypto
pip install zsys[crypto]

# Blockchain
pip install zsys[blockchain]

# Всё вместе
pip install zsys[all]
```

### Пример использования

```python
# Импорт интерфейса из core (всегда доступен)
from zsys.core.interfaces import IUserBot

# Импорт реализации (доступен только после установки модуля)
from zsys.telegram.pyrogram.client import PyrogramClient, PyrogramConfig

# Использование
config = PyrogramConfig(api_id=12345, api_hash="...", session_name="bot")
client: IUserBot = PyrogramClient(config)  # Соответствует интерфейсу

@client.on_message()
async def handler(client, message):
    await message.reply("Hello!")

await client.start()
```

## 🎨 Паттерны проектирования

### 1. Protocol-based (структурная типизация)
Вместо ABC (наследование) используем Protocol (duck typing):

```python
# Вместо ABC
class IClient(ABC):
    @abstractmethod
    async def start(self): pass

# Используем Protocol
class IClient(Protocol):
    async def start(self) -> None: ...
```

**Преимущества**:
- Не нужно явное наследование
- Более гибкий duck typing
- Легче писать тесты и моки

### 2. Dependency Injection
Код зависит от интерфейсов, а не от реализаций:

```python
class MyService:
    def __init__(self, storage: IStorage):
        self.storage = storage  # Любая реализация IStorage
    
    async def save_user(self, user: BaseUser):
        await self.storage.set(f"user:{user.id}", user.to_dict())

# Можно использовать любое хранилище
service1 = MyService(storage=SQLiteStorage("data.db"))
service2 = MyService(storage=RedisStorage("redis://..."))
service3 = MyService(storage=MemoryStorage())
```

### 3. Optional Dependencies
Модули проверяют доступность библиотек:

```python
try:
    from pyrogram import Client
    PYROGRAM_AVAILABLE = True
except ImportError:
    PYROGRAM_AVAILABLE = False
    Client = None

class PyrogramClient(IUserBot):
    def __init__(self, config):
        if not PYROGRAM_AVAILABLE:
            raise ClientError("Install: pip install zsys[telegram-pyrogram]")
```

## ✅ Требования выполнены

### ✅ 1. Core (максимальная абстракция)
- ✅ Core не знает о внешних сервисах
- ✅ Только интерфейсы (Protocol-based)
- ✅ Базовые модели (dataclasses)
- ✅ Хелперы (Config, Logger, Exceptions)

### ✅ 2. Modules (zsys-[feature])
- ✅ telegram: pyrogram, aiogram, telethon
- ✅ storage: sqlite, redis, memory
- ✅ crypto: aes, rsa, ecc
- ✅ blockchain: simple_chain, evm_chain

### ✅ 3. Опциональные зависимости
- ✅ Каждый модуль устанавливается отдельно
- ✅ pip install zsys[telegram-pyrogram]
- ✅ pip install zsys[storage,crypto]

### ✅ 4. Структура проекта
- ✅ Соответствует требованиям
- ✅ Модульная архитектура
- ✅ Чистые абстракции в core

## 📚 Дополнительная информация

- [README.md](README.md) — Основная документация
- [QUICKSTART.md](QUICKSTART.md) — Быстрый старт
- [examples/](examples/) — Примеры использования

---

Архитектура создана согласно требованиям для максимальной модульности и гибкости.
