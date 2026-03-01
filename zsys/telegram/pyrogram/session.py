"""
Core Userbot Session Module - Pyrogram session utilities.

Provides:
- Session creation helpers
- Session validation
- Session management utilities
"""

import os
import sys
import signal
from pathlib import Path
from typing import Optional, Dict, Any, Callable, NoReturn

__all__ = [
    'create_session',
    'validate_session',
    'get_session_path',
    'SessionConfig',
]


class SessionConfig:
    """Configuration for Pyrogram session."""
    
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session_name: str = "session",
        workdir: Optional[str] = None,
        device_model: str = "Desktop",
        system_version: str = "1.0",
        app_version: str = "1.0",
    ):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.workdir = workdir or os.getcwd()
        self.device_model = device_model
        self.system_version = system_version
        self.app_version = app_version
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Pyrogram Client kwargs."""
        return {
            'api_id': self.api_id,
            'api_hash': self.api_hash,
            'name': self.session_name,
            'workdir': self.workdir,
            'device_model': self.device_model,
            'system_version': self.system_version,
            'app_version': self.app_version,
        }


def get_session_path(
    session_name: str,
    workdir: Optional[str] = None,
    extension: str = ".session"
) -> Path:
    """
    Get full path to session file.
    
    Args:
        session_name: Session name (without extension)
        workdir: Working directory (default: current directory)
        extension: Session file extension
        
    Returns:
        Path to session file
    """
    workdir = Path(workdir) if workdir else Path.cwd()
    name = session_name.removesuffix(extension)
    return workdir / f"{name}{extension}"


def validate_session(
    session_name: str,
    workdir: Optional[str] = None
) -> bool:
    """
    Check if session file exists and is valid.
    
    Args:
        session_name: Session name
        workdir: Working directory
        
    Returns:
        True if session exists and appears valid
    """
    path = get_session_path(session_name, workdir)
    
    if not path.exists():
        return False
    
    # Check minimum file size (valid session files are typically > 1KB)
    if path.stat().st_size < 100:
        return False
    
    return True


async def create_session(
    config: SessionConfig,
    on_start: Optional[Callable] = None,
    on_success: Optional[Callable] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
    hide_password: bool = True,
) -> bool:
    """
    Create new Pyrogram session.
    
    Args:
        config: Session configuration
        on_start: Callback when session creation starts
        on_success: Callback when session created successfully
        on_error: Callback when error occurs
        hide_password: Hide password input in terminal
        
    Returns:
        True if session created successfully, False otherwise
    """
    try:
        from pyrogram import Client
        from pyrogram.errors import BadRequest, SessionPasswordNeeded
    except ImportError:
        raise ImportError("pyrogram is required for session creation. Install with: pip install pyrogram")
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig: int, frame: Any) -> NoReturn:
        print("\nSession creation cancelled by user.")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        if on_start:
            on_start()
        
        client_kwargs = config.to_dict()
        client_kwargs['hide_password'] = hide_password
        
        async with Client(**client_kwargs) as app:
            await app.start()
            
            if on_success:
                on_success()
            
            return True
            
    except (BadRequest, SessionPasswordNeeded) as e:
        if on_error:
            on_error(e)
        return False
    except Exception as e:
        if on_error:
            on_error(e)
        return False


def prompt_input(
    prompt: str,
    required: bool = False,
    default: Optional[str] = None,
    validator: Optional[Callable[[str], bool]] = None,
    error_msg: str = "Invalid input. Please try again."
) -> str:
    """
    Get user input with validation.
    
    Args:
        prompt: Prompt message
        required: Whether input is required
        default: Default value if empty input
        validator: Validation function
        error_msg: Error message for invalid input
        
    Returns:
        User input or default value
    """
    while True:
        value = input(f"{prompt} ").strip()
        
        if not value and default is not None:
            return default
        
        if required and not value:
            print("This field is required!")
            continue
        
        if validator and value and not validator(value):
            print(error_msg)
            continue
        
        return value


def confirm_action(prompt: str, default: bool = False) -> bool:
    """
    Ask user for confirmation.
    
    Args:
        prompt: Confirmation prompt
        default: Default value if empty input
        
    Returns:
        True if confirmed, False otherwise
    """
    suffix = " [Y/n]" if default else " [y/N]"
    response = input(f"{prompt}{suffix} ").strip().lower()
    
    if not response:
        return default
    
    return response in ('y', 'yes', 'да')
