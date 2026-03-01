"""
Example: AES Encryption and Decryption

This example demonstrates how to use AES cipher
for encrypting and decrypting data.

Install:
    pip install zsys[crypto]

Run:
    python examples/crypto_example.py
"""

from zsys.crypto.aes import AESCipher
from zsys.crypto.rsa import RSACipher
from zsys.crypto.ecc import ECCCipher
from zsys.core.logging import get_logger

logger = get_logger(__name__)


def aes_example():
    """AES encryption example."""
    logger.info("=== AES Encryption Example ===")
    
    # Create cipher with secret key
    cipher = AESCipher(key="my_super_secret_key_12345")
    
    # Original text
    original_text = "Hello, ZSYS! This is a secret message."
    logger.info(f"Original: {original_text}")
    
    # Encrypt
    encrypted = cipher.encrypt_string(original_text)
    logger.info(f"Encrypted (hex): {encrypted.hex()}")
    
    # Decrypt
    decrypted = cipher.decrypt_string(encrypted)
    logger.info(f"Decrypted: {decrypted}")
    
    assert original_text == decrypted, "Decryption failed!"
    logger.info("✅ AES encryption/decryption successful!\n")


def rsa_example():
    """RSA encryption example."""
    logger.info("=== RSA Encryption Example ===")
    
    # Generate new key pair
    cipher = RSACipher.generate(key_size=2048)
    
    # Original text
    original_text = "Hello, RSA!"
    logger.info(f"Original: {original_text}")
    
    # Encrypt with public key
    encrypted = cipher.encrypt_string(original_text)
    logger.info(f"Encrypted (hex): {encrypted.hex()[:100]}...")
    
    # Decrypt with private key
    decrypted = cipher.decrypt_string(encrypted)
    logger.info(f"Decrypted: {decrypted}")
    
    # Export keys
    private_pem = cipher.export_private_key()
    public_pem = cipher.export_public_key()
    logger.info(f"Private key (PEM):\n{private_pem.decode()[:100]}...")
    logger.info(f"Public key (PEM):\n{public_pem.decode()[:100]}...")
    
    assert original_text == decrypted, "Decryption failed!"
    logger.info("✅ RSA encryption/decryption successful!\n")


def ecc_example():
    """ECC encryption example."""
    logger.info("=== ECC Encryption Example ===")
    
    # Generate new key pair
    cipher = ECCCipher.generate()
    
    # Original text
    original_text = "Hello, ECC! Elliptic curves are awesome!"
    logger.info(f"Original: {original_text}")
    
    # Encrypt
    encrypted = cipher.encrypt_string(original_text)
    logger.info(f"Encrypted (hex): {encrypted.hex()[:100]}...")
    
    # Decrypt
    decrypted = cipher.decrypt_string(encrypted)
    logger.info(f"Decrypted: {decrypted}")
    
    assert original_text == decrypted, "Decryption failed!"
    logger.info("✅ ECC encryption/decryption successful!\n")


def main():
    """Run all examples."""
    logger.info("Starting Crypto Examples...\n")
    
    try:
        aes_example()
        rsa_example()
        ecc_example()
        
        logger.info("🎉 All crypto examples completed successfully!")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
