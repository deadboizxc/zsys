# ZSYS Examples

Примеры использования ZSYS для различных задач.

## Доступные примеры

### 1. Pyrogram Userbot (`pyrogram_userbot_example.py`)
Userbot с отслеживанием статистики сообщений через SQLite.

```bash
pip install zsys[telegram-pyrogram]
python examples/pyrogram_userbot_example.py
```

### 2. Aiogram Bot (`aiogram_bot_example.py`)
Telegram бот с сессиями в Redis.

```bash
pip install zsys[telegram-aiogram,storage-redis]
python examples/aiogram_bot_example.py
```

### 3. Crypto (`crypto_example.py`)
Примеры шифрования с AES, RSA и ECC.

```bash
pip install zsys[crypto]
python examples/crypto_example.py
```

### 4. Blockchain (`blockchain_example.py`)
Простой блокчейн с proof-of-work.

```bash
pip install zsys
python examples/blockchain_example.py
```

### 5. Storage (`storage_example.py`)
Сравнение различных хранилищ: Memory, SQLite, Redis.

```bash
pip install zsys[storage]
python examples/storage_example.py
```

## Настройка

Для некоторых примеров нужно создать `.env` файл:

```env
# Pyrogram
PYROGRAM_API_ID=12345
PYROGRAM_API_HASH=your_api_hash
PYROGRAM_SESSION_NAME=my_session

# Aiogram
BOT_TOKEN=your_bot_token

# Redis (если используете)
REDIS_URL=redis://localhost:6379/0
```

## Redis

Для примеров с Redis нужен запущенный Redis сервер:

```bash
# Docker
docker run -d -p 6379:6379 redis:alpine

# Или установите локально
# brew install redis  (macOS)
# apt install redis   (Ubuntu)
```
