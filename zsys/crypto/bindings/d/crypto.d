// D binding for zsys/crypto via extern(C).
//
// Build: dmd crypto.d -L-lzsys_crypto
//
// Usage:
//   auto aes = new AES(cast(ubyte[])"my-32-byte-key!!!!!!!!!!!!!!!!!");
//   ubyte[] ct = aes.encrypt(cast(ubyte[])"Hello");
//   ubyte[] pt = aes.decrypt(ct);
//
//   auto [privPem, pubPem] = RSA.generate(2048);
//   ubyte[] ct = RSA.encrypt(pubPem, cast(ubyte[])"secret");
//
//   auto [privPem, pubPem] = ECC.generate();
//   ubyte[] ct = ECC.encrypt(pubPem, cast(ubyte[])"secret");

module zsys.crypto;

import core.stdc.stdlib : free;
import std.string : toStringz, fromStringz;

// ── raw C declarations ──────────────────────────────────────────────── //

extern (C) {
    uint8_t* zsys_aes_encrypt(const uint8_t* key, size_t key_len,
                               const uint8_t* plaintext, size_t pt_len,
                               size_t* out_len);
    uint8_t* zsys_aes_decrypt(const uint8_t* key, size_t key_len,
                               const uint8_t* ciphertext, size_t ct_len,
                               size_t* out_len);

    char* zsys_rsa_generate(int key_bits, char** pub_pem);
    uint8_t* zsys_rsa_encrypt(const char* pub_pem,
                               const uint8_t* plaintext, size_t pt_len,
                               size_t* out_len);
    uint8_t* zsys_rsa_decrypt(const char* priv_pem,
                               const uint8_t* ciphertext, size_t ct_len,
                               size_t* out_len);

    char* zsys_ecc_generate(char** pub_pem);
    uint8_t* zsys_ecc_encrypt(const char* pub_pem,
                               const uint8_t* plaintext, size_t pt_len,
                               size_t* out_len);
    uint8_t* zsys_ecc_decrypt(const char* priv_pem,
                               const uint8_t* ciphertext, size_t ct_len,
                               size_t* out_len);
}

// ── internal helpers ─────────────────────────────────────────────────── //

private ubyte[] cBufToD(uint8_t* ptr, size_t n) {
    assert(ptr, "C function returned NULL");
    auto result = ptr[0 .. n].dup;
    free(ptr);
    return result;
}

// ── AES-256-CBC ──────────────────────────────────────────────────────── //

/// AES-256-CBC symmetric encryption. RAII — key is copied on construction.
class AES {
    private ubyte[] _key;

    this(ubyte[] key) { _key = key.dup; }

    /// Encrypt data. Returns IV (16 B) + ciphertext.
    ubyte[] encrypt(ubyte[] data) {
        size_t n;
        auto p = zsys_aes_encrypt(
            _key.ptr, _key.length,
            data.ptr, data.length, &n);
        if (!p) throw new Exception("zsys_aes_encrypt failed");
        return cBufToD(p, n);
    }

    /// Decrypt ciphertext produced by encrypt().
    ubyte[] decrypt(ubyte[] data) {
        size_t n;
        auto p = zsys_aes_decrypt(
            _key.ptr, _key.length,
            data.ptr, data.length, &n);
        if (!p) throw new Exception("zsys_aes_decrypt failed");
        return cBufToD(p, n);
    }
}

// ── RSA-OAEP ─────────────────────────────────────────────────────────── //

struct KeyPair {
    string priv_;
    string pub_;
}

/// RSA-OAEP (SHA-256) asymmetric encryption — all methods are static.
class RSA {
    /// Generate RSA key pair. Returns KeyPair with priv_ and pub_ PEM strings.
    static KeyPair generate(int bits = 2048) {
        char* pubPtr;
        char* privPtr = zsys_rsa_generate(bits, &pubPtr);
        if (!privPtr) throw new Exception("zsys_rsa_generate failed");
        scope (exit) { free(privPtr); free(pubPtr); }
        return KeyPair(fromStringz(privPtr).idup, fromStringz(pubPtr).idup);
    }

    /// Encrypt data with RSA-OAEP using pubPem (PEM string).
    static ubyte[] encrypt(string pubPem, ubyte[] data) {
        size_t n;
        auto p = zsys_rsa_encrypt(
            pubPem.toStringz, data.ptr, data.length, &n);
        if (!p) throw new Exception("zsys_rsa_encrypt failed");
        return cBufToD(p, n);
    }

    /// Decrypt RSA-OAEP ciphertext using privPem (PEM string).
    static ubyte[] decrypt(string privPem, ubyte[] data) {
        size_t n;
        auto p = zsys_rsa_decrypt(
            privPem.toStringz, data.ptr, data.length, &n);
        if (!p) throw new Exception("zsys_rsa_decrypt failed");
        return cBufToD(p, n);
    }
}

// ── ECC (ECDH P-256 + AES-256-GCM) ──────────────────────────────────── //

/// ECDH P-256 + AES-256-GCM hybrid encryption — all methods are static.
/// Ciphertext layout: eph_pub (65 B) | nonce (12 B) | ciphertext | tag (16 B).
class ECC {
    /// Generate EC P-256 key pair. Returns KeyPair with priv_ and pub_ PEM strings.
    static KeyPair generate() {
        char* pubPtr;
        char* privPtr = zsys_ecc_generate(&pubPtr);
        if (!privPtr) throw new Exception("zsys_ecc_generate failed");
        scope (exit) { free(privPtr); free(pubPtr); }
        return KeyPair(fromStringz(privPtr).idup, fromStringz(pubPtr).idup);
    }

    /// Encrypt data with ECDH + AES-256-GCM using pubPem (PEM string).
    static ubyte[] encrypt(string pubPem, ubyte[] data) {
        size_t n;
        auto p = zsys_ecc_encrypt(
            pubPem.toStringz, data.ptr, data.length, &n);
        if (!p) throw new Exception("zsys_ecc_encrypt failed");
        return cBufToD(p, n);
    }

    /// Decrypt ECDH + AES-256-GCM ciphertext using privPem (PEM string).
    static ubyte[] decrypt(string privPem, ubyte[] data) {
        size_t n;
        auto p = zsys_ecc_decrypt(
            privPem.toStringz, data.ptr, data.length, &n);
        if (!p) throw new Exception("zsys_ecc_decrypt failed");
        return cBufToD(p, n);
    }
}
