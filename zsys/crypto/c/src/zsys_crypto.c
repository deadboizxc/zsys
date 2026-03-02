/*
 * zsys_crypto.c — OpenSSL implementation of zsys/crypto C API.
 *
 * Algorithms:
 *   AES  : AES-256-CBC, random 16-byte IV prepended, PKCS7 padding
 *   RSA  : RSA-OAEP with SHA-256 (EVP_PKEY keygen + PEM serialisation)
 *   ECC  : ECDH P-256 ephemeral + HKDF-SHA256 + AES-256-GCM
 *
 * All functions allocate output with malloc(); caller must free().
 * Returns NULL on any OpenSSL error.
 */

#include "zsys_crypto.h"

#include <stdlib.h>
#include <string.h>

#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/pem.h>
#include <openssl/bio.h>
#include <openssl/ec.h>
#include <openssl/rsa.h>
#include <openssl/kdf.h>
#include <openssl/err.h>
#include <openssl/objects.h>

/* Suppress deprecation warnings for EC_KEY API used on OpenSSL 3.x */
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"

/* ── internal helpers ──────────────────────────────────────────────────── */

/* Drain a BIO into a NUL-terminated heap string. Caller must free(). */
static char *bio_to_string(BIO *bio)
{
    BUF_MEM *mem = NULL;
    BIO_get_mem_ptr(bio, &mem);
    char *s = malloc(mem->length + 1);
    if (s) {
        memcpy(s, mem->data, mem->length);
        s[mem->length] = '\0';
    }
    return s;
}

/* Load private key from a PEM string. Caller must EVP_PKEY_free(). */
static EVP_PKEY *load_private_key(const char *pem)
{
    BIO *bio = BIO_new_mem_buf(pem, -1);
    if (!bio) return NULL;
    EVP_PKEY *pkey = PEM_read_bio_PrivateKey(bio, NULL, NULL, NULL);
    BIO_free(bio);
    return pkey;
}

/* Load public key from a PEM string. Caller must EVP_PKEY_free(). */
static EVP_PKEY *load_public_key(const char *pem)
{
    BIO *bio = BIO_new_mem_buf(pem, -1);
    if (!bio) return NULL;
    EVP_PKEY *pkey = PEM_read_bio_PUBKEY(bio, NULL, NULL, NULL);
    BIO_free(bio);
    return pkey;
}

/* Serialise an EVP_PKEY to two heap PEM strings (priv + pub).
 * Returns private PEM; sets *pub_out to public PEM. Both must be freed. */
static char *pkey_to_pem_pair(EVP_PKEY *pkey, char **pub_out)
{
    BIO *bp = BIO_new(BIO_s_mem());
    BIO *bb = BIO_new(BIO_s_mem());
    if (!bp || !bb) { BIO_free(bp); BIO_free(bb); return NULL; }

    if (PEM_write_bio_PrivateKey(bp, pkey, NULL, NULL, 0, NULL, NULL) != 1 ||
        PEM_write_bio_PUBKEY(bb, pkey) != 1) {
        BIO_free(bp); BIO_free(bb); return NULL;
    }

    char *priv = bio_to_string(bp);
    char *pub  = bio_to_string(bb);
    BIO_free(bp);
    BIO_free(bb);

    if (!priv || !pub) { free(priv); free(pub); return NULL; }
    *pub_out = pub;
    return priv;
}

/* Copy key bytes into a 32-byte buffer, truncating or zero-padding as needed. */
static void normalise_key_256(const uint8_t *key, size_t key_len, uint8_t out[32])
{
    memset(out, 0, 32);
    memcpy(out, key, key_len < 32 ? key_len : 32);
}

/* HKDF-SHA256: derive out_len bytes from secret into out[].
 * info = "handshake data" (matches Python ECCCipher._derive_key). */
