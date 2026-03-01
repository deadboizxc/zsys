"""
BaseConfig - Universal configuration base class.

All ZSYS configurations should inherit from this class.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field
from pathlib import Path
import os


class BaseConfig(BaseModel):
    """
    Universal base configuration for all ZSYS projects.
    
    Features:
    - Type-safe configuration with Pydantic
    - Automatic validation
    - Environment variable support
    - .env file loading
    
    Usage:
        class MyBotConfig(BaseConfig):
            token: str
            api_id: int
            
            class Config:
                env_prefix = "BOT_"
        
        config = MyBotConfig()
        # Reads from: BOT_TOKEN, BOT_API_ID environment variables
    """
    
    # === Common fields ===
    
    app_name: str = Field(
        default="ZSYS",
        description="Application name"
    )
    
    debug: bool = Field(
        default=False,
        description="Debug mode"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
    
    work_dir: Path = Field(
        default_factory=lambda: Path.cwd(),
        description="Working directory"
    )
    
    class Config:
        """Pydantic configuration."""
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"
        validate_assignment = True
        arbitrary_types_allowed = True
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "BaseConfig":
        """
        Load configuration from environment variables.
        
        Args:
            env_file: Path to .env file (optional)
        """
        if env_file and os.path.exists(env_file):
            return cls(_env_file=env_file)
        return cls()
