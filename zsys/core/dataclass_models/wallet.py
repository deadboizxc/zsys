"""BaseWallet dataclass — platform-agnostic cryptocurrency wallet model.

Represents a cryptocurrency wallet in memory without ORM dependencies.
For database persistence use ``zsys.data.orm.wallet.BaseWallet`` instead.
"""
# RU: Датакласс BaseWallet — платформо-независимая модель криптокошелька.
# RU: Для сохранения в БД используйте zsys.data.orm.wallet.BaseWallet.

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class BaseWallet:
    """Platform-agnostic cryptocurrency wallet model.

    Represents a wallet in memory for any blockchain (Bitcoin, Ethereum,
    EVM-compatible chains).  Can be extended by blockchain-specific
    subclasses (BitcoinWallet, EthereumWallet, SimpleChainWallet).

    Warning:
        ``private_key`` must be stored and transmitted securely.
        Never log or expose it over untrusted channels.

    Attributes:
        address: Public wallet address derived from the key pair.
        private_key: Raw private key — handle with extreme care.
        balance: Current wallet balance in the native currency units.
        currency: Ticker symbol of the native currency (e.g. ``"ETH"``).
        label: Optional human-friendly label for this wallet.
        is_watch_only: If True, private key access is disabled (read-only tracking).
        created_at: Timestamp when this wallet record was created.
        last_updated: Timestamp when the balance was last refreshed.
    """
    # RU: Платформо-независимая модель криптовалютного кошелька.

    address: str
    """Wallet address (public key)"""

    private_key: str
    """Private key (handle with care!)"""

    balance: float = 0.0
    """Current wallet balance"""

    currency: str = "BTC"
    """Currency type (BTC, ETH, etc.)"""

    label: Optional[str] = None
    """Wallet label/name"""

    is_watch_only: bool = False
    """Whether this is a watch-only wallet (no private key access)"""

    created_at: datetime = field(default_factory=datetime.now)
    """When this wallet was created"""

    last_updated: datetime = field(default_factory=datetime.now)
    """When balance was last updated"""

    @property
    def display_address(self) -> str:
        """Truncated address for safe display in UIs and logs.

        Returns:
            First 8 + ``"..."`` + last 6 characters for long addresses,
            or the full address for short ones.
        """
        # RU: Сокращённый адрес для отображения в UI и логах.
        if len(self.address) > 20:
            return f"{self.address[:8]}...{self.address[-6:]}"
        return self.address

    @property
    def has_balance(self) -> bool:
        """True if the wallet holds a non-zero balance.

        Returns:
            True when ``balance > 0``.
        """
        # RU: True, если баланс кошелька больше нуля.
        return self.balance > 0

    def to_dict(self, include_private_key: bool = False) -> dict:
        """Serialise the wallet to a plain dictionary.

        Args:
            include_private_key: If True and the wallet is not watch-only,
                include the ``private_key`` field in the output.
                Defaults to False for safety.

        Returns:
            Dictionary with wallet fields; timestamps as ISO-8601 strings.
            Private key is excluded unless explicitly requested.
        """
        # RU: Сериализовать кошелёк в словарь; приватный ключ исключён по умолчанию.
        data = {
            "address": self.address,
            "balance": self.balance,
            "currency": self.currency,
            "label": self.label,
            "is_watch_only": self.is_watch_only,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }

        if include_private_key and not self.is_watch_only:
            data["private_key"] = self.private_key

        return data
