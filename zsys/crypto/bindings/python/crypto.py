"""Python cffi binding for zsys/crypto.

Wraps all 8 C functions with three clean classes: AES, RSA, ECC.
C buffers are freed automatically after copying into Python bytes objects.

Usage::

    from zsys.crypto.bindings.python.crypto import AES, RSA, ECC

    # Symmetric
    aes = AES(key=b"my-32-byte-secret-key-padded!!!!")
    ct  = aes.encrypt(b"Hello, world!")
    pt  = aes.decrypt(ct)

    # Asymmetric RSA
    priv, pub = RSA.generate(bits=2048)
    ct  = RSA.encrypt(pub, b"secret")
    pt  = RSA.decrypt(priv, ct)

    # Hybrid ECC
    priv, pub = ECC.generate()
    ct  = ECC.encrypt(pub, b"secret")
    pt  = ECC.decrypt(priv, ct)
"""

from __future__ import annotations

from pathlib import Path


def _load():
    try:
        from cffi import FFI

        ffi = FFI()
        ffi.cdef("""
            void free(void *ptr);

            uint8_t *zsys_aes_encrypt(const uint8_t *key, size_t key_len,
                                       const uint8_t *plaintext, size_t pt_len,
                                       size_t *out_len);
            uint8_t *zsys_aes_decrypt(const uint8_t *key, size_t key_len,
                                       const uint8_t *ciphertext, size_t ct_len,
                                       size_t *out_len);

            char *zsys_rsa_generate(int key_bits, char **pub_pem);
            uint8_t *zsys_rsa_encrypt(const char *pub_pem,
                                       const uint8_t *plaintext, size_t pt_len,
                                       size_t *out_len);
            uint8_t *zsys_rsa_decrypt(const char *priv_pem,
                                       const uint8_t *ciphertext, size_t ct_len,
                                       size_t *out_len);

            char *zsys_ecc_generate(char **pub_pem);
            uint8_t *zsys_ecc_encrypt(const char *pub_pem,
                                       const uint8_t *plaintext, size_t pt_len,
                                       size_t *out_len);
            uint8_t *zsys_ecc_decrypt(const char *priv_pem,
                                       const uint8_t *ciphertext, size_t ct_len,
                                       size_t *out_len);
        """)
        here = Path(__file__).resolve().parent
        for candidate in ["libzsys_crypto.so", "libzsys_crypto.so.1"]:
            for base in [
                here,
                here.parent.parent / "c" / "build",
                Path("/usr/local/lib"),
                Path("/usr/lib"),
            ]:
                p = base / candidate
                if p.exists():
                    return ffi, ffi.dlopen(str(p))
        return ffi, ffi.dlopen("libzsys_crypto.so")
    except Exception as e:
        raise RuntimeError(f"libzsys_crypto.so not found: {e}")


_ffi: object = None
_lib: object = None


def _get_lib():
    global _ffi, _lib
    if _lib is None:
        _ffi, _lib = _load()
    return _ffi, _lib


def _buf_to_bytes(ffi, lib, buf, n: int) -> bytes:
    """Copy C heap buffer into Python bytes and free the C buffer."""
    result = bytes(ffi.buffer(buf, n))
    lib.free(buf)
    return result


class AES:
    """AES-256-CBC symmetric encryption.

    The key is used as-is (truncated or zero-padded to 32 bytes internally).
    Output of encrypt() is: 16-byte random IV + PKCS7-padded ciphertext.
    """

    def __init__(self, key: bytes) -> None:
        self._key = key

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt *data*. Returns IV (16 bytes) + ciphertext."""
        ffi, lib = _get_lib()
        out_len = ffi.new("size_t *")
        buf = lib.zsys_aes_encrypt(
            self._key,
            len(self._key),
            data,
            len(data),
            out_len,
        )
        if buf == ffi.NULL:
            raise RuntimeError("zsys_aes_encrypt failed")
        return _buf_to_bytes(ffi, lib, buf, out_len[0])

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt AES-256-CBC ciphertext produced by :meth:`encrypt`."""
        ffi, lib = _get_lib()
        out_len = ffi.new("size_t *")
        buf = lib.zsys_aes_decrypt(
            self._key,
            len(self._key),
            data,
            len(data),
            out_len,
        )
        if buf == ffi.NULL:
            raise RuntimeError("zsys_aes_decrypt failed")
        return _buf_to_bytes(ffi, lib, buf, out_len[0])


