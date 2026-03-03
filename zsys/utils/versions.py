# -*- coding: utf-8 -*-
"""Version utilities for zsys core.

Provides version management and Python compatibility checking.
Exposes PythonVersion named-tuple and VersionInfo class with frozen constants.
"""
# RU: Утилиты управления версиями для ядра zsys.
# RU: Содержит PythonVersion (именованный кортеж) и VersionInfo с классовыми константами версий.

from sys import version_info
from typing import NamedTuple, Final, Tuple


class PythonVersion(NamedTuple):
    """Structure for storing Python version information.

    Attributes:
        major: Major version number.
        minor: Minor version number.
        micro: Micro (patch) version number.
        releaselevel: Release level string ('alpha', 'beta', 'candidate', 'final').
        serial: Release serial number within the release level.

    Example:
        >>> v = PythonVersion(3, 11, 0, 'final', 0)
        >>> v.formatted
        '3.11.0'
    """

    # RU: Именованный кортеж — описывает компоненты версии Python-интерпретатора.
    major: int
    minor: int
    micro: int
    releaselevel: str
    serial: int

    @property
    def formatted(self) -> str:
        """Return version in 'major.minor.micro' format.

        Returns:
            str: Version string formatted as 'major.minor.micro'.
        """
        # RU: Возвращает краткое представление версии в стандартном формате.
        return f"{self.major}.{self.minor}.{self.micro}"

    @property
    def full_info(self) -> str:
        """Return full version information including release level.

        Returns:
            str: Extended version string such as '3.11.0-final'.
        """
        # RU: Дополняет краткую версию меткой уровня выпуска (alpha/beta/rc/final).
        return f"{self.formatted}-{self.releaselevel}"

    def __str__(self) -> str:
        """Return the formatted version string.

        Returns:
            str: Version formatted as 'major.minor.micro'.
        """
        # RU: Делегирует форматированному представлению для удобного str() и f-строк.
        return self.formatted


class VersionInfo:
    """Class for managing project versions.

    Attributes:
        PYTHON: PythonVersion instance populated from sys.version_info at import time.
        CORE: Core library version string (semver).
        STAGE: Development stage label ('alpha', 'beta', 'stable', etc.).
        PYTHON_COMPATIBLE: Tuple of (major, minor) pairs considered compatible.

    Example:
        >>> VersionInfo.check_compatibility()
        True
        >>> VersionInfo.get_info()['core_version']
        '1.0.0'
    """

    # RU: Хранит версии Python и ядра zsys в виде классовых констант — инстанцирование не нужно.

    # Python version
    PYTHON: Final[PythonVersion] = PythonVersion(
        major=version_info.major,
        minor=version_info.minor,
        micro=version_info.micro,
        releaselevel=version_info.releaselevel,
        serial=version_info.serial,
    )

    # Core version
    CORE: Final[str] = "1.0.0"

    # Development stage
    STAGE: Final[str] = "stable"

    # Compatible Python versions
    PYTHON_COMPATIBLE: Final[Tuple[Tuple[int, int], ...]] = (
        (3, 8),
        (3, 9),
        (3, 10),
        (3, 11),
        (3, 12),
    )

    @classmethod
    def check_compatibility(cls) -> bool:
        """Check Python version compatibility.

        Returns:
            bool: True if the running Python (major, minor) is in PYTHON_COMPATIBLE.

        Raises:
            Nothing — always returns a bool.
        """
        # RU: Проверяет наличие пары (major, minor) текущего Python в списке совместимых версий.
        return (cls.PYTHON.major, cls.PYTHON.minor) in cls.PYTHON_COMPATIBLE

    @classmethod
    def get_info(cls) -> dict:
        """Get version information as a dictionary.

        Returns:
            dict: Mapping with keys ``python_version``, ``core_version``,
                ``stage``, and ``is_compatible``.
        """
        # RU: Собирает сводную информацию о версиях в словарь для сериализации или вывода.
        return {
            "python_version": cls.PYTHON.formatted,
            "core_version": cls.CORE,
            "stage": cls.STAGE,
            "is_compatible": cls.check_compatibility(),
        }


# Aliases for backward compatibility
__python_version__: Final[str] = VersionInfo.PYTHON.formatted
__version__: Final[str] = VersionInfo.CORE
__version_stage__: Final[str] = VersionInfo.STAGE
__core_version__: Final[str] = f"{__version__}_{__version_stage__}"