static int hkdf_derive(const uint8_t *secret, size_t secret_len,
                        uint8_t *out, size_t out_len)
{
    EVP_PKEY_CTX *pctx = EVP_PKEY_CTX_new_id(EVP_PKEY_HKDF, NULL);
    if (!pctx) return 0;

    int ok =
        (EVP_PKEY_derive_init(pctx) > 0) &&
        (EVP_PKEY_CTX_set_hkdf_md(pctx, EVP_sha256()) > 0) &&
        (EVP_PKEY_CTX_set1_hkdf_key(pctx, secret, (int)secret_len) > 0) &&
        (EVP_PKEY_CTX_add1_hkdf_info(pctx,
            (const unsigned char *)"handshake data", 14) > 0) &&
        (EVP_PKEY_derive(pctx, out, &out_len) > 0);

    EVP_PKEY_CTX_free(pctx);
    return ok;
}

/* Generate a fresh EC P-256 EVP_PKEY. Caller must EVP_PKEY_free(). */
static EVP_PKEY *generate_ec_key(void)
{
    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_EC, NULL);
    if (!ctx) return NULL;

    EVP_PKEY *pkey = NULL;
    if (EVP_PKEY_keygen_init(ctx) <= 0 ||
        EVP_PKEY_CTX_set_ec_paramgen_curve_nid(ctx, NID_X9_62_prime256v1) <= 0 ||
        EVP_PKEY_keygen(ctx, &pkey) <= 0) {
        EVP_PKEY_CTX_free(ctx);
        return NULL;
    }
    EVP_PKEY_CTX_free(ctx);
    return pkey;
}

/* Extract uncompressed P-256 public key point (65 bytes) from EVP_PKEY. */
static int ec_pkey_pub_bytes(EVP_PKEY *pkey, uint8_t out[65])
{
    const EC_KEY    *ec    = EVP_PKEY_get0_EC_KEY(pkey);
    if (!ec) return 0;
    const EC_GROUP  *group = EC_KEY_get0_group(ec);
    const EC_POINT  *point = EC_KEY_get0_public_key(ec);
    size_t n = EC_POINT_point2oct(group, point,
                                  POINT_CONVERSION_UNCOMPRESSED,
                                  out, 65, NULL);
    return (n == 65);
}

/* Reconstruct an EVP_PKEY (public-only) from 65-byte uncompressed point. */
static EVP_PKEY *ec_pkey_from_pub_bytes(const uint8_t *bytes, size_t len)
{
    EC_KEY   *ec    = EC_KEY_new_by_curve_name(NID_X9_62_prime256v1);
    if (!ec) return NULL;

    const EC_GROUP *group = EC_KEY_get0_group(ec);
    EC_POINT       *pt    = EC_POINT_new(group);

    if (!pt ||
        EC_POINT_oct2point(group, pt, bytes, len, NULL) != 1 ||
        EC_KEY_set_public_key(ec, pt) != 1) {
        EC_POINT_free(pt);
        EC_KEY_free(ec);
        return NULL;
    }
    EC_POINT_free(pt);

    EVP_PKEY *pkey = EVP_PKEY_new();
    if (!pkey || EVP_PKEY_assign_EC_KEY(pkey, ec) != 1) {
        EVP_PKEY_free(pkey);
        EC_KEY_free(ec);
        return NULL;
    }
    return pkey; /* ec now owned by pkey */
}

/* ECDH: derive shared secret, then HKDF into 32-byte AES key. */
static int ecdh_derive_aes_key(EVP_PKEY *priv, EVP_PKEY *peer_pub,
                                uint8_t key_out[32])
{
    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new(priv, NULL);
    if (!ctx) return 0;

    size_t ss_len = 0;
    int ok = (EVP_PKEY_derive_init(ctx) > 0) &&
             (EVP_PKEY_derive_set_peer(ctx, peer_pub) > 0) &&
             (EVP_PKEY_derive(ctx, NULL, &ss_len) > 0);
    if (!ok) { EVP_PKEY_CTX_free(ctx); return 0; }

    uint8_t *ss = malloc(ss_len);
    if (!ss) { EVP_PKEY_CTX_free(ctx); return 0; }

    if (EVP_PKEY_derive(ctx, ss, &ss_len) <= 0) {
        free(ss); EVP_PKEY_CTX_free(ctx); return 0;
    }
    EVP_PKEY_CTX_free(ctx);

    ok = hkdf_derive(ss, ss_len, key_out, 32);
    free(ss);
    return ok;
}