class RSA:
    """RSA-OAEP (SHA-256) asymmetric encryption — all methods are static."""

    @staticmethod
    def generate(bits: int = 2048) -> tuple[str, str]:
        """Generate RSA key pair. Returns ``(priv_pem, pub_pem)``."""
        ffi, lib = _get_lib()
        pub_ptr = ffi.new("char **")
        priv_buf = lib.zsys_rsa_generate(bits, pub_ptr)
        if priv_buf == ffi.NULL:
            raise RuntimeError("zsys_rsa_generate failed")
        priv_pem = ffi.string(priv_buf).decode()
        pub_pem = ffi.string(pub_ptr[0]).decode()
        lib.free(priv_buf)
        lib.free(pub_ptr[0])
        return priv_pem, pub_pem

    @staticmethod
    def encrypt(pub_pem: str, data: bytes) -> bytes:
        """Encrypt *data* with RSA-OAEP using *pub_pem* (PEM string)."""
        ffi, lib = _get_lib()
        out_len = ffi.new("size_t *")
        buf = lib.zsys_rsa_encrypt(
            pub_pem.encode(),
            data,
            len(data),
            out_len,
        )
        if buf == ffi.NULL:
            raise RuntimeError("zsys_rsa_encrypt failed")
        return _buf_to_bytes(ffi, lib, buf, out_len[0])

    @staticmethod
    def decrypt(priv_pem: str, data: bytes) -> bytes:
        """Decrypt RSA-OAEP ciphertext with *priv_pem* (PEM string)."""
        ffi, lib = _get_lib()
        out_len = ffi.new("size_t *")
        buf = lib.zsys_rsa_decrypt(
            priv_pem.encode(),
            data,
            len(data),
            out_len,
        )
        if buf == ffi.NULL:
            raise RuntimeError("zsys_rsa_decrypt failed")
        return _buf_to_bytes(ffi, lib, buf, out_len[0])


class ECC:
    """ECDH P-256 + AES-256-GCM hybrid encryption — all methods are static.

    Ciphertext layout: ephemeral pubkey (65 B) + nonce (12 B) + ciphertext + GCM tag (16 B).
    """

    @staticmethod
    def generate() -> tuple[str, str]:
        """Generate EC P-256 key pair. Returns ``(priv_pem, pub_pem)``."""
        ffi, lib = _get_lib()
        pub_ptr = ffi.new("char **")
        priv_buf = lib.zsys_ecc_generate(pub_ptr)
        if priv_buf == ffi.NULL:
            raise RuntimeError("zsys_ecc_generate failed")
        priv_pem = ffi.string(priv_buf).decode()
        pub_pem = ffi.string(pub_ptr[0]).decode()
        lib.free(priv_buf)
        lib.free(pub_ptr[0])
        return priv_pem, pub_pem

    @staticmethod
    def encrypt(pub_pem: str, data: bytes) -> bytes:
        """Encrypt *data* with ECDH + AES-256-GCM using *pub_pem*."""
        ffi, lib = _get_lib()
        out_len = ffi.new("size_t *")
        buf = lib.zsys_ecc_encrypt(
            pub_pem.encode(),
            data,
            len(data),
            out_len,
        )
        if buf == ffi.NULL:
            raise RuntimeError("zsys_ecc_encrypt failed")
        return _buf_to_bytes(ffi, lib, buf, out_len[0])

    @staticmethod
    def decrypt(priv_pem: str, data: bytes) -> bytes:
        """Decrypt ECDH + AES-256-GCM ciphertext with *priv_pem*."""
        ffi, lib = _get_lib()
        out_len = ffi.new("size_t *")
        buf = lib.zsys_ecc_decrypt(
            priv_pem.encode(),
            data,
            len(data),
            out_len,
        )
        if buf == ffi.NULL:
            raise RuntimeError("zsys_ecc_decrypt failed")
        return _buf_to_bytes(ffi, lib, buf, out_len[0])


__all__ = ["AES", "RSA", "ECC"]
