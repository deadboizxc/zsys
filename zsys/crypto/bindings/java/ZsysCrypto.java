// Java binding for zsys/crypto via JNA.
// Add to pom.xml / build.gradle:
//   net.java.dev.jna:jna:5.14.0
//
// Usage:
//   try (var aes = new ZsysCrypto.AES(key)) {
//       byte[] ct = aes.encrypt(plaintext);
//       byte[] pt = aes.decrypt(ct);
//   }
//
//   var pair = ZsysCrypto.RSA.generate(2048);
//   byte[] ct = ZsysCrypto.RSA.encrypt(pair.pubPem, plaintext);
//
//   var pair = ZsysCrypto.ECC.generate();
//   byte[] ct = ZsysCrypto.ECC.encrypt(pair.pubPem, plaintext);

package zsys.crypto;

import com.sun.jna.*;
import com.sun.jna.ptr.*;

public final class ZsysCrypto {

    private ZsysCrypto() {}

    // ── raw JNA interface ─────────────────────────────────────────────── //

    interface Lib extends Library {
        Lib INSTANCE = Native.load("zsys_crypto", Lib.class);

        // AES
        Pointer zsys_aes_encrypt(
            byte[] key,  long keyLen,
            byte[] plaintext, long ptLen,
            LongByReference outLen);
        Pointer zsys_aes_decrypt(
            byte[] key,  long keyLen,
            byte[] ciphertext, long ctLen,
            LongByReference outLen);

        // RSA
        Pointer zsys_rsa_generate(int keyBits, PointerByReference pubPem);
        Pointer zsys_rsa_encrypt(
            String pubPem,
            byte[] plaintext, long ptLen,
            LongByReference outLen);
        Pointer zsys_rsa_decrypt(
            String privPem,
            byte[] ciphertext, long ctLen,
            LongByReference outLen);

        // ECC
        Pointer zsys_ecc_generate(PointerByReference pubPem);
        Pointer zsys_ecc_encrypt(
            String pubPem,
            byte[] plaintext, long ptLen,
            LongByReference outLen);
        Pointer zsys_ecc_decrypt(
            String privPem,
            byte[] ciphertext, long ctLen,
            LongByReference outLen);

        void free(Pointer ptr);
    }

    // ── internal helper ───────────────────────────────────────────────── //

    private static byte[] readAndFree(Pointer ptr, long len) {
        byte[] bytes = ptr.getByteArray(0, (int) len);
        Lib.INSTANCE.free(ptr);
        return bytes;
    }

    // ── KeyPair return type ───────────────────────────────────────────── //

    public static final class KeyPair {
        public final String privPem;
        public final String pubPem;

        KeyPair(String privPem, String pubPem) {
            this.privPem = privPem;
            this.pubPem  = pubPem;
        }
    }

    // ── AES-256-CBC ───────────────────────────────────────────────────── //

    /** AES-256-CBC symmetric encryption. */
    public static final class AES implements AutoCloseable {
        private final Lib     lib = Lib.INSTANCE;
        private final byte[]  key;

        public AES(byte[] key) {
            this.key = key.clone();
        }

        /** Encrypt {@code data}. Returns IV (16 B) + ciphertext. */
        public byte[] encrypt(byte[] data) {
            LongByReference outLen = new LongByReference();
            Pointer ptr = lib.zsys_aes_encrypt(key, key.length, data, data.length, outLen);
            if (ptr == null) throw new RuntimeException("zsys_aes_encrypt failed");
            return readAndFree(ptr, outLen.getValue());
        }

        /** Decrypt AES-256-CBC ciphertext produced by {@link #encrypt}. */
        public byte[] decrypt(byte[] data) {
            LongByReference outLen = new LongByReference();
            Pointer ptr = lib.zsys_aes_decrypt(key, key.length, data, data.length, outLen);
            if (ptr == null) throw new RuntimeException("zsys_aes_decrypt failed");
            return readAndFree(ptr, outLen.getValue());
        }

        @Override public void close() { /* key is JVM-managed */ }
    }

    // ── RSA-OAEP ─────────────────────────────────────────────────────── //

    /** RSA-OAEP (SHA-256) asymmetric encryption. */
    public static final class RSA implements AutoCloseable {
        private final Lib lib = Lib.INSTANCE;

        /** Generate RSA key pair of {@code bits} size. */
        public KeyPair generate(int bits) {
            PointerByReference pubRef  = new PointerByReference();
            Pointer            privPtr = lib.zsys_rsa_generate(bits, pubRef);
            if (privPtr == null) throw new RuntimeException("zsys_rsa_generate failed");
            String privPem = privPtr.getString(0);
            String pubPem  = pubRef.getValue().getString(0);
            lib.free(privPtr);
            lib.free(pubRef.getValue());
            return new KeyPair(privPem, pubPem);
        }

        /** Encrypt {@code data} with RSA-OAEP using PEM public key. */
        public byte[] encrypt(String pubPem, byte[] data) {
            LongByReference outLen = new LongByReference();
            Pointer ptr = lib.zsys_rsa_encrypt(pubPem, data, data.length, outLen);
            if (ptr == null) throw new RuntimeException("zsys_rsa_encrypt failed");
            return readAndFree(ptr, outLen.getValue());
        }

        /** Decrypt RSA-OAEP ciphertext with PEM private key. */
        public byte[] decrypt(String privPem, byte[] data) {
            LongByReference outLen = new LongByReference();
            Pointer ptr = lib.zsys_rsa_decrypt(privPem, data, data.length, outLen);
            if (ptr == null) throw new RuntimeException("zsys_rsa_decrypt failed");
            return readAndFree(ptr, outLen.getValue());
        }

        @Override public void close() {}
    }

    // ── ECC (ECDH P-256 + AES-256-GCM) ──────────────────────────────── //

    /**
     * ECDH P-256 + AES-256-GCM hybrid encryption.
     *
     * <p>Ciphertext layout: eph_pub (65 B) + nonce (12 B) + ciphertext + GCM tag (16 B).
     */
    public static final class ECC implements AutoCloseable {
        private final Lib lib = Lib.INSTANCE;

        /** Generate EC P-256 key pair. */
        public KeyPair generate() {
            PointerByReference pubRef  = new PointerByReference();
            Pointer            privPtr = lib.zsys_ecc_generate(pubRef);
            if (privPtr == null) throw new RuntimeException("zsys_ecc_generate failed");
            String privPem = privPtr.getString(0);
            String pubPem  = pubRef.getValue().getString(0);
            lib.free(privPtr);
            lib.free(pubRef.getValue());
            return new KeyPair(privPem, pubPem);
        }

        /** Encrypt {@code data} with ECDH + AES-256-GCM using PEM public key. */
        public byte[] encrypt(String pubPem, byte[] data) {
            LongByReference outLen = new LongByReference();
            Pointer ptr = lib.zsys_ecc_encrypt(pubPem, data, data.length, outLen);
            if (ptr == null) throw new RuntimeException("zsys_ecc_encrypt failed");
            return readAndFree(ptr, outLen.getValue());
        }

        /** Decrypt ECDH + AES-256-GCM ciphertext with PEM private key. */
        public byte[] decrypt(String privPem, byte[] data) {
            LongByReference outLen = new LongByReference();
            Pointer ptr = lib.zsys_ecc_decrypt(privPem, data, data.length, outLen);
            if (ptr == null) throw new RuntimeException("zsys_ecc_decrypt failed");
            return readAndFree(ptr, outLen.getValue());
        }

        @Override public void close() {}
    }
}
