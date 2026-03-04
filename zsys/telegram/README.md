# zsys.telegram

Telegram client for zsys built on TDLib (Telegram Database Library).

## Installation

### 1. Install TDLib

```bash
# Using the install script
./scripts/install_tdlib.sh

# Or manually on Ubuntu/Debian
sudo apt install cmake g++ git gperf libssl-dev zlib1g-dev
git clone --depth 1 --branch v1.8.29 https://github.com/tdlib/td.git
cd td && mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --target install -j$(nproc)
```

### 2. Install zsys with telegram support

```bash
pip install zsys[telegram-tdlib]
```

### 3. Set library path (if not in /usr/local/lib)

```bash
export TDLIB_PATH=/path/to/libtdjson.so
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
