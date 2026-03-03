"""BaseWallet model - cryptocurrency wallet entity."""

from decimal import Decimal
from sqlalchemy import Column, String, Integer, ForeignKey, Numeric

from .base import BaseModel


class BaseWallet(BaseModel):
    """
    Base Wallet model - represents a cryptocurrency wallet.

    Stores balance as string to avoid floating-point precision issues.
    For precise calculations, convert to Decimal.

    Attributes:
        address: Wallet address (unique)
        label: Human-readable label
        balance: Current balance (as string for precision)
        user_id: Foreign key to the User who owns this wallet (optional)
        currency: Currency code (USD, BTC, ETH, etc.)
    """

    __tablename__ = "wallets"

    address = Column(String(255), unique=True, nullable=False, index=True)
    label = Column(String(255), nullable=True)
    balance = Column(String(100), default="0")  # Store as string for precision
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    currency = Column(String(10), default="USD")

    @property
    def balance_decimal(self) -> Decimal:
        """Get balance as Decimal for calculations."""
        return Decimal(self.balance or "0")

    def __repr__(self) -> str:
        return f"<BaseWallet(id={self.id}, address={self.address[:16]}...)>"


# Backward compatible alias
Wallet = BaseWallet

__all__ = ["BaseWallet", "Wallet"]
