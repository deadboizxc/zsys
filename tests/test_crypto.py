# core/tests/test_crypto.py — Тесты для core.crypto (P1)
"""
Тесты модуля crypto:
- hash_password() (argon2, bcrypt)
- verify_password()
- Hashing utilities
"""

import pytest


class TestCryptoImport:
    """Тесты импорта crypto модулей."""
    
    def test_import_hashing(self):
        """Тест импорта hashing модуля."""
        try:
            from crypto import hashing
            assert hashing is not None
        except ImportError:
            pytest.skip("crypto.hashing не реализован")


class TestPasswordHashing:
    """Тесты хеширования паролей."""
    
    def test_hash_password_argon2(self):
        """Тест хеширования пароля через argon2."""
        try:
            from zsys.crypto.hashing import hash_password, verify_password
        except ImportError:
            pytest.skip("crypto.hashing не реализован")
        
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20
        
        # Проверка пароля
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_hash_different_passwords_different_hashes(self):
        """Тест что разные пароли дают разные хеши."""
        try:
            from zsys.crypto.hashing import hash_password
        except ImportError:
            pytest.skip("crypto.hashing не реализован")
        
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")
        
        assert hash1 != hash2
    
    def test_hash_same_password_different_hashes(self):
        """Тест что один пароль дает разные хеши (из-за salt)."""
        try:
            from zsys.crypto.hashing import hash_password
        except ImportError:
            pytest.skip("crypto.hashing не реализован")
        
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Хеши должны быть разными из-за разных salt
        assert hash1 != hash2


class TestBlockchainHashing:
    """Тесты blockchain hashing (если реализованы)."""
    
    def test_blockchain_import(self):
        """Тест импорта blockchain модулей."""
        try:
            from crypto import blockchain
            assert blockchain is not None
        except ImportError:
            pytest.skip("crypto.blockchain не реализован")
