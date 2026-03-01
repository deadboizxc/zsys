# -*- coding: utf-8 -*-
"""
Hot reload watcher for zsys modules.

Auto-reloads modules when files change, similar to FastAPI/uvicorn --reload.

Usage:
    from zsys.modules.watcher import ModuleWatcher
    
    watcher = ModuleWatcher(client, ["modules", "custom_modules"])
    await watcher.start()
    
    # ... later
    await watcher.stop()
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Set, Optional, Callable, TYPE_CHECKING
from functools import partial

if TYPE_CHECKING:
    from pyrogram import Client

try:
    from watchfiles import awatch, Change
    WATCHFILES_AVAILABLE = True
except ImportError:
    WATCHFILES_AVAILABLE = False

from zsys.core.logging import get_logger

_log = get_logger(__name__)


class ModuleWatcher:
    """
    File watcher for automatic module reloading.
    
    Watches module directories for changes and automatically reloads
    modified modules without requiring manual .reload command.
    
    Features:
    - Debouncing (waits for file to stabilize before reload)
    - Ignores __pycache__ and .pyc files
    - Supports multiple directories
    - Thread-safe
    
    Example:
        watcher = ModuleWatcher(client, ["modules", "custom_modules"])
        await watcher.start()
    """
    
    def __init__(
        self,
        client: "Client",
        directories: List[str],
        debounce_ms: int = 500,
        reload_callback: Optional[Callable] = None,
    ):
        """
        Initialize module watcher.
        
        Args:
            client: Pyrogram client for module reloading
            directories: List of directories to watch
            debounce_ms: Debounce time in milliseconds
            reload_callback: Optional callback after reload (module_name, success)
        """
        self.client = client
        self.directories = [Path(d).resolve() for d in directories]
        self.debounce = debounce_ms / 1000.0
        self.reload_callback = reload_callback
        
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._pending_reloads: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        
    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()
    
    async def start(self) -> None:
        """Start watching for file changes."""
        if not WATCHFILES_AVAILABLE:
            _log.warning("watchfiles not installed. Run: pip install watchfiles")
            return
        
        if self.is_running:
            return
        
        self._stop_event.clear()
        self._task = asyncio.create_task(self._watch_loop())
        _log.info(f"Hot reload watcher started for: {[str(d) for d in self.directories]}")
    
    async def stop(self) -> None:
        """Stop watching."""
        if not self.is_running:
            return
        
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        _log.info("Hot reload watcher stopped")
    
    async def _watch_loop(self) -> None:
        """Main watch loop."""
        try:
            # Filter directories that exist
            watch_paths = [d for d in self.directories if d.exists()]
            if not watch_paths:
                _log.warning("No watch directories found")
                return
            
            async for changes in awatch(
                *watch_paths,
                stop_event=self._stop_event,
                debounce=int(self.debounce * 1000),
                rust_timeout=1000,
            ):
                await self._handle_changes(changes)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            _log.error(f"Watcher error: {e}")
    
    async def _handle_changes(self, changes: Set) -> None:
        """Handle file change events."""
        modules_to_reload: Set[str] = set()
        
        for change_type, path_str in changes:
            path = Path(path_str)
            
            # Skip non-Python files
            if path.suffix != ".py":
                continue
            
            # Skip __pycache__
            if "__pycache__" in str(path):
                continue
            
            # Skip __init__.py 
            if path.name == "__init__.py":
                continue
            
            module_name = path.stem
            
            # Determine if it's a create, modify or delete
            if change_type == Change.deleted:
                _log.info(f"Module deleted: {module_name}")
                # Unload the module
                await self._unload_module(module_name)
            else:
                # Added or modified
                modules_to_reload.add(module_name)
        
        # Reload changed modules
        for module_name in modules_to_reload:
            await self._reload_module(module_name)
    
    async def _reload_module(self, module_name: str) -> bool:
        """Reload a single module."""
        async with self._lock:
            try:
                from zsys.telegram.pyrogram.modules import reload_modules, get_module_path
                
                # Check if core or custom module
                core_path = get_module_path(module_name, core=True)
                custom_path = get_module_path(module_name, core=False)
                
                is_core = core_path.exists()
                
                _log.info(f"♻️  Hot reloading: {module_name}")
                success = await reload_modules(module_name, self.client, core=is_core)
                
                if self.reload_callback:
                    await self.reload_callback(module_name, success)
                
                return success
                
            except Exception as e:
                _log.error(f"Hot reload failed for {module_name}: {e}")
                return False
    
    async def _unload_module(self, module_name: str) -> bool:
        """Unload a module."""
        async with self._lock:
            try:
                from zsys.telegram.pyrogram.modules import unload_module
                return await unload_module(module_name, self.client)
            except Exception as e:
                _log.error(f"Unload failed for {module_name}: {e}")
                return False


# Singleton watcher instance
_watcher: Optional[ModuleWatcher] = None


def get_watcher() -> Optional[ModuleWatcher]:
    """Get the global watcher instance."""
    return _watcher


async def start_watcher(
    client: "Client",
    directories: List[str],
    debounce_ms: int = 500,
) -> ModuleWatcher:
    """
    Start the global module watcher.
    
    Args:
        client: Pyrogram client
        directories: Directories to watch
        debounce_ms: Debounce time
        
    Returns:
        ModuleWatcher instance
    """
    global _watcher
    
    if _watcher and _watcher.is_running:
        await _watcher.stop()
    
    _watcher = ModuleWatcher(client, directories, debounce_ms)
    await _watcher.start()
    return _watcher


async def stop_watcher() -> None:
    """Stop the global watcher."""
    global _watcher
    if _watcher:
        await _watcher.stop()
        _watcher = None