/* ── AES-256-CBC ──────────────────────────────────────────────────────── */

uint8_t *zsys_aes_encrypt(const uint8_t *key,    size_t key_len,
                           const uint8_t *plaintext, size_t pt_len,
                           size_t *out_len)
{
    uint8_t iv[16], aes_key[32];
    if (RAND_bytes(iv, 16) != 1) return NULL;
    normalise_key_256(key, key_len, aes_key);

    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return NULL;

    if (EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, aes_key, iv) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return NULL;
    }

    /* Allocate: IV(16) + ciphertext(pt_len) + padding block(16) */
    uint8_t *out = malloc(16 + pt_len + 16);
    if (!out) { EVP_CIPHER_CTX_free(ctx); return NULL; }

    memcpy(out, iv, 16);

    int len = 0, flen = 0;
    if (EVP_EncryptUpdate(ctx, out + 16, &len, plaintext, (int)pt_len) != 1 ||
        EVP_EncryptFinal_ex(ctx, out + 16 + len, &flen) != 1) {
        free(out); EVP_CIPHER_CTX_free(ctx); return NULL;
    }

    EVP_CIPHER_CTX_free(ctx);
    *out_len = 16 + (size_t)len + (size_t)flen;
    return out;
}

uint8_t *zsys_aes_decrypt(const uint8_t *key,      size_t key_len,
                           const uint8_t *ciphertext, size_t ct_len,
                           size_t *out_len)
{
    if (ct_len < 16) return NULL;

    uint8_t aes_key[32];
    normalise_key_256(key, key_len, aes_key);

    const uint8_t *iv  = ciphertext;
    const uint8_t *enc = ciphertext + 16;
    int enc_len        = (int)(ct_len - 16);

    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return NULL;

    if (EVP_DecryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, aes_key, iv) != 1) {
        EVP_CIPHER_CTX_free(ctx); return NULL;
    }

    uint8_t *out = malloc(enc_len + 16);
    if (!out) { EVP_CIPHER_CTX_free(ctx); return NULL; }

    int len = 0, flen = 0;
    if (EVP_DecryptUpdate(ctx, out, &len, enc, enc_len) != 1 ||
        EVP_DecryptFinal_ex(ctx, out + len, &flen) != 1) {
        free(out); EVP_CIPHER_CTX_free(ctx); return NULL;
    }

    EVP_CIPHER_CTX_free(ctx);
    *out_len = (size_t)len + (size_t)flen;
    return out;
}

/* ── RSA-OAEP ─────────────────────────────────────────────────────────── */

char *zsys_rsa_generate(int key_bits, char **pub_pem)
{
    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_RSA, NULL);
    if (!ctx) return NULL;

    EVP_PKEY *pkey = NULL;
    if (EVP_PKEY_keygen_init(ctx) <= 0 ||
        EVP_PKEY_CTX_set_rsa_keygen_bits(ctx, key_bits) <= 0 ||
        EVP_PKEY_keygen(ctx, &pkey) <= 0) {
        EVP_PKEY_CTX_free(ctx); return NULL;
    }
    EVP_PKEY_CTX_free(ctx);

    char *priv = pkey_to_pem_pair(pkey, pub_pem);
    EVP_PKEY_free(pkey);
    return priv;
}

