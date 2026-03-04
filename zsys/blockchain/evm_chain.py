"""EVM chain implementation — Ethereum and EVM-compatible blockchain backends.

Provides EVMWallet and EVMChain classes that implement IWallet and IBlockchain
for Ethereum, BSC, Polygon, and any other EVM-compatible network.

Requires web3::

    pip install zsys[blockchain]
"""
# RU: Реализация EVM-цепочки — Ethereum и совместимые блокчейны.
# RU: Требует web3: pip install zsys[blockchain].

from typing import Any, Optional
from zsys.core.interfaces import IBlockchain, IWallet
from zsys.core.dataclass_models import BaseWallet, BaseTransaction, TransactionStatus
from zsys.log import get_logger
from zsys.core.exceptions import BlockchainError, TransactionError

try:
    from web3 import Web3
    from eth_account import Account

    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    Web3 = None
    Account = None


logger = get_logger(__name__)


class EVMWallet(IWallet):
    """
    EVM wallet implementation.

    Works with Ethereum and EVM-compatible chains (BSC, Polygon, etc.)

    Install with:
        pip install zsys[blockchain]

    Usage:
        wallet = EVMWallet.generate()
        print(f"Address: {wallet.address}")
        print(f"Balance: {await wallet.balance} ETH")
    """

    # RU: Кошелёк EVM. Поддерживает Ethereum и все совместимые сети.

    def __init__(self, private_key: str, w3: Optional[Any] = None):
        """
        Initialize EVM wallet.

        Args:
            private_key: Private key (hex string)
            w3: Web3 instance (optional)
        """
        if not WEB3_AVAILABLE:
            raise BlockchainError(
                "Web3 is not installed. Install with: pip install zsys[blockchain]"
            )

        self._private_key = private_key
        self._account = Account.from_key(private_key)
        self._w3 = w3 or Web3(Web3.HTTPProvider("https://eth.llamarpc.com"))

    @classmethod
    def generate(cls, w3: Optional[Any] = None) -> "EVMWallet":
        """
        Generate new EVM wallet.

        Args:
            w3: Web3 instance (optional)

        Returns:
            New EVMWallet instance
        """
        if not WEB3_AVAILABLE:
            raise BlockchainError(
                "Web3 is not installed. Install with: pip install zsys[blockchain]"
            )

        account = Account.create()
        return cls(account.key.hex(), w3)

    @property
    def address(self) -> str:
        """Get wallet address."""
        return self._account.address

    @property
    def private_key(self) -> str:
        """Get private key."""
        return self._private_key

    @property
    def balance(self) -> float:
        """Get current wallet balance in ETH."""
        balance_wei = self._w3.eth.get_balance(self.address)
        return self._w3.from_wei(balance_wei, "ether")

    def create_transaction(self, to: str, amount: float, **kwargs: Any) -> dict:
        """
        Create a new transaction.

        Args:
            to: Recipient address
            amount: Amount in ETH
            **kwargs: Additional parameters (gas_price, gas_limit, nonce)

        Returns:
            Transaction dictionary
        """
        nonce = kwargs.get("nonce") or self._w3.eth.get_transaction_count(self.address)
        gas_price = kwargs.get("gas_price") or self._w3.eth.gas_price
        gas_limit = kwargs.get("gas_limit", 21000)

        transaction = {
            "nonce": nonce,
            "to": to,
            "value": self._w3.to_wei(amount, "ether"),
            "gas": gas_limit,
            "gasPrice": gas_price,
            "chainId": self._w3.eth.chain_id,
        }

        return transaction

    def sign_transaction(self, transaction: dict) -> Any:
        """
        Sign a transaction.

        Args:
            transaction: Transaction dictionary

        Returns:
            Signed transaction
        """
        signed = self._w3.eth.account.sign_transaction(transaction, self._private_key)
        return signed

    async def send_transaction(self, transaction: dict) -> str:
        """
        Send a signed transaction.

        Args:
            transaction: Signed transaction

        Returns:
            Transaction hash
        """
        signed = self.sign_transaction(transaction)
        tx_hash = self._w3.eth.send_raw_transaction(signed.rawTransaction)
        return tx_hash.hex()

    async def get_transaction(self, tx_hash: str) -> Optional[dict]:
        """
        Get transaction by hash.

        Args:
            tx_hash: Transaction hash

        Returns:
            Transaction dictionary or None
        """
        try:
            tx = self._w3.eth.get_transaction(tx_hash)
            return dict(tx) if tx else None
        except Exception as e:
            logger.error(f"Failed to get transaction: {e}")
            return None


class EVMChain(IBlockchain):
    """
    EVM chain implementation.

    Provides blockchain interface for Ethereum and EVM-compatible chains.

    Usage:
        chain = EVMChain("https://eth.llamarpc.com")

        balance = chain.get_balance("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
        block = chain.get_block(12345)
    """

    # RU: Реализация IBlockchain для EVM-совместимых блокчейнов.

    def __init__(self, rpc_url: str = "https://eth.llamarpc.com"):
        """
        Initialize EVM chain.

        Args:
            rpc_url: RPC endpoint URL
        """
        if not WEB3_AVAILABLE:
            raise BlockchainError(
                "Web3 is not installed. Install with: pip install zsys[blockchain]"
            )

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not self.w3.is_connected():
            raise BlockchainError(f"Failed to connect to {rpc_url}")

        logger.info(f"Connected to EVM chain (ID: {self.w3.eth.chain_id})")

    def add_block(self, data: Any) -> Any:
        """Not applicable for EVM chains (blocks are mined by network)."""
        raise NotImplementedError("Cannot add blocks to EVM chain directly")

    def validate_chain(self) -> bool:
        """EVM chain validation is done by network consensus."""
        return self.w3.is_connected()

    def get_balance(self, address: str) -> float:
        """
        Get balance for an address.

        Args:
            address: Wallet address

        Returns:
            Balance in ETH
        """
        balance_wei = self.w3.eth.get_balance(address)
        return self.w3.from_wei(balance_wei, "ether")

    def get_block(self, index: int) -> Optional[dict]:
        """
        Get block by number.

        Args:
            index: Block number

        Returns:
            Block dictionary or None
        """
        try:
            block = self.w3.eth.get_block(index)
            return dict(block) if block else None
        except Exception as e:
            logger.error(f"Failed to get block: {e}")
            return None

    @property
    def chain(self) -> list:
        """Not applicable for EVM chains (too large)."""
        raise NotImplementedError("Cannot get entire EVM chain")

    @property
    def latest_block(self) -> dict:
        """Get the latest block."""
        return dict(self.w3.eth.get_block("latest"))


__all__ = ["EVMWallet", "EVMChain"]
