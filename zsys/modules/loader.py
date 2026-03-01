# -*- coding: utf-8 -*-
"""Module loader for zsys core.

Provides utilities for loading and managing Python modules dynamically.
"""

import sys
import os
import importlib
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from types import ModuleType
from dataclasses import dataclass, field
from functools import lru_cache

try:
    from zsys._core import parse_meta_comments as _c_parse_meta_comments, C_AVAILABLE as _C
except ImportError:
    _C = False


@dataclass
class ModuleInfo:
    """Information about a loaded module."""
    name: str
    path: Path
    module: Optional[ModuleType] = None
    enabled: bool = True
    loaded: bool = False
    error: Optional[str] = None
    meta: Dict[str, str] = field(default_factory=dict)
    
    @property
    def status(self) -> str:
        """Get module status string."""
        if not self.enabled:
            return "disabled"
        if self.error:
            return "error"
        if self.loaded:
            return "loaded"
        return "pending"


class ModuleLoader:
    """Generic module loader for dynamic module management.
    
    Example:
        loader = ModuleLoader(Path("./modules"))
        modules = loader.discover()
        for name in modules:
            loader.load(name)
    """
    
    def __init__(
        self,
        base_path: Path,
        prefix: str = "",
        on_load: Optional[Callable[[ModuleInfo], None]] = None,
        on_error: Optional[Callable[[ModuleInfo, Exception], None]] = None
    ):
        """Initialize module loader.
        
        Args:
            base_path: Base directory for modules.
            prefix: Module import prefix (e.g., "custom_modules").
            on_load: Callback when module loads successfully.
            on_error: Callback when module fails to load.
        """
        self.base_path = Path(base_path)
        self.prefix = prefix
        self.on_load = on_load
        self.on_error = on_error
        self._modules: Dict[str, ModuleInfo] = {}
        self._cache: Dict[str, ModuleType] = {}
    
    def discover(self, pattern: str = "*.py") -> List[str]:
        """Discover available modules in base path.
        
        Args:
            pattern: Glob pattern for module files.
        
        Returns:
            List of module names.
        """
        if not self.base_path.exists():
            return []
        
        modules = [
            path.stem
            for path in self.base_path.glob(pattern)
            if path.is_file() and not path.name.startswith("_")
        ]
        
        return sorted(modules)
    
    def is_enabled(self, name: str) -> bool:
        """Check if module is enabled via environment variable.
        
        Args:
            name: Module name.
        
        Returns:
            True if enabled (default), False if explicitly disabled.
        """
        env_var = f"{name.upper()}_ENABLED"
        return os.getenv(env_var, "true").strip().lower() in ("1", "true", "yes", "on")
    
    def get_path(self, name: str) -> Path:
        """Get full path to module file.
        
        Args:
            name: Module name.
        
        Returns:
            Path to module file.
        """
        return self.base_path / f"{name}.py"
    
    def load(self, name: str, force: bool = False) -> Optional[ModuleInfo]:
        """Load a module by name.
        
        Args:
            name: Module name.
            force: Force reload even if cached.
        
        Returns:
            ModuleInfo on success, None on failure.
        """
        # Check cache
        if name in self._modules and not force:
            info = self._modules[name]
            if info.loaded:
                return info
        
        # Create module info
        module_path = self.get_path(name)
        info = ModuleInfo(
            name=name,
            path=module_path,
            enabled=self.is_enabled(name)
        )
        
        if not info.enabled:
            self._modules[name] = info
            return info
        
        if not module_path.exists():
            info.error = f"Module file not found: {module_path}"
            self._modules[name] = info
            return info
        
        # Load module
        try:
            # Add base path to sys.path if needed
            base_str = str(self.base_path)
            if base_str not in sys.path:
                sys.path.insert(0, base_str)
            
            # Import module
            import_name = f"{self.prefix}.{name}" if self.prefix else name
            
            if import_name in sys.modules and force:
                del sys.modules[import_name]
            
            module = importlib.import_module(import_name)
            
            info.module = module
            info.loaded = True
            info.meta = self._parse_meta(module_path)
            
            self._modules[name] = info
            self._cache[name] = module
            
            if self.on_load:
                self.on_load(info)
            
            return info
            
        except Exception as e:
            info.error = f"{type(e).__name__}: {str(e)}"
            info.loaded = False
            self._modules[name] = info
            
            if self.on_error:
                self.on_error(info, e)
            
            return info
    
    def unload(self, name: str) -> bool:
        """Unload a module.
        
        Args:
            name: Module name.
        
        Returns:
            True if unloaded successfully.
        """
        if name in self._modules:
            info = self._modules[name]
            
            import_name = f"{self.prefix}.{name}" if self.prefix else name
            if import_name in sys.modules:
                del sys.modules[import_name]
            
            if name in self._cache:
                del self._cache[name]
            
            info.loaded = False
            info.module = None
            return True
        
        return False
    
    def get(self, name: str) -> Optional[ModuleInfo]:
        """Get module info by name.
        
        Args:
            name: Module name.
        
        Returns:
            ModuleInfo or None if not found.
        """
        return self._modules.get(name)
    
    def get_all(self) -> Dict[str, ModuleInfo]:
        """Get all loaded modules.
        
        Returns:
            Dictionary of module names to ModuleInfo.
        """
        return self._modules.copy()
    
    def load_all(self) -> List[ModuleInfo]:
        """Discover and load all modules.
        
        Returns:
            List of ModuleInfo for all modules.
        """
        names = self.discover()
        results = []
        
        for name in names:
            info = self.load(name)
            if info:
                results.append(info)
        
        return results
    
    @lru_cache(maxsize=256)
    def _parse_meta(self, module_path: Path) -> Dict[str, str]:
        """Parse module metadata from comments."""
        try:
            content = module_path.read_text(encoding="utf-8")
            if _C:
                return _c_parse_meta_comments(content)
            meta = {}
            for line in content.split("\n")[:50]:
                line = line.strip()
                if line.startswith("# @"):
                    parts = line[3:].split(" ", 1)
                    if len(parts) == 2:
                        meta[parts[0].lower()] = parts[1].strip()
            return meta
        except Exception:
            return {}
