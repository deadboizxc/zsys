"""IBlockchain — abstract contract for blockchain backend implementations.

Defines the structural subtyping interface (Protocol) that all blockchain
backends must satisfy: block addition, chain validation, balance queries,
and block retrieval.
"""
# RU: Интерфейс IBlockchain — контракт для реализаций блокчейн-бэкендов.
# RU: Используется структурная типизация (Protocol): явное наследование не требуется.

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class IBlockchain(Protocol):
    """Abstract contract for blockchain implementations.

    All concrete backends (SimpleBlockchain, EVMChain, etc.) must satisfy
    this structural interface.  Implementations do not need to inherit
    explicitly — duck typing via ``isinstance(obj, IBlockchain)`` is supported.

    Supported backends:
        - SimpleBlockchain: educational proof-of-work chain
        - EVMChain: Ethereum and EVM-compatible networks
        - BitcoinChain: Bitcoin network (future)
    """

    # RU: Абстрактный контракт для реализаций блокчейна.

    def add_block(self, data: Any) -> Any:
        """Append a new block carrying *data* to the chain.

        Implementations must create a valid block (hash linkage, PoW or
        equivalent), append it to the internal chain list, and return it.

        Args:
            data: Arbitrary block payload (transactions dict, string, etc.).

        Returns:
            The newly created and appended block object.

        Raises:
            BlockchainError: If block creation or validation fails.
        """
        # RU: Добавить новый блок с данными data в цепочку и вернуть его.
        ...

    def validate_chain(self) -> bool:
        """Verify the integrity of the entire blockchain.

        Implementations must check that every block's hash matches its
        computed hash and that each block's previous_hash equals the hash
        of the preceding block.

        Returns:
            True if the chain is intact and unmodified, False otherwise.
        """
        # RU: Проверить целостность всей цепочки блоков.
        ...

    def get_balance(self, address: str) -> float:
        """Calculate the net balance for a wallet address.

        Implementations must scan all transaction blocks and sum credits
        minus debits for *address*.

        Args:
            address: Wallet address (public key or account identifier).

        Returns:
            Current balance as a float (0.0 if no transactions found).
        """
        # RU: Вычислить баланс кошелька по адресу, сканируя все блоки.
        ...

    def get_block(self, index: int) -> Optional[Any]:
        """Retrieve a block by its position in the chain.

        Args:
            index: Zero-based block index (0 = genesis block).

        Returns:
            The block at *index*, or None if the index is out of range.
        """
        # RU: Получить блок по индексу; None если индекс вне диапазона.
        ...

    @property
    def chain(self) -> list[Any]:
        """The complete ordered list of blocks in the chain.

        Returns:
            List of block objects from genesis to latest.
        """
        # RU: Полный упорядоченный список блоков от генезиса до последнего.
        ...

    @property
    def latest_block(self) -> Any:
        """The most recently appended block.

        Returns:
            The last block object in the chain.
        """
        # RU: Последний добавленный блок цепочки.
        ...


__all__ = [
    "IBlockchain",
]
