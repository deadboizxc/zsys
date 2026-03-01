"""
README for ZSYS Core Logging Module.

This module provides the foundational logging system for the entire ZSYS ecosystem.
"""

# ===== BaseLogger Overview =====

## Architecture

```
zsys.core.logging
│
├── base.py              # BaseLogger class (foundation)
└── __init__.py          # Public API exports

zsys.log
│
├── logger.py            # ColorLogger (extends BaseLogger with colors & rotation)
└── unified.py           # UnifiedLogger (extends BaseLogger with sockets & memory)
```

## Inheritance Hierarchy

```
BaseLogger (core.logging.base)
    ├── ColorLogger (log.logger)
    └── UnifiedLogger (log.unified)
```

# ===== Basic Usage =====

## Simple Logging

```python
from zsys.core.logging import BaseLogger

logger = BaseLogger("myapp")
logger.info("Application started")
logger.error("Error occurred", exc_info=True)
logger.debug("Debug information")
```

## Log Levels

```python
logger = BaseLogger("myapp", level="DEBUG")  # String level
logger = BaseLogger("myapp", level=10)       # Integer level

# Available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
logger.set_level("WARNING")  # Change level dynamically
```

## Custom Format

```python
logger = BaseLogger(
    "myapp",
    format_string="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
```

# ===== Advanced Features =====

## Context Logging

Add contextual information to logs automatically:

```python
logger = BaseLogger("api")

# Temporary context (context manager)
with logger.context(user_id=123, request_id="abc-def"):
    logger.info("Processing request")  # Logs: "Processing request [user_id=123 request_id=abc-def]"
    logger.error("Request failed")     # Logs: "Request failed [user_id=123 request_id=abc-def]"

# Outside context - no extra info
logger.info("New request")  # Logs: "New request"
```

## Bound Loggers

Create logger instances with permanent context:

```python
base_logger = BaseLogger("app")

# Create user-specific logger
user_logger = base_logger.bind(user_id=123, session="xyz")
user_logger.info("User logged in")    # Always includes user_id and session
user_logger.info("User action")       # Always includes user_id and session

# Create request-specific logger
request_logger = base_logger.bind(request_id="req-456")
request_logger.info("Processing")     # Always includes request_id
```

## Child Loggers

Create hierarchical logger structure:

```python
app_logger = BaseLogger("myapp")
db_logger = app_logger.get_child("database")      # Name: "myapp.database"
cache_logger = app_logger.get_child("cache")      # Name: "myapp.cache"

db_logger.info("Connected to database")
cache_logger.info("Cache initialized")
```

## Handler Management

```python
import logging
from logging.handlers import RotatingFileHandler

logger = BaseLogger("app")

# Add file handler
file_handler = RotatingFileHandler(
    "app.log",
    maxBytes=5*1024*1024,  # 5MB
    backupCount=3
)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))
logger.add_handler(file_handler)

# Get all handlers
handlers = logger.get_handlers()

# Remove specific handler
logger.remove_handler(file_handler)

# Clear all handlers
logger.clear_handlers()
```

## State Management

```python
logger = BaseLogger("app")

# Disable logging
logger.disable()
logger.info("This won't be logged")

# Enable logging
logger.enable()
logger.info("This will be logged")

# Check state
if logger.is_disabled():
    print("Logger is disabled")
```

## Level Checking

```python
logger = BaseLogger("app", level="INFO")

# Check if level is enabled
if logger.is_enabled_for("DEBUG"):
    expensive_data = compute_debug_info()
    logger.debug(expensive_data)

# Get current level
level = logger.get_level()  # Returns integer (20 for INFO)
```

# ===== Extended Loggers =====

## ColorLogger (with colors & file rotation)

```python
from zsys.log import ColorLogger

logger = ColorLogger(
    name="myapp",
    log_file="logs/app.log",
    level="debug",
    enable_console=True,
    max_bytes=5 * 1024 * 1024,  # 5 MB
    backup_count=3
)

logger.info("This will be green in console")
logger.error("This will be red in console")
logger.print_color("Custom colored text", color="cyan")
```

## UnifiedLogger (with sockets & memory management)

```python
from zsys.log import UnifiedLogger

logger = UnifiedLogger(
    name="api",
    log_file="logs/api.log",
    log_level="info",
    memory_limit_mb=10,
    socket_ip="127.0.0.1",
    socket_port=9999
)

# Connect to socket for streaming
await logger.connect_socket()

logger.info("This will be logged and streamed via socket")
```

