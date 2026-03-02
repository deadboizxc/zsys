// Kotlin/Native cinterop definition (paste into zsys_crypto.def for kotlinc-native):
//
// headers      = zsys_crypto.h
// headerFilter = zsys_crypto.h
// compilerOpts = -I../../c/include
// linkerOpts   = -lzsys_crypto

// ─────────────────────────────────────────────────────────────────────────────
// Kotlin/JVM binding via JNA (works on any JVM without native compilation).
// Add to build.gradle.kts:
//   implementation("net.java.dev.jna:jna:5.14.0")
// ─────────────────────────────────────────────────────────────────────────────

package zsys.crypto

import com.sun.jna.Library
import com.sun.jna.Native
import com.sun.jna.Pointer
import com.sun.jna.ptr.LongByReference
import com.sun.jna.ptr.PointerByReference

private interface ZsysCryptoLib : Library {
    // AES
    fun zsys_aes_encrypt(
        key: ByteArray, keyLen: Long,
        plaintext: ByteArray, ptLen: Long,
        outLen: LongByReference,
    ): Pointer?

    fun zsys_aes_decrypt(
        key: ByteArray, keyLen: Long,
        ciphertext: ByteArray, ctLen: Long,
        outLen: LongByReference,
    ): Pointer?

    // RSA
    fun zsys_rsa_generate(keyBits: Int, pubPem: PointerByReference): Pointer?
    fun zsys_rsa_encrypt(
        pubPem: String,
        plaintext: ByteArray, ptLen: Long,
        outLen: LongByReference,
    ): Pointer?
    fun zsys_rsa_decrypt(
        privPem: String,
        ciphertext: ByteArray, ctLen: Long,
        outLen: LongByReference,
    ): Pointer?

    // ECC
    fun zsys_ecc_generate(pubPem: PointerByReference): Pointer?
    fun zsys_ecc_encrypt(
        pubPem: String,
        plaintext: ByteArray, ptLen: Long,
        outLen: LongByReference,
    ): Pointer?
    fun zsys_ecc_decrypt(
        privPem: String,
        ciphertext: ByteArray, ctLen: Long,
        outLen: LongByReference,
    ): Pointer?

    fun free(ptr: Pointer)

    companion object {
        val INSTANCE: ZsysCryptoLib =
            Native.load("zsys_crypto", ZsysCryptoLib::class.java)
    }
}

// ── internal helpers ──────────────────────────────────────────────────── //

private fun Pointer.readAndFree(lib: ZsysCryptoLib, len: Long): ByteArray {
    val bytes = this.getByteArray(0, len.toInt())
    lib.free(this)
    return bytes
}

// ── AES-256-CBC ───────────────────────────────────────────────────────── //

/** AES-256-CBC symmetric encryption. Implements [AutoCloseable] for safety. */
class AES(private val key: ByteArray) : AutoCloseable {
    private val lib = ZsysCryptoLib.INSTANCE

    /** Encrypt [data]. Returns IV (16 B) + ciphertext. */
    fun encrypt(data: ByteArray): ByteArray {
        val outLen = LongByReference()
        val ptr = lib.zsys_aes_encrypt(key, key.size.toLong(), data, data.size.toLong(), outLen)
            ?: error("zsys_aes_encrypt failed")
        return ptr.readAndFree(lib, outLen.value)
    }

    /** Decrypt AES-256-CBC ciphertext produced by [encrypt]. */
    fun decrypt(data: ByteArray): ByteArray {
        val outLen = LongByReference()
        val ptr = lib.zsys_aes_decrypt(key, key.size.toLong(), data, data.size.toLong(), outLen)
            ?: error("zsys_aes_decrypt failed")
        return ptr.readAndFree(lib, outLen.value)
    }

    override fun close() { /* key is JVM-managed; nothing to free */ }
}

// ── RSA-OAEP ─────────────────────────────────────────────────────────── //

/** RSA-OAEP (SHA-256) asymmetric encryption. Implements [AutoCloseable]. */
class RSA : AutoCloseable {
    private val lib = ZsysCryptoLib.INSTANCE

    /** Generate RSA key pair. Returns Pair(privPEM, pubPEM). */
    fun generate(bits: Int = 2048): Pair<String, String> {
        val pubRef = PointerByReference()
        val privPtr = lib.zsys_rsa_generate(bits, pubRef)
            ?: error("zsys_rsa_generate failed")
        val privPem = privPtr.getString(0)
        val pubPem  = pubRef.value.getString(0)
        lib.free(privPtr)
        lib.free(pubRef.value)
        return privPem to pubPem
    }

    /** Encrypt [data] with RSA-OAEP using PEM public key. */
    fun encrypt(pubPem: String, data: ByteArray): ByteArray {
        val outLen = LongByReference()
        val ptr = lib.zsys_rsa_encrypt(pubPem, data, data.size.toLong(), outLen)
            ?: error("zsys_rsa_encrypt failed")
        return ptr.readAndFree(lib, outLen.value)
    }

    /** Decrypt RSA-OAEP ciphertext with PEM private key. */
    fun decrypt(privPem: String, data: ByteArray): ByteArray {
        val outLen = LongByReference()
        val ptr = lib.zsys_rsa_decrypt(privPem, data, data.size.toLong(), outLen)
            ?: error("zsys_rsa_decrypt failed")
        return ptr.readAndFree(lib, outLen.value)
    }

    override fun close() {}
}

// ── ECC (ECDH P-256 + AES-256-GCM) ──────────────────────────────────── //

/**
 * ECDH P-256 + AES-256-GCM hybrid encryption. Implements [AutoCloseable].
 *
 * Ciphertext layout: eph_pub (65 B) + nonce (12 B) + ciphertext + GCM tag (16 B).
 */
class ECC : AutoCloseable {
    private val lib = ZsysCryptoLib.INSTANCE

    /** Generate EC P-256 key pair. Returns Pair(privPEM, pubPEM). */
    fun generate(): Pair<String, String> {
        val pubRef = PointerByReference()
        val privPtr = lib.zsys_ecc_generate(pubRef)
            ?: error("zsys_ecc_generate failed")
        val privPem = privPtr.getString(0)
        val pubPem  = pubRef.value.getString(0)
        lib.free(privPtr)
        lib.free(pubRef.value)
        return privPem to pubPem
    }

    /** Encrypt [data] with ECDH + AES-256-GCM using PEM public key. */
    fun encrypt(pubPem: String, data: ByteArray): ByteArray {
        val outLen = LongByReference()
        val ptr = lib.zsys_ecc_encrypt(pubPem, data, data.size.toLong(), outLen)
            ?: error("zsys_ecc_encrypt failed")
        return ptr.readAndFree(lib, outLen.value)
    }

    /** Decrypt ECDH + AES-256-GCM ciphertext with PEM private key. */
    fun decrypt(privPem: String, data: ByteArray): ByteArray {
        val outLen = LongByReference()
        val ptr = lib.zsys_ecc_decrypt(privPem, data, data.size.toLong(), outLen)
            ?: error("zsys_ecc_decrypt failed")
        return ptr.readAndFree(lib, outLen.value)
    }

    override fun close() {}
}
