"""
Example: Simple Blockchain

This example demonstrates how to use the simple blockchain
implementation for educational purposes.

Install:
    pip install zsys

Run:
    python examples/blockchain_example.py
"""

from zsys.blockchain.simple_chain import SimpleBlockchain
from zsys.core.logging import get_logger
import json

logger = get_logger(__name__)


def main():
    """Main function."""
    logger.info("=== Simple Blockchain Example ===\n")
    
    # Create blockchain with difficulty 4 (4 leading zeros)
    blockchain = SimpleBlockchain(difficulty=4)
    logger.info(f"Blockchain created with difficulty {blockchain.difficulty}\n")
    
    # Add some transactions
    logger.info("Adding transactions...")
    
    transactions = [
        {"from": "Alice", "to": "Bob", "amount": 50},
        {"from": "Bob", "to": "Charlie", "amount": 25},
        {"from": "Alice", "to": "Charlie", "amount": 30},
        {"from": "Charlie", "to": "Bob", "amount": 10},
    ]
    
    for tx in transactions:
        blockchain.add_block(tx)
        logger.info(f"  Added: {tx}")
    
    logger.info("\n")
    
    # Validate blockchain
    is_valid = blockchain.validate_chain()
    logger.info(f"Blockchain is valid: {is_valid}\n")
    
    # Show balances
    logger.info("=== Balances ===")
    for person in ["Alice", "Bob", "Charlie"]:
        balance = blockchain.get_balance(person)
        logger.info(f"{person}: {balance}")
    
    logger.info("\n")
    
    # Show blockchain details
    logger.info("=== Blockchain Details ===")
    blockchain_dict = blockchain.to_dict()
    logger.info(f"Total blocks: {blockchain_dict['length']}")
    logger.info(f"Difficulty: {blockchain_dict['difficulty']}")
    logger.info(f"Valid: {blockchain_dict['is_valid']}")
    
    logger.info("\n=== Blocks ===")
    for block in blockchain_dict['blocks'][:3]:  # Show first 3 blocks
        logger.info(f"\nBlock #{block['index']}")
        logger.info(f"  Hash: {block['hash'][:20]}...")
        logger.info(f"  Previous: {block['previous_hash'][:20]}...")
        logger.info(f"  Data: {block['data']}")
        logger.info(f"  Nonce: {block['nonce']}")
    
    # Try to tamper with blockchain
    logger.info("\n=== Testing Blockchain Security ===")
    logger.info("Attempting to tamper with block #2...")
    
    # Modify data in block 2
    original_data = blockchain.chain[2].data
    blockchain.chain[2].data = {"from": "Hacker", "to": "Hacker", "amount": 9999}
    
    is_valid_after_tamper = blockchain.validate_chain()
    logger.info(f"Blockchain is valid after tampering: {is_valid_after_tamper}")
    
    # Restore original data
    blockchain.chain[2].data = original_data
    is_valid_restored = blockchain.validate_chain()
    logger.info(f"Blockchain is valid after restoration: {is_valid_restored}")
    
    logger.info("\n✅ Blockchain example completed!")


if __name__ == "__main__":
    main()
