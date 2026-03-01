# ZSYS Quick Start Guide

## Установка

### Базовая установка (только ядро)
```bash
pip install zsys
```

### С Telegram модулями
```bash
# Pyrogram (для userbots)
pip install zsys[telegram-pyrogram]

# Aiogram (для ботов)
pip install zsys[telegram-aiogram]

# Все Telegram модули
pip install zsys[telegram]
```

### С Storage модулями
```bash
# Redis
pip install zsys[storage-redis]

# PostgreSQL
pip install zsys[storage-postgres]

# Все Storage
pip install zsys[storage]
```

### С Crypto и Blockchain
```bash
# Криптография
pip install zsys[crypto]

# Блокчейн
pip install zsys[blockchain]
```

### Полная установка
```bash
pip install zsys[all]
```

## Быстрый старт

### Pyrogram Userbot

```python
from zsys.telegram.pyrogram.client import PyrogramClient, PyrogramConfig

config = PyrogramConfig(
    api_id=12345,
    api_hash="your_api_hash",
    session_name="my_session"
)

client = PyrogramClient(config)

@client.on_message()
async def handler(client, message):
    if message.text == "/hello":
        await message.reply("Hello from ZSYS!")

await client.start()
```

### Aiogram Bot

```python
from zsys.telegram.aiogram.bot import AiogramBot, AiogramConfig

config = AiogramConfig(token="YOUR_BOT_TOKEN")
bot = AiogramBot(config)

@bot.command("start")
async def start_handler(message):
    await message.reply("Hello! I'm a ZSYS bot!")

@bot.command("help")
async def help_handler(message):
    await message.reply("Available commands:\n/start - Start bot\n/help - Show this message")

await bot.start()
```

### SQLite Storage

```python
from zsys.storage.sqlite import SQLiteStorage

storage = SQLiteStorage("my_data.db")
await storage.connect()

# Сохранить данные
await storage.set("user:123", {"name": "Alice", "age": 25})

# Получить данные
user = await storage.get("user:123")
print(user)  # {"name": "Alice", "age": 25}

# Проверить существование
exists = await storage.exists("user:123")

# Удалить
await storage.delete("user:123")

await storage.disconnect()
```

### Redis Storage

```python
from zsys.storage.redis import RedisStorage

storage = RedisStorage("redis://localhost:6379/0")
await storage.connect()

# Сохранить с истечением (1 час)
await storage.set("session:abc123", "user_data", expire=3600)

# Получить
session = await storage.get("session:abc123")

# Получить все ключи
keys = await storage.keys("session:*")

await storage.disconnect()
```

### AES Encryption

```python
from zsys.crypto.aes import AESCipher

cipher = AESCipher(key="my_secret_key_12345")

# Зашифровать текст
encrypted = cipher.encrypt_string("Secret message!")

# Расшифровать
decrypted = cipher.decrypt_string(encrypted)
print(decrypted)  # "Secret message!"
```

### Simple Blockchain

```python
from zsys.blockchain.simple_chain import SimpleBlockchain

blockchain = SimpleBlockchain(difficulty=4)

# Добавить блоки
blockchain.add_block({"from": "Alice", "to": "Bob", "amount": 50})
blockchain.add_block({"from": "Bob", "to": "Charlie", "amount": 25})

# Проверить валидность
is_valid = blockchain.validate_chain()
print(f"Chain is valid: {is_valid}")

# Получить баланс
alice_balance = blockchain.get_balance("Alice")
print(f"Alice balance: {alice_balance}")  # -50

bob_balance = blockchain.get_balance("Bob")
print(f"Bob balance: {bob_balance}")  # 25 (50 - 25)
```

### EVM Wallet

```python
from zsys.blockchain.evm_chain import EVMWallet

# Создать новый кошелек
wallet = EVMWallet.generate()
print(f"Address: {wallet.address}")
print(f"Private Key: {wallet.private_key}")

# Получить баланс
balance = wallet.balance
print(f"Balance: {balance} ETH")

# Создать транзакцию
transaction = wallet.create_transaction(
    to="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    amount=0.1  # 0.1 ETH
)

# Отправить транзакцию
tx_hash = await wallet.send_transaction(transaction)
print(f"Transaction hash: {tx_hash}")
```

## Примеры комбинирования модулей

### Userbot + Storage

```python
from zsys.telegram.pyrogram.client import PyrogramClient, PyrogramConfig
from zsys.storage.sqlite import SQLiteStorage

# Настроить клиент и хранилище
config = PyrogramConfig(api_id=12345, api_hash="...", session_name="bot")
client = PyrogramClient(config)
storage = SQLiteStorage("bot_data.db")

await storage.connect()

@client.on_message()
async def message_counter(client, message):
    # Получить счетчик сообщений для пользователя
    key = f"msg_count:{message.from_user.id}"
    count = await storage.get(key) or 0
    
    # Увеличить
    count += 1
    await storage.set(key, count)
    
    # Отправить каждое 10-е сообщение
    if count % 10 == 0:
        await message.reply(f"You've sent {count} messages!")

await client.start()
```

### Bot + Crypto

```python
from zsys.telegram.aiogram.bot import AiogramBot, AiogramConfig
from zsys.crypto.aes import AESCipher

config = AiogramConfig(token="YOUR_TOKEN")
bot = AiogramBot(config)
cipher = AESCipher(key="secret_key_123")

@bot.command("encrypt")
async def encrypt_handler(message):
    text = message.text.replace("/encrypt ", "")
    encrypted = cipher.encrypt_string(text)
    await message.reply(f"Encrypted: {encrypted.hex()}")

@bot.command("decrypt")
async def decrypt_handler(message):
    hex_data = message.text.replace("/decrypt ", "")
    encrypted = bytes.fromhex(hex_data)
    decrypted = cipher.decrypt_string(encrypted)
    await message.reply(f"Decrypted: {decrypted}")

await bot.start()
```

## Переменные окружения

Создайте файл `.env` в корне проекта:

```env
# Pyrogram
PYROGRAM_API_ID=12345
PYROGRAM_API_HASH=your_api_hash
PYROGRAM_SESSION_NAME=my_session

# Aiogram
BOT_TOKEN=your_bot_token

# Redis
REDIS_URL=redis://localhost:6379/0

# App settings
APP_NAME=MyBot
DEBUG=false
LOG_LEVEL=INFO
```

Использование:

```python
from zsys.telegram.pyrogram.client import PyrogramConfig

# Автоматически загрузит из .env
config = PyrogramConfig()
```

## Следующие шаги

- Изучите [полную документацию](README.md)
- Посмотрите примеры в папке `examples/`
- Прочитайте о [архитектуре проекта](STRUCTURE.md)

## Помощь

Если возникли проблемы:
- Проверьте, установлены ли нужные зависимости
- Убедитесь, что используете Python 3.10+
- Создайте issue на GitHub

---

Happy coding! 🚀
