// Vala VAPI binding for zsys_crypto.
// Declares all 8 C functions in the ZsysCrypto namespace.
//
// Build:
//   valac --vapidir=. --pkg zsys_crypto -X -lzsys_crypto your_app.vala
//
// Usage:
//   size_t out_len;
//   uint8* ct = ZsysCrypto.aes_encrypt(key, 32, plaintext, pt_len, out out_len);
//   // ... use ct[0..out_len] ...
//   GLib.free(ct);

[CCode (cheader_filename = "zsys_crypto.h", cprefix = "zsys_")]
namespace ZsysCrypto {

    /* ── AES-256-CBC ─────────────────────────────────────────── */

    [CCode (cname = "zsys_aes_encrypt")]
    public static uint8* aes_encrypt (
        uint8* key,  size_t key_len,
        uint8* plaintext, size_t pt_len,
        out size_t out_len
    );

    [CCode (cname = "zsys_aes_decrypt")]
    public static uint8* aes_decrypt (
        uint8* key,  size_t key_len,
        uint8* ciphertext, size_t ct_len,
        out size_t out_len
    );

    /* ── RSA-OAEP ────────────────────────────────────────────── */

    [CCode (cname = "zsys_rsa_generate")]
    public static string? rsa_generate (int key_bits, out string? pub_pem);

    [CCode (cname = "zsys_rsa_encrypt")]
    public static uint8* rsa_encrypt (
        string pub_pem,
        uint8* plaintext, size_t pt_len,
        out size_t out_len
    );

    [CCode (cname = "zsys_rsa_decrypt")]
    public static uint8* rsa_decrypt (
        string priv_pem,
        uint8* ciphertext, size_t ct_len,
        out size_t out_len
    );

    /* ── ECC (ECDH P-256 + AES-256-GCM) ─────────────────────── */

    [CCode (cname = "zsys_ecc_generate")]
    public static string? ecc_generate (out string? pub_pem);

    [CCode (cname = "zsys_ecc_encrypt")]
    public static uint8* ecc_encrypt (
        string pub_pem,
        uint8* plaintext, size_t pt_len,
        out size_t out_len
    );

    [CCode (cname = "zsys_ecc_decrypt")]
    public static uint8* ecc_decrypt (
        string priv_pem,
        uint8* ciphertext, size_t ct_len,
        out size_t out_len
    );
}
