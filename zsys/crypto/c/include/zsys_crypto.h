#ifndef ZSYS_CRYPTO_H
#define ZSYS_CRYPTO_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ── AES-256-CBC ─────────────────────────────────────────────── */
/* Encrypts plaintext. Output = 16-byte IV + ciphertext (PKCS7).
 * Returns heap-allocated buffer; *out_len = total bytes.
 * Caller must free(). Returns NULL on error. */
uint8_t *zsys_aes_encrypt(const uint8_t *key, size_t key_len,
                           const uint8_t *plaintext, size_t pt_len,
                           size_t *out_len);

/* Decrypts buffer produced by zsys_aes_encrypt.
 * Returns heap-allocated plaintext; *out_len = plaintext length. */
uint8_t *zsys_aes_decrypt(const uint8_t *key, size_t key_len,
                           const uint8_t *ciphertext, size_t ct_len,
                           size_t *out_len);

/* ── RSA-OAEP ────────────────────────────────────────────────── */
/* Generate RSA key pair. key_bits = 2048 or 4096.
 * Returns PEM-encoded private key; *pub_pem = heap-alloc public key.
 * Caller must free() both. Returns NULL on error. */
char *zsys_rsa_generate(int key_bits, char **pub_pem);

/* Encrypt with RSA-OAEP (public key PEM). Returns heap-alloc bytes. */
uint8_t *zsys_rsa_encrypt(const char *pub_pem,
                           const uint8_t *plaintext, size_t pt_len,
                           size_t *out_len);

/* Decrypt with RSA-OAEP (private key PEM). Returns heap-alloc bytes. */
uint8_t *zsys_rsa_decrypt(const char *priv_pem,
                           const uint8_t *ciphertext, size_t ct_len,
                           size_t *out_len);

/* ── ECC (ECDH P-256 + AES-256-GCM) ─────────────────────────── */
/* Generate EC key pair. Returns PEM private key; *pub_pem = PEM public key.
 * Caller must free() both. */
char *zsys_ecc_generate(char **pub_pem);

/* Encrypt: ECDH ephemeral + AES-256-GCM.
 * Output = 65-byte uncompressed ephemeral pubkey + 12-byte nonce + ciphertext + 16-byte GCM tag.
 * Returns heap-alloc bytes; *out_len = total. */
uint8_t *zsys_ecc_encrypt(const char *pub_pem,
                           const uint8_t *plaintext, size_t pt_len,
                           size_t *out_len);

/* Decrypt buffer produced by zsys_ecc_encrypt. */
uint8_t *zsys_ecc_decrypt(const char *priv_pem,
                           const uint8_t *ciphertext, size_t ct_len,
                           size_t *out_len);

#ifdef __cplusplus
}
#endif
#endif /* ZSYS_CRYPTO_H */
