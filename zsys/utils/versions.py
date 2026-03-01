# -*- coding: utf-8 -*-
"""Version utilities for zsys core.

Provides version management and Python compatibility checking.
"""

from sys import version_info
from typing import NamedTuple, Final, Tuple


class PythonVersion(NamedTuple):
    """Structure for storing Python version information."""
    major: int
    minor: int
    micro: int
    releaselevel: str
    serial: int

    @property
    def formatted(self) -> str:
        """Return version in 'major.minor.micro' format."""
        return f"{self.major}.{self.minor}.{self.micro}"

    @property
    def full_info(self) -> str:
        """Return full version information."""
        return f"{self.formatted}-{self.releaselevel}"
    
    def __str__(self) -> str:
        return self.formatted


class VersionInfo:
    """Class for managing project versions."""
    
    # Python version
    PYTHON: Final[PythonVersion] = PythonVersion(
        major=version_info.major,
        minor=version_info.minor,
        micro=version_info.micro,
        releaselevel=version_info.releaselevel,
        serial=version_info.serial
    )
    
    # Core version
    CORE: Final[str] = "1.0.0"
    
    # Development stage
    STAGE: Final[str] = "stable"
    
    # Compatible Python versions
    PYTHON_COMPATIBLE: Final[Tuple[Tuple[int, int], ...]] = (
        (3, 8), (3, 9), (3, 10), (3, 11), (3, 12)
    )

    @classmethod
    def check_compatibility(cls) -> bool:
        """Check Python version compatibility.
        
        Returns:
            bool: True if Python version is compatible.
        """
        return (cls.PYTHON.major, cls.PYTHON.minor) in cls.PYTHON_COMPATIBLE
    
    @classmethod
    def get_info(cls) -> dict:
        """Get version information as dictionary.
        
        Returns:
            dict: Version information.
        """
        return {
            "python_version": cls.PYTHON.formatted,
            "core_version": cls.CORE,
            "stage": cls.STAGE,
            "is_compatible": cls.check_compatibility()
        }


# Aliases for backward compatibility
__python_version__: Final[str] = VersionInfo.PYTHON.formatted
__version__: Final[str] = VersionInfo.CORE
__version_stage__: Final[str] = VersionInfo.STAGE
__core_version__: Final[str] = f"{__version__}_{__version_stage__}"
