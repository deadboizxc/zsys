# zsys.telegram

Telegram client for zsys built on TDLib (Telegram Database Library).

## Installation

### Quick Start (автоустановка)

```bash
# Установить zsys с telegram модулем
pip install zsys[telegram]

# TDLib скачается автоматически при первом импорте
# Или установить вручную:
zsys-tdlib-install

# Или через Python:
python -m zsys.telegram.tdlib_installer
```

### Manual Installation

```bash
# 1. Зависимости (Ubuntu/Debian)
sudo apt install cmake g++ git gperf libssl-dev zlib1g-dev

# 2. Установить TDLib
./scripts/install_tdlib.sh

# 3. Собрать libtg (C wrapper)
cd c && mkdir build && cd build
cmake .. && make
```

### Environment Variables

```bash
# Указать путь к TDLib (если не в стандартном месте)
export TDLIB_PATH=/path/to/lib

# Пропустить проверку TDLib при импорте
export ZSYS_SKIP_TDLIB_CHECK=1
```

## Usage

```python
from zsys.telegram import TdlibClient, TdlibConfig, filters

config = TdlibConfig(
    api_id=123456,
    api_hash="your_api_hash",
    phone_number="+1234567890",  # or bot_token="..."
)

client = TdlibClient(config)

@client.on_message(filters.private & filters.text)
async def handle_message(message):
    await message.reply(f"Echo: {message.text}")

await client.start()
await client.idle()
```

## Structure

```
zsys/telegram/
├── __init__.py      # Main exports
├── client.py        # TdlibClient (main API)
├── config.py        # TdlibConfig
├── binding.py       # ctypes bindings to libtdjson
├── types.py         # Message, User, Chat, File, etc.
├── filters.py       # Composable filters (&, |, ~)
├── errors.py        # TdlibError, FloodWait, RPCError
├── router.py        # Message routing
├── c/               # Custom C wrapper (libtg)
│   ├── include/tg.h
│   └── src/*.c
└── scripts/
    └── install_tdlib.sh
```

## C Wrapper (libtg)

The `c/` directory contains a custom C wrapper around TDLib that provides:
- Simplified API for common operations
- Async request/response handling
- Type-safe message/user/chat structures

Build with CMake:
```bash
cd c && mkdir build && cd build
cmake .. && make
```
