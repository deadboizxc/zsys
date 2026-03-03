"""
Multi-Client System for Pyrogram/Telethon userbots.

Provides:
- MultiClient for managing multiple bot/userbot clients
- Command registration with decorators
- Message dispatching across clients
- Plugin system support
"""

import asyncio
from typing import Callable, List, Dict, Any, Optional, Union, Tuple

__all__ = [
    "MultiClient",
    "command",
    "MODULE_COMMANDS",
    "ConsoleClient",
]

# Global command registry for module decorators
MODULE_COMMANDS: List[Tuple[List[str], str, Callable]] = []


def command(names: Union[str, List[str]], prefix: str = "/"):
    """
    Decorator for registering module commands.

    Args:
        names: Command name(s) to register (string or list)
        prefix: Command prefix (default: "/")

    Returns:
        Decorated function

    Example:
        @command("help")
        async def help_cmd(client, msg, args):
            await msg.reply("Help message")

        @command(["start", "begin"], prefix=".")
        async def start_cmd(client, msg, args):
            pass
    """
    if isinstance(names, str):
        names = [names]

    def decorator(func: Callable) -> Callable:
        MODULE_COMMANDS.append((names, prefix, func))
        return func

    return decorator


class MultiClient:
    """
    Manager for multiple Pyrogram/Telethon clients.

    Handles message dispatching, command routing, and cross-client actions.

    Example:
        mc = MultiClient()
        mc.add_client(pyrogram_client)
        mc.add_client(telethon_client)
        mc.register_command("ping", ping_handler)
        await mc.start_all()
    """

    def __init__(self, prefixes: List[str] = None):
        """
        Initialize MultiClient.

        Args:
            prefixes: List of command prefixes (default: ["/", "."])
        """
        self.clients: List[Any] = []
        self.handlers: List[Callable] = []
        self.commands: Dict[str, Callable] = {}
        self.prefixes: List[str] = prefixes or ["/", "."]
        self._started: bool = False

    def add_client(self, client: Any) -> None:
        """
        Add a client to the manager.

        Args:
            client: Pyrogram/Telethon client instance
        """
        self.clients.append(client)

        # Register dispatcher if client supports on_message
        if hasattr(client, "on_message"):
            client.on_message(self._dispatch)

    def remove_client(self, client: Any) -> bool:
        """
        Remove a client from the manager.

        Args:
            client: Client to remove

        Returns:
            True if removed, False if not found
        """
        if client in self.clients:
            self.clients.remove(client)
            return True
        return False

    def register_command(self, name: str, func: Callable) -> None:
        """
        Register a command handler.

        Args:
            name: Command name (without prefix)
            func: Handler function (sync or async)
        """
        self.commands[name.lower()] = func

    def register_commands(self, commands: Dict[str, Callable]) -> None:
        """
        Register multiple commands at once.

        Args:
            commands: Dict of {name: handler}
        """
        for name, func in commands.items():
            self.register_command(name, func)

    def load_module_commands(self) -> int:
        """
        Load commands registered via @command decorator.

        Returns:
            Number of commands loaded
        """
        count = 0
        for names, prefix, func in MODULE_COMMANDS:
            for name in names:
                self.commands[name.lower()] = func
                count += 1
        return count

    def _dispatch(self, msg: Any) -> None:
        """
        Dispatch incoming message to appropriate handler.

        Args:
            msg: Message object (dict or Message instance)
        """
        # Extract text from message
        if isinstance(msg, dict):
            text = msg.get("text", "")
        else:
            text = getattr(msg, "text", "") or getattr(msg, "caption", "") or ""

        if not text:
            return

        # Check for command prefix
        for prefix in self.prefixes:
            if text.startswith(prefix):
                command_text = text[len(prefix) :]
                parts = command_text.split(maxsplit=1)

                if not parts:
                    return

                cmd_name = parts[0].lower()
                args = parts[1].split() if len(parts) > 1 else []

                if cmd_name in self.commands:
                    func = self.commands[cmd_name]

                    if asyncio.iscoroutinefunction(func):
                        asyncio.create_task(func(self, msg, args))
                    else:
                        func(self, msg, args)

                break

    async def send_message_all(self, target: Union[int, str], text: str) -> List[Any]:
        """
        Send message from all clients.

        Args:
            target: Chat ID or username
            text: Message text

        Returns:
            List of sent messages
        """
        results = []
        for client in self.clients:
            if hasattr(client, "send_message"):
                try:
                    if asyncio.iscoroutinefunction(client.send_message):
                        msg = await client.send_message(target, text)
                    else:
                        msg = client.send_message(target, text)
                    results.append(msg)
                except Exception as e:
                    results.append(e)
        return results

    async def start_all(self) -> None:
        """Start all clients."""
        for client in self.clients:
            if hasattr(client, "start"):
                if asyncio.iscoroutinefunction(client.start):
                    await client.start()
                else:
                    client.start()
        self._started = True

    async def stop_all(self) -> None:
        """Stop all clients."""
        for client in self.clients:
            if hasattr(client, "stop"):
                if asyncio.iscoroutinefunction(client.stop):
                    await client.stop()
                else:
                    client.stop()
        self._started = False

    @property
    def is_started(self) -> bool:
        """Check if clients are started."""
        return self._started

    def __len__(self) -> int:
        """Return number of clients."""
        return len(self.clients)


class ConsoleClient:
    """
    Simple console-based client for testing.

    Simulates a chat client reading from stdin.

    Example:
        client = ConsoleClient()
        mc = MultiClient()
        mc.add_client(client)
        await client.start()
    """

    def __init__(self, prompt: str = "You: "):
        """
        Initialize console client.

        Args:
            prompt: Input prompt string
        """
        self.handlers: List[Callable] = []
        self.prompt = prompt
        self._running = False

    async def start(self) -> None:
        """Start console input loop."""
        print("Console client started. Type commands with prefix (e.g., /help)")
        self._running = True

        while self._running:
            try:
                # Use asyncio-compatible input
                text = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input(self.prompt)
                )

                msg = {"user": "console", "text": text, "chat_id": 0}

                for handler in self.handlers:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(msg)
                    else:
                        handler(msg)

            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                print(f"Error: {e}")

    async def stop(self) -> None:
        """Stop console client."""
        self._running = False

    async def send_message(self, target: Any, text: str) -> Dict[str, Any]:
        """
        Print message to console.

        Args:
            target: Target (ignored for console)
            text: Message text

        Returns:
            Fake message dict
        """
        print(f"Bot: {text}")
        return {"text": text, "target": target}

    def on_message(self, handler: Callable) -> None:
        """
        Register message handler.

        Args:
            handler: Handler function
        """
        self.handlers.append(handler)
