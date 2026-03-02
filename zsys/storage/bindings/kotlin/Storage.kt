/**
 * Kotlin JNA bindings for zsys/storage (ZsysKV key-value store).
 *
 * Add to build.gradle.kts:
 *   implementation("net.java.dev.jna:jna:5.14.0")
 */

package zsys.storage

import com.sun.jna.*
import com.sun.jna.ptr.PointerByReference

// ── JNA library interface ─────────────────────────────────────────────────────

internal interface ZsysStorageLib : Library {

    /** Callback type used by zsys_kv_foreach. */
    fun interface KVIterFn : Callback {
        fun invoke(key: String, value: String, ctx: Pointer?): Int
    }

    fun zsys_kv_new(initialCap: Long): Pointer?
    fun zsys_kv_free(kv: Pointer?)
    fun zsys_kv_set(kv: Pointer?, key: String, value: String): Int
    fun zsys_kv_get(kv: Pointer?, key: String): String?
    fun zsys_kv_del(kv: Pointer?, key: String): Int
    fun zsys_kv_has(kv: Pointer?, key: String): Int
    fun zsys_kv_count(kv: Pointer?): Long
    fun zsys_kv_clear(kv: Pointer?)
    fun zsys_kv_foreach(kv: Pointer?, fn: KVIterFn, ctx: Pointer?)
    fun zsys_kv_to_json(kv: Pointer?): Pointer?
    fun zsys_kv_from_json(kv: Pointer?, json: String): Int
    fun zsys_free(ptr: Pointer?)

    companion object {
        val INSTANCE: ZsysStorageLib by lazy {
            Native.load("zsys_storage", ZsysStorageLib::class.java)
        }
    }
}

// ── Safe Kotlin wrapper ───────────────────────────────────────────────────────

/**
 * In-memory key-value store backed by a native ZsysKV instance.
 *
 * Implements [AutoCloseable]; use inside `use { }` to ensure the native
 * handle is freed deterministically.
 *
 * ```kotlin
 * ZsysStorage.KV().use { kv ->
 *     kv["greeting"] = "hello"
 *     println(kv["greeting"]) // hello
 * }
 * ```
 */
class KV @JvmOverloads constructor(initialCap: Long = 0L) : AutoCloseable {

    private val lib = ZsysStorageLib.INSTANCE
    private var ptr: Pointer = lib.zsys_kv_new(initialCap)
        ?: throw OutOfMemoryError("zsys_kv_new returned null")

    // ── MutableMap-like interface ─────────────────────────────────────────

    /** Insert or update a key-value pair. */
    operator fun set(key: String, value: String) {
        val rc = lib.zsys_kv_set(ptr, key, value)
        if (rc != 0) throw OutOfMemoryError("zsys_kv_set failed for key '$key'")
    }

    /**
     * Retrieve a value by key.
     * @throws NoSuchElementException if the key is not present.
     */
    operator fun get(key: String): String =
        lib.zsys_kv_get(ptr, key) ?: throw NoSuchElementException("Key not found: '$key'")

    /** Returns the value or null if absent. */
    fun getOrNull(key: String): String? = lib.zsys_kv_get(ptr, key)

    /** Delete a key. @throws NoSuchElementException if not found. */
    fun del(key: String) {
        val rc = lib.zsys_kv_del(ptr, key)
        if (rc != 0) throw NoSuchElementException("Key not found: '$key'")
    }

    /** Returns true if the key exists. */
    operator fun contains(key: String): Boolean = lib.zsys_kv_has(ptr, key) == 1

    /** Number of entries in the store. */
    fun count(): Long = lib.zsys_kv_count(ptr)

    /** Remove all entries. */
    fun clear() = lib.zsys_kv_clear(ptr)

    // ── Iteration ─────────────────────────────────────────────────────────

    /**
     * Iterate over all key-value pairs.
     * Return `false` from [block] to stop iteration early.
     */
    fun forEach(block: (key: String, value: String) -> Boolean) {
        lib.zsys_kv_foreach(ptr, ZsysStorageLib.KVIterFn { k, v, _ ->
            if (block(k, v)) 0 else 1
        }, null)
    }

    /** Collect all key-value pairs into a [Map]. */
    fun items(): Map<String, String> {
        val result = mutableMapOf<String, String>()
        forEach { k, v -> result[k] = v; true }
        return result
    }

    // ── Serialisation ─────────────────────────────────────────────────────

    /** Serialise the store to a JSON string. */
    fun toJson(): String {
        val raw = lib.zsys_kv_to_json(ptr)
            ?: throw RuntimeException("zsys_kv_to_json failed")
        return try {
            raw.getString(0)
        } finally {
            lib.zsys_free(raw)
        }
    }

    /** Deserialise and merge a JSON string into this store. */
    fun fromJson(json: String) {
        val rc = lib.zsys_kv_from_json(ptr, json)
        if (rc != 0) throw IllegalArgumentException("zsys_kv_from_json: parse error")
    }

    // ── Lifecycle ─────────────────────────────────────────────────────────

    override fun close() {
        lib.zsys_kv_free(ptr)
        // Prevent double-free if close() is called again.
        ptr = Pointer.NULL
    }
}
