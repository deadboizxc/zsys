/**
 * zsys modules bindings — Kotlin/JNA
 *
 * Wraps ZsysRouter and ZsysRegistry from libzsys_core.so.
 *
 * Dependency (Maven):
 *   <dependency>
 *     <groupId>net.java.dev.jna</groupId>
 *     <artifactId>jna</artifactId>
 *     <version>5.14.0</version>
 *   </dependency>
 */

package zsys.modules

import com.sun.jna.Library
import com.sun.jna.Native
import com.sun.jna.Pointer
import com.sun.jna.Memory

// ── JNA interface ─────────────────────────────────────────────────────────

internal interface ZsysCoreLib : Library {
    // Router
    fun zsys_router_new(): Pointer?
    fun zsys_router_free(r: Pointer)
    fun zsys_router_add(r: Pointer, trigger: String, handler_id: Int): Int
    fun zsys_router_remove(r: Pointer, trigger: String): Int
    fun zsys_router_lookup(r: Pointer, trigger: String): Int
    fun zsys_router_count(r: Pointer): Long
    fun zsys_router_clear(r: Pointer)

    // Registry
    fun zsys_registry_new(): Pointer?
    fun zsys_registry_free(reg: Pointer)
    fun zsys_registry_register(reg: Pointer, name: String, handler_id: Int,
                                description: String?, category: String?): Int
    fun zsys_registry_unregister(reg: Pointer, name: String): Int
    fun zsys_registry_get(reg: Pointer, name: String): Int
    fun zsys_registry_info(reg: Pointer, name: String,
                           out_desc: Memory?, desc_len: Long,
                           out_cat: Memory?,  cat_len: Long): Int
    fun zsys_registry_count(reg: Pointer): Long
    fun zsys_registry_name_at(reg: Pointer, i: Long): Pointer?
}

private val lib: ZsysCoreLib by lazy {
    Native.load("zsys_core", ZsysCoreLib::class.java)
}

// ── exceptions ────────────────────────────────────────────────────────────

class ZsysException(message: String) : RuntimeException(message)

// ── Router ────────────────────────────────────────────────────────────────

/**
 * Trigger → handler_id open-addressing hash table.
 * Lookup is case-insensitive.
 * Implements [AutoCloseable] — use with `use {}` or call [close] manually.
 */
class Router : AutoCloseable {
    private var ptr: Pointer

    init {
        ptr = lib.zsys_router_new()
            ?: throw ZsysException("zsys_router_new() returned null")
    }

    /** Add or update a trigger → handler_id mapping. */
    fun add(trigger: String, handlerId: Int) {
        if (lib.zsys_router_add(ptr, trigger, handlerId) != 0)
            throw ZsysException("zsys_router_add failed for trigger: $trigger")
    }

    /**
     * Remove a trigger.
     * @return true if it existed, false otherwise.
     */
    fun remove(trigger: String): Boolean = lib.zsys_router_remove(ptr, trigger) == 0

    /**
     * Look up handler_id for trigger (case-insensitive).
     * @return handler_id or -1 if not found.
     */
    fun lookup(trigger: String): Int = lib.zsys_router_lookup(ptr, trigger)

    /** Number of registered triggers. */
    fun count(): Long = lib.zsys_router_count(ptr)

    /** Remove all entries. */
    fun clear() = lib.zsys_router_clear(ptr)

    /** True if trigger is registered. */
    operator fun contains(trigger: String): Boolean = lookup(trigger) != -1

    override fun close() {
        lib.zsys_router_free(ptr)
    }
}

// ── Registry ──────────────────────────────────────────────────────────────

/** Metadata returned by [Registry.info]. */
data class HandlerInfo(val description: String, val category: String)

/**
 * Dynamic array of name → handler_id entries with optional
 * description and category metadata.
 * Implements [AutoCloseable] — use with `use {}` or call [close] manually.
 */
class Registry : AutoCloseable {
    private var ptr: Pointer

    init {
        ptr = lib.zsys_registry_new()
            ?: throw ZsysException("zsys_registry_new() returned null")
    }

    /**
     * Register a handler. [description] and [category] are optional (null).
     */
    fun register(name: String, handlerId: Int,
                 description: String? = null, category: String? = null) {
        if (lib.zsys_registry_register(ptr, name, handlerId, description, category) != 0)
            throw ZsysException("zsys_registry_register failed for: $name")
    }

    /**
     * Unregister by name.
     * @return true if it existed.
     */
    fun unregister(name: String): Boolean =
        lib.zsys_registry_unregister(ptr, name) == 0

    /**
     * Return handler_id for name, or -1 if not found.
     */
    fun get(name: String): Int = lib.zsys_registry_get(ptr, name)

    /**
     * Return [HandlerInfo] for a registered name.
     * @throws ZsysException if not found.
     */
    fun info(name: String): HandlerInfo {
        val descBuf = Memory(256)
        val catBuf  = Memory(128)
        val rc = lib.zsys_registry_info(ptr, name, descBuf, 256L, catBuf, 128L)
        if (rc != 0) throw ZsysException("zsys_registry_info: not found: $name")
        return HandlerInfo(
            description = descBuf.getString(0),
            category    = catBuf.getString(0),
        )
    }

    /** Number of registered entries. */
    fun count(): Long = lib.zsys_registry_count(ptr)

    /**
     * Name at index [i], or null if out of bounds.
     */
    fun nameAt(i: Long): String? =
        lib.zsys_registry_name_at(ptr, i)?.getString(0)

    /** All registered handler names. */
    fun names(): List<String> {
        val n = count()
        return (0 until n).mapNotNull { nameAt(it) }
    }

    /** True if name is registered. */
    operator fun contains(name: String): Boolean = get(name) != -1

    override fun close() {
        lib.zsys_registry_free(ptr)
    }
}
