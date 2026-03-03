"""IWallet — abstract contract for cryptocurrency wallet implementations.

Defines the structural Protocol interface that all wallet backends
(Bitcoin, Ethereum, EVM chains, hardware wallets) must satisfy.
"""
# RU: Интерфейс IWallet — контракт для реализаций криптовалютных кошельков.
# RU: Все бэкенды (Bitcoin, Ethereum, EVM и др.) должны соответствовать этому протоколу.

from typing import Protocol, runtime_checkable, Any, Optional


@runtime_checkable
class IWallet(Protocol):
    """Abstract contract for cryptocurrency wallet implementations.

    All wallet backends must expose identity properties (address, private_key,
    balance) and the full transaction lifecycle: create, sign, send, and query.

    Warning:
        Handle ``private_key`` with extreme care.  Never log or expose it
        over untrusted channels.

    Supported implementations:
        - EVMWallet: Ethereum and EVM-compatible chains
        - BitcoinWallet: Bitcoin network (future)
        - HardwareWallet: Ledger/Trezor integrations (future)
    """

    # RU: Абстрактный контракт для реализаций криптовалютных кошельков.

    @property
    def address(self) -> str:
        """Public wallet address (derived from the public key).

        Returns:
            Blockchain address string (e.g. ``"0xAbCd..."``) for this wallet.
        """
        # RU: Публичный адрес кошелька (производный от открытого ключа).
        ...

    @property
    def private_key(self) -> str:
        """Raw private key for this wallet.

        Warning:
            Never expose this value over network or in logs.
            Possession of the private key grants full control of the wallet.

        Returns:
            Private key as a hex string.
        """
        # RU: Закрытый ключ кошелька. НИКОГДА не передавать по сети или в логи.
        ...

    @property
    def balance(self) -> float:
        """Current balance of the wallet in the native chain currency.

        Returns:
            Balance as a float (e.g. ETH for Ethereum wallets).
        """
        # RU: Текущий баланс кошелька в нативной валюте цепочки.
        ...

    def create_transaction(self, to: str, amount: float, **kwargs: Any) -> Any:
        """Build an unsigned transaction transferring *amount* to *to*.

        Implementations must populate all required fields (nonce, gas, etc.)
        but must NOT sign the transaction.

        Args:
            to: Recipient wallet address.
            amount: Amount to transfer in the native currency units.
            **kwargs: Chain-specific parameters (gas_price, gas_limit, nonce).

        Returns:
            Unsigned transaction object (format is implementation-specific).
        """
        # RU: Создать неподписанную транзакцию перевода amount монет на адрес to.
        ...

    def sign_transaction(self, transaction: Any) -> Any:
        """Sign *transaction* with this wallet's private key.

        Args:
            transaction: Unsigned transaction object from :meth:`create_transaction`.

        Returns:
            Signed transaction ready for broadcasting.
        """
        # RU: Подписать транзакцию закрытым ключом кошелька.
        ...

    async def send_transaction(self, transaction: Any) -> str:
        """Broadcast a signed transaction to the network.

        Args:
            transaction: Signed transaction object from :meth:`sign_transaction`.

        Returns:
            Transaction hash (hex string) assigned by the network.

        Raises:
            BlockchainError: If the network rejects the transaction.
        """
        # RU: Отправить подписанную транзакцию в сеть; вернуть хеш транзакции.
        ...

    async def get_transaction(self, tx_hash: str) -> Optional[Any]:
        """Fetch a transaction from the network by its hash.

        Args:
            tx_hash: Transaction hash returned by :meth:`send_transaction`.

        Returns:
            Transaction object (format is implementation-specific),
            or None if not found.
        """
        # RU: Получить транзакцию из сети по хешу; None, если не найдена.
        ...


__all__ = [
    "IWallet",
]
