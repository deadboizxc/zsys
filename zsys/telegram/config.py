"""TdlibConfig — configuration for libtg-based Telegram client."""
# RU: Конфигурация для TDLib-клиента (libtg).

from __future__ import annotations

from typing import Optional

from pydantic import Field

from zsys.core.config import BaseConfig


class TdlibConfig(BaseConfig):
    """Configuration for TdlibClient (userbot or bot via libtg / TDLib).

    Attributes:
        api_id: Telegram API ID from my.telegram.org.
        api_hash: Telegram API hash.
        session_dir: Directory to store session data. Default: ".".
        session_name: Session file name without extension. Default: "session".
        bot_token: Bot token from @BotFather. If set, runs as a bot.
        phone: Phone number in international format. If set, skips interactive prompt.
        device_model: Device model string reported to Telegram.
        system_version: OS version string reported to Telegram.
        app_version: App version string reported to Telegram.
        lang_code: IETF language tag. Default: "en".
        use_test_dc: Connect to Telegram test servers. Default: False.
        log_verbosity: TDLib log verbosity (0=errors only, 5=all). Default: 0.
        prefix: Command prefix for zsys.modules router. Default: ".".
        core_modules_dir: Directory for built-in modules.
        custom_modules_dir: Directory for user-defined modules.
        auto_load_modules: Load modules on start. Default: True.

    Note:
        All fields can be overridden via TDLIB_* env variables.

    Example::

        cfg = TdlibConfig(api_id=123456, api_hash="abc123def456")
        client = TdlibClient(cfg)
    """

    # RU: Конфигурация libtg клиента. Все поля переопределяются через TDLIB_* env.

    # Credentials
    api_id: int = Field(description="Telegram API ID")
    api_hash: str = Field(description="Telegram API hash")
    session_dir: str = Field(default=".", description="Папка сессии")
    session_name: str = Field(default="session", description="Имя сессии")
    bot_token: Optional[str] = Field(default=None, description="Bot token")
    phone: Optional[str] = Field(default=None, description="Номер телефона")

    # App identity
    device_model: str = Field(default="Desktop")
    system_version: str = Field(default="Linux")
    app_version: str = Field(default="1.0.0")
    lang_code: str = Field(default="en")

    # TDLib settings
    use_test_dc: bool = Field(default=False)
    log_verbosity: int = Field(default=0)

    # zsys.modules
    prefix: str = Field(default=".")
    core_modules_dir: str = Field(default="modules")
    custom_modules_dir: str = Field(default="custom_modules")
    auto_load_modules: bool = Field(default=True)

    class Config:
        # RU: Префикс переменных окружения для TDLib клиента.
        env_prefix = "TDLIB_"


__all__ = ["TdlibConfig"]