uint8_t *zsys_rsa_encrypt(const char *pub_pem,
                           const uint8_t *plaintext, size_t pt_len,
                           size_t *out_len)
{
    EVP_PKEY *pkey = load_public_key(pub_pem);
    if (!pkey) return NULL;

    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new(pkey, NULL);
    EVP_PKEY_free(pkey);
    if (!ctx) return NULL;

    if (EVP_PKEY_encrypt_init(ctx) <= 0 ||
        EVP_PKEY_CTX_set_rsa_padding(ctx, RSA_PKCS1_OAEP_PADDING) <= 0 ||
        EVP_PKEY_CTX_set_rsa_oaep_md(ctx, EVP_sha256()) <= 0) {
        EVP_PKEY_CTX_free(ctx); return NULL;
    }

    size_t olen = 0;
    if (EVP_PKEY_encrypt(ctx, NULL, &olen, plaintext, pt_len) <= 0) {
        EVP_PKEY_CTX_free(ctx); return NULL;
    }

    uint8_t *out = malloc(olen);
    if (!out || EVP_PKEY_encrypt(ctx, out, &olen, plaintext, pt_len) <= 0) {
        free(out); EVP_PKEY_CTX_free(ctx); return NULL;
    }

    EVP_PKEY_CTX_free(ctx);
    *out_len = olen;
    return out;
}

uint8_t *zsys_rsa_decrypt(const char *priv_pem,
                           const uint8_t *ciphertext, size_t ct_len,
                           size_t *out_len)
{
    EVP_PKEY *pkey = load_private_key(priv_pem);
    if (!pkey) return NULL;

    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new(pkey, NULL);
    EVP_PKEY_free(pkey);
    if (!ctx) return NULL;

    if (EVP_PKEY_decrypt_init(ctx) <= 0 ||
        EVP_PKEY_CTX_set_rsa_padding(ctx, RSA_PKCS1_OAEP_PADDING) <= 0 ||
        EVP_PKEY_CTX_set_rsa_oaep_md(ctx, EVP_sha256()) <= 0) {
        EVP_PKEY_CTX_free(ctx); return NULL;
    }

    size_t olen = 0;
    if (EVP_PKEY_decrypt(ctx, NULL, &olen, ciphertext, ct_len) <= 0) {
        EVP_PKEY_CTX_free(ctx); return NULL;
    }

    uint8_t *out = malloc(olen);
    if (!out || EVP_PKEY_decrypt(ctx, out, &olen, ciphertext, ct_len) <= 0) {
        free(out); EVP_PKEY_CTX_free(ctx); return NULL;
    }

    EVP_PKEY_CTX_free(ctx);
    *out_len = olen;
    return out;
}

/* ── ECC (ECDH P-256 + AES-256-GCM) ──────────────────────────────────── */

char *zsys_ecc_generate(char **pub_pem)
{
    EVP_PKEY *pkey = generate_ec_key();
    if (!pkey) return NULL;

    char *priv = pkey_to_pem_pair(pkey, pub_pem);
    EVP_PKEY_free(pkey);
    return priv;
}

uint8_t *zsys_ecc_encrypt(const char *pub_pem,
                           const uint8_t *plaintext, size_t pt_len,
                           size_t *out_len)
{
    EVP_PKEY *recv_pub = load_public_key(pub_pem);
    if (!recv_pub) return NULL;

    EVP_PKEY *eph_key = generate_ec_key();
    if (!eph_key) { EVP_PKEY_free(recv_pub); return NULL; }

    uint8_t aes_key[32];
    if (!ecdh_derive_aes_key(eph_key, recv_pub, aes_key)) {
        EVP_PKEY_free(eph_key); EVP_PKEY_free(recv_pub); return NULL;
    }
    EVP_PKEY_free(recv_pub);

    uint8_t eph_pub[65];
    if (!ec_pkey_pub_bytes(eph_key, eph_pub)) {
        EVP_PKEY_free(eph_key); return NULL;
    }
    EVP_PKEY_free(eph_key);

    uint8_t nonce[12];
    if (RAND_bytes(nonce, 12) != 1) return NULL;

    /* Layout: eph_pub(65) | nonce(12) | ciphertext(pt_len) | tag(16) */
    uint8_t *out = malloc(65 + 12 + pt_len + 16);
    if (!out) return NULL;
    memcpy(out,      eph_pub, 65);
    memcpy(out + 65, nonce,   12);

    EVP_CIPHER_CTX *cctx = EVP_CIPHER_CTX_new();
    if (!cctx) { free(out); return NULL; }

    if (EVP_EncryptInit_ex(cctx, EVP_aes_256_gcm(), NULL, NULL, NULL) != 1 ||
        EVP_CIPHER_CTX_ctrl(cctx, EVP_CTRL_GCM_SET_IVLEN, 12, NULL)  != 1 ||
        EVP_EncryptInit_ex(cctx, NULL, NULL, aes_key, nonce)          != 1) {
        free(out); EVP_CIPHER_CTX_free(cctx); return NULL;
    }

    int elen = 0, eflen = 0;
    if (EVP_EncryptUpdate(cctx, out + 65 + 12, &elen,
                          plaintext, (int)pt_len) != 1 ||
        EVP_EncryptFinal_ex(cctx, out + 65 + 12 + elen, &eflen) != 1 ||
        EVP_CIPHER_CTX_ctrl(cctx, EVP_CTRL_GCM_GET_TAG, 16,
                            out + 65 + 12 + elen + eflen) != 1) {
        free(out); EVP_CIPHER_CTX_free(cctx); return NULL;
    }

    EVP_CIPHER_CTX_free(cctx);
    *out_len = 65 + 12 + (size_t)elen + (size_t)eflen + 16;
    return out;
}