# ===== Best Practices =====

## Module-Level Logger

```python
# mymodule.py
from zsys.core.logging import get_logger

logger = get_logger(__name__)  # Uses module name

def my_function():
    logger.info("Function called")
```

## Structured Logging with Context

```python
logger = BaseLogger("api")

def handle_request(user_id: int, request_id: str):
    # Automatically add context to all logs in this scope
    with logger.context(user_id=user_id, request_id=request_id):
        logger.info("Request received")
        process_request()
        logger.info("Request completed")

def process_request():
    # Context is automatically propagated
    logger.debug("Processing step 1")
    logger.debug("Processing step 2")
```

## Error Logging

```python
logger = BaseLogger("app")

try:
    risky_operation()
except Exception as e:
    logger.exception("Operation failed")  # Automatically logs traceback
    # or
    logger.error("Operation failed: %s", e, exc_info=True)
```

## Performance Optimization

```python
logger = BaseLogger("app", level="INFO")

# Bad: Always computes debug info
logger.debug(f"Debug: {expensive_computation()}")

# Good: Only computes if DEBUG is enabled
if logger.is_enabled_for("DEBUG"):
    logger.debug(f"Debug: {expensive_computation()}")

# Better: Use lazy string formatting
logger.debug("Debug: %s", expensive_computation)  # Only formats if logged
```

# ===== Migration Guide =====

## From Old Logger to BaseLogger

Old code:
```python
from zsys.core.logging import Logger

logger = Logger("myapp", level="INFO")
logger.info("Message")
```

New code (backward compatible):
```python
from zsys.core.logging import Logger  # Now alias for BaseLogger

logger = Logger("myapp", level="INFO")
logger.info("Message")

# Or explicitly use BaseLogger
from zsys.core.logging import BaseLogger

logger = BaseLogger("myapp", level="INFO")
logger.info("Message")
```

All old code continues to work! BaseLogger is 100% backward compatible.

# ===== API Reference =====

## Core Methods

- `debug(message, *args, **kwargs)` - Log debug message
- `info(message, *args, **kwargs)` - Log info message
- `warning(message, *args, **kwargs)` - Log warning message
- `error(message, *args, **kwargs)` - Log error message
- `critical(message, *args, **kwargs)` - Log critical message
- `exception(message, *args, **kwargs)` - Log exception with traceback
- `log(level, message, *args, **kwargs)` - Log with specific level

## Level Management

- `set_level(level)` - Set logging level
- `get_level()` - Get current level
- `is_enabled_for(level)` - Check if level is enabled

## Handler Management

- `add_handler(handler)` - Add handler
- `remove_handler(handler)` - Remove handler
- `clear_handlers()` - Remove all handlers
- `get_handlers()` - Get list of handlers

## Context Management

- `context(**kwargs)` - Context manager for temporary context
- `bind(**kwargs)` - Create new logger with permanent context

## Utilities

- `get_child(suffix)` - Create child logger
- `enable()` - Enable logging
- `disable()` - Disable logging
- `is_disabled()` - Check if disabled

# ===== Testing =====

```python
import pytest
from zsys.core.logging import BaseLogger

def test_basic_logging():
    logger = BaseLogger("test")
    logger.info("Test message")  # Should not raise

def test_context():
    logger = BaseLogger("test")
    with logger.context(key="value"):
        # Check context is added (implementation-specific)
        pass

def test_levels():
    logger = BaseLogger("test", level="WARNING")
    assert logger.get_level() == 30  # WARNING level
    assert not logger.is_enabled_for("DEBUG")
    assert logger.is_enabled_for("ERROR")
```

# ===== Summary =====

BaseLogger provides:
✅ All standard logging methods (debug, info, warning, error, critical, exception)
✅ Context support for structured logging
✅ Bound loggers with permanent context
✅ Child logger creation
✅ Handler management
✅ State management (enable/disable)
✅ Level management and checking
✅ Thread-safe operations
✅ 100% backward compatible with old Logger

Use BaseLogger for:
- Core application logging
- Building custom logger classes (inherit and extend)
- Structured logging with context
- Module-level loggers

Use ColorLogger for:
- Colored console output
- File rotation
- Development environments

Use UnifiedLogger for:
- Production environments with monitoring
- Socket-based log streaming
- Memory-aware log buffering
- API dashboards