uint8_t *zsys_ecc_decrypt(const char *priv_pem,
                           const uint8_t *ciphertext, size_t ct_len,
                           size_t *out_len)
{
    if (ct_len < 65 + 12 + 16) return NULL;

    const uint8_t *eph_pub_bytes = ciphertext;
    const uint8_t *nonce         = ciphertext + 65;
    const uint8_t *enc_data      = ciphertext + 65 + 12;
    size_t         enc_data_len  = ct_len - 65 - 12 - 16;
    const uint8_t *tag           = ciphertext + ct_len - 16;

    EVP_PKEY *priv_key = load_private_key(priv_pem);
    if (!priv_key) return NULL;

    EVP_PKEY *eph_pub = ec_pkey_from_pub_bytes(eph_pub_bytes, 65);
    if (!eph_pub) { EVP_PKEY_free(priv_key); return NULL; }

    uint8_t aes_key[32];
    if (!ecdh_derive_aes_key(priv_key, eph_pub, aes_key)) {
        EVP_PKEY_free(eph_pub); EVP_PKEY_free(priv_key); return NULL;
    }
    EVP_PKEY_free(eph_pub);
    EVP_PKEY_free(priv_key);

    EVP_CIPHER_CTX *cctx = EVP_CIPHER_CTX_new();
    if (!cctx) return NULL;

    if (EVP_DecryptInit_ex(cctx, EVP_aes_256_gcm(), NULL, NULL, NULL)  != 1 ||
        EVP_CIPHER_CTX_ctrl(cctx, EVP_CTRL_GCM_SET_IVLEN, 12, NULL)   != 1 ||
        EVP_DecryptInit_ex(cctx, NULL, NULL, aes_key, nonce)           != 1 ||
        EVP_CIPHER_CTX_ctrl(cctx, EVP_CTRL_GCM_SET_TAG, 16,
                            (void *)tag)                               != 1) {
        EVP_CIPHER_CTX_free(cctx); return NULL;
    }

    uint8_t *out = malloc(enc_data_len + 1);
    if (!out) { EVP_CIPHER_CTX_free(cctx); return NULL; }

    int dlen = 0, dflen = 0;
    if (EVP_DecryptUpdate(cctx, out, &dlen,
                          enc_data, (int)enc_data_len) != 1 ||
        EVP_DecryptFinal_ex(cctx, out + dlen, &dflen)  != 1) {
        /* Authentication tag mismatch or decryption error */
        free(out); EVP_CIPHER_CTX_free(cctx); return NULL;
    }

    EVP_CIPHER_CTX_free(cctx);
    *out_len = (size_t)dlen + (size_t)dflen;
    return out;
}

#pragma GCC diagnostic pop
