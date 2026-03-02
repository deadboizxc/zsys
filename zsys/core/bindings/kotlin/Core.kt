/**
 * zsys.core Kotlin/JNA bindings — ZsysUser, ZsysChat, ZsysClientConfig.
 *
 * Requires JNA on the classpath:
 *   implementation("net.java.dev.jna:jna:5.14.0")
 *
 * The shared library (libzsys_core.so) must be on LD_LIBRARY_PATH or
 * in a JNA-searchable path.
 */

package zsys.core

import com.sun.jna.Library
import com.sun.jna.Native
import com.sun.jna.Pointer
import com.sun.jna.Structure
import com.sun.jna.ptr.IntByReference

// ─── JNA interface (raw C bindings) ──────────────────────────────────────────

internal interface ZsysCoreLib : Library {

    // ── ZsysUser ──────────────────────────────────────────────────────────
    fun zsys_user_new(): Pointer?
    fun zsys_user_free(u: Pointer?)
    fun zsys_user_copy(dst: Pointer?, src: Pointer?): Int
    fun zsys_user_set_username(u: Pointer?, `val`: String?): Int
    fun zsys_user_set_first_name(u: Pointer?, `val`: String?): Int
    fun zsys_user_set_last_name(u: Pointer?, `val`: String?): Int
    fun zsys_user_set_phone(u: Pointer?, `val`: String?): Int
    fun zsys_user_set_lang_code(u: Pointer?, `val`: String?): Int
    fun zsys_user_to_json(u: Pointer?): Pointer?
    fun zsys_user_from_json(u: Pointer?, json: String?): Int

    // ── ZsysChat ──────────────────────────────────────────────────────────
    fun zsys_chat_new(): Pointer?
    fun zsys_chat_free(c: Pointer?)
    fun zsys_chat_copy(dst: Pointer?, src: Pointer?): Int
    fun zsys_chat_set_title(c: Pointer?, `val`: String?): Int
    fun zsys_chat_set_username(c: Pointer?, `val`: String?): Int
    fun zsys_chat_set_description(c: Pointer?, `val`: String?): Int
    fun zsys_chat_type_str(type: Int): String?
    fun zsys_chat_to_json(c: Pointer?): Pointer?
    fun zsys_chat_from_json(c: Pointer?, json: String?): Int

    // ── ZsysClientConfig ──────────────────────────────────────────────────
    fun zsys_client_config_new(): Pointer?
    fun zsys_client_config_free(cfg: Pointer?)
    fun zsys_client_config_copy(dst: Pointer?, src: Pointer?): Int
    fun zsys_client_set_api_hash(c: Pointer?, `val`: String?): Int
    fun zsys_client_set_session_name(c: Pointer?, `val`: String?): Int
    fun zsys_client_set_phone(c: Pointer?, `val`: String?): Int
    fun zsys_client_set_bot_token(c: Pointer?, `val`: String?): Int
    fun zsys_client_set_device_model(c: Pointer?, `val`: String?): Int
    fun zsys_client_set_system_version(c: Pointer?, `val`: String?): Int
    fun zsys_client_set_app_version(c: Pointer?, `val`: String?): Int
    fun zsys_client_set_lang_code(c: Pointer?, `val`: String?): Int
    fun zsys_client_set_lang_pack(c: Pointer?, `val`: String?): Int
    fun zsys_client_set_proxy(
        c: Pointer?,
        host: String?,
        port: Int,
        user: String?,
        pass: String?
    ): Int
    fun zsys_client_config_validate(c: Pointer?, outErr: ByteArray?, errLen: Long): Int
    fun zsys_client_config_to_json(c: Pointer?): Pointer?
    fun zsys_client_config_from_json(c: Pointer?, json: String?): Int

    // ── shared ────────────────────────────────────────────────────────────
    fun zsys_free(ptr: Pointer?)

    companion object {
        val INSTANCE: ZsysCoreLib by lazy {
            Native.load("zsys_core", ZsysCoreLib::class.java) as ZsysCoreLib
        }
    }
}

// ─── Enumerations ─────────────────────────────────────────────────────────────

/** Mirrors ZsysChatType. */
enum class ChatType(val value: Int) {
    PRIVATE(0),
    GROUP(1),
    SUPERGROUP(2),
    CHANNEL(3),
    BOT(4);

    companion object {
        fun fromInt(v: Int) = entries.firstOrNull { it.value == v } ?: PRIVATE
    }
}

/** Mirrors ZsysClientMode. */
enum class ClientMode(val value: Int) {
    USER(0),
    BOT(1);

    companion object {
        fun fromInt(v: Int) = entries.firstOrNull { it.value == v } ?: USER
    }
}

// ─── helpers ──────────────────────────────────────────────────────────────────

private val lib get() = ZsysCoreLib.INSTANCE

/** Read a JNA Pointer as a C string, then free it with zsys_free(). */
private fun Pointer.readAndFreeString(): String {
    val s = getString(0)
    lib.zsys_free(this)
    return s
}

/** Struct field offsets for ZsysUser (matches the C layout). */
private object UserOffsets {
    const val ID          = 0L
    const val USERNAME    = 8L
    const val FIRST_NAME  = 16L
    const val LAST_NAME   = 24L
    const val PHONE       = 32L
    const val LANG_CODE   = 40L
    const val IS_BOT      = 48L
    const val IS_PREMIUM  = 52L
    const val CREATED_AT  = 56L   // 4 bytes padding before this on 64-bit
}

/** Struct field offsets for ZsysChat. */
private object ChatOffsets {
    const val ID            = 0L
    const val TYPE          = 8L
    const val TITLE         = 16L
    const val USERNAME      = 24L
    const val DESCRIPTION   = 32L
    const val MEMBER_COUNT  = 40L
    const val IS_RESTRICTED = 44L
    const val IS_SCAM       = 48L
    const val CREATED_AT    = 56L
}

/** Struct field offsets for ZsysClientConfig. */
private object CfgOffsets {
    const val API_ID          = 0L
    const val API_HASH        = 8L
    const val SESSION_NAME    = 16L
    const val MODE            = 24L
    const val PHONE           = 32L
    const val BOT_TOKEN       = 40L
    const val DEVICE_MODEL    = 48L
    const val SYSTEM_VERSION  = 56L
    const val APP_VERSION     = 64L
    const val LANG_CODE       = 72L
    const val LANG_PACK       = 80L
    const val PROXY_HOST      = 88L
    const val PROXY_PORT      = 96L
    const val PROXY_USER      = 104L
    const val PROXY_PASS      = 112L
    const val SLEEP_THRESHOLD = 120L
    const val MAX_CONCURRENT  = 124L
}

private fun Pointer.readCStr(offset: Long): String? =
    getPointer(offset)?.getString(0)

// ═══════════════════════════════ User ════════════════════════════════════════

/**
 * Kotlin wrapper for ZsysUser.
 *
 * Owns the underlying C heap allocation; call [close] (or use `use {}`)
 * to free it explicitly, or let the finalizer handle it.
 */
class User private constructor(private var ptr: Pointer) : AutoCloseable {

    companion object {
        /** Allocate a new zero-initialised User. */
        fun create(): User {
            val p = lib.zsys_user_new() ?: throw OutOfMemoryError("zsys_user_new() returned NULL")
            return User(p)
        }

        /** Deserialise from a JSON string. */
        fun fromJson(json: String): User {
            val u = create()
            if (lib.zsys_user_from_json(u.ptr, json) != 0) {
                u.close()
                throw IllegalArgumentException("zsys_user_from_json() parse error")
            }
            return u
        }
    }

    override fun close() {
        lib.zsys_user_free(ptr)
    }

    // ── properties ──────────────────────────────────────────────────────────

    var id: Long
        get() = ptr.getLong(UserOffsets.ID)
        set(v) = ptr.setLong(UserOffsets.ID, v)

    var username: String?
        get() = ptr.readCStr(UserOffsets.USERNAME)
        set(v) { lib.zsys_user_set_username(ptr, v) }

    var firstName: String?
        get() = ptr.readCStr(UserOffsets.FIRST_NAME)
        set(v) { lib.zsys_user_set_first_name(ptr, v ?: "") }

    var lastName: String?
        get() = ptr.readCStr(UserOffsets.LAST_NAME)
        set(v) { lib.zsys_user_set_last_name(ptr, v) }

    var phone: String?
        get() = ptr.readCStr(UserOffsets.PHONE)
        set(v) { lib.zsys_user_set_phone(ptr, v) }

    var langCode: String?
        get() = ptr.readCStr(UserOffsets.LANG_CODE)
        set(v) { lib.zsys_user_set_lang_code(ptr, v) }

    var isBot: Boolean
        get() = ptr.getInt(UserOffsets.IS_BOT) != 0
        set(v) = ptr.setInt(UserOffsets.IS_BOT, if (v) 1 else 0)

    var isPremium: Boolean
        get() = ptr.getInt(UserOffsets.IS_PREMIUM) != 0
        set(v) = ptr.setInt(UserOffsets.IS_PREMIUM, if (v) 1 else 0)

    var createdAt: Long
        get() = ptr.getLong(UserOffsets.CREATED_AT)
        set(v) = ptr.setLong(UserOffsets.CREATED_AT, v)

    // ── serialisation ────────────────────────────────────────────────────────

    fun toJson(): String =
        lib.zsys_user_to_json(ptr)?.readAndFreeString()
            ?: throw RuntimeException("zsys_user_to_json() failed")

    override fun toString() = "User(id=$id, username=$username, firstName=$firstName)"
}

// ═══════════════════════════════ Chat ════════════════════════════════════════

/**
 * Kotlin wrapper for ZsysChat.
 */
class Chat private constructor(private var ptr: Pointer) : AutoCloseable {

    companion object {
        fun create(): Chat {
            val p = lib.zsys_chat_new() ?: throw OutOfMemoryError("zsys_chat_new() returned NULL")
            return Chat(p)
        }

        fun fromJson(json: String): Chat {
            val c = create()
            if (lib.zsys_chat_from_json(c.ptr, json) != 0) {
                c.close()
                throw IllegalArgumentException("zsys_chat_from_json() parse error")
            }
            return c
        }
    }

    override fun close() {
        lib.zsys_chat_free(ptr)
    }

    // ── properties ──────────────────────────────────────────────────────────

    var id: Long
        get() = ptr.getLong(ChatOffsets.ID)
        set(v) = ptr.setLong(ChatOffsets.ID, v)

    var type: ChatType
        get() = ChatType.fromInt(ptr.getInt(ChatOffsets.TYPE))
        set(v) = ptr.setInt(ChatOffsets.TYPE, v.value)

    val typeStr: String
        get() = lib.zsys_chat_type_str(ptr.getInt(ChatOffsets.TYPE)) ?: "unknown"

    var title: String?
        get() = ptr.readCStr(ChatOffsets.TITLE)
        set(v) { lib.zsys_chat_set_title(ptr, v) }

    var username: String?
        get() = ptr.readCStr(ChatOffsets.USERNAME)
        set(v) { lib.zsys_chat_set_username(ptr, v) }

    var description: String?
        get() = ptr.readCStr(ChatOffsets.DESCRIPTION)
        set(v) { lib.zsys_chat_set_description(ptr, v) }

    var memberCount: Int
        get() = ptr.getInt(ChatOffsets.MEMBER_COUNT)
        set(v) = ptr.setInt(ChatOffsets.MEMBER_COUNT, v)

    val isRestricted: Boolean get() = ptr.getInt(ChatOffsets.IS_RESTRICTED) != 0
    val isScam: Boolean       get() = ptr.getInt(ChatOffsets.IS_SCAM) != 0

    val createdAt: Long get() = ptr.getLong(ChatOffsets.CREATED_AT)

    // ── serialisation ────────────────────────────────────────────────────────

    fun toJson(): String =
        lib.zsys_chat_to_json(ptr)?.readAndFreeString()
            ?: throw RuntimeException("zsys_chat_to_json() failed")

    override fun toString() = "Chat(id=$id, type=${type.name}, title=$title)"
}

// ═══════════════════════════════ ClientConfig ═════════════════════════════════

/**
 * Kotlin wrapper for ZsysClientConfig.
 */
class ClientConfig private constructor(private var ptr: Pointer) : AutoCloseable {

    companion object {
        fun create(): ClientConfig {
            val p = lib.zsys_client_config_new()
                ?: throw OutOfMemoryError("zsys_client_config_new() returned NULL")
            return ClientConfig(p)
        }

        fun fromJson(json: String): ClientConfig {
            val cfg = create()
            if (lib.zsys_client_config_from_json(cfg.ptr, json) != 0) {
                cfg.close()
                throw IllegalArgumentException("zsys_client_config_from_json() parse error")
            }
            return cfg
        }
    }

    override fun close() {
        lib.zsys_client_config_free(ptr)
    }

    // ── properties ──────────────────────────────────────────────────────────

    var apiId: Int
        get() = ptr.getInt(CfgOffsets.API_ID)
        set(v) = ptr.setInt(CfgOffsets.API_ID, v)

    var apiHash: String?
        get() = ptr.readCStr(CfgOffsets.API_HASH)
        set(v) { lib.zsys_client_set_api_hash(ptr, v ?: "") }

    var sessionName: String?
        get() = ptr.readCStr(CfgOffsets.SESSION_NAME)
        set(v) { lib.zsys_client_set_session_name(ptr, v ?: "") }

    var mode: ClientMode
        get() = ClientMode.fromInt(ptr.getInt(CfgOffsets.MODE))
        set(v) = ptr.setInt(CfgOffsets.MODE, v.value)

    var phone: String?
        get() = ptr.readCStr(CfgOffsets.PHONE)
        set(v) { lib.zsys_client_set_phone(ptr, v) }

    var botToken: String?
        get() = ptr.readCStr(CfgOffsets.BOT_TOKEN)
        set(v) { lib.zsys_client_set_bot_token(ptr, v) }

    var deviceModel: String?
        get() = ptr.readCStr(CfgOffsets.DEVICE_MODEL)
        set(v) { lib.zsys_client_set_device_model(ptr, v) }

    var systemVersion: String?
        get() = ptr.readCStr(CfgOffsets.SYSTEM_VERSION)
        set(v) { lib.zsys_client_set_system_version(ptr, v) }

    var appVersion: String?
        get() = ptr.readCStr(CfgOffsets.APP_VERSION)
        set(v) { lib.zsys_client_set_app_version(ptr, v) }

    var langCode: String?
        get() = ptr.readCStr(CfgOffsets.LANG_CODE)
        set(v) { lib.zsys_client_set_lang_code(ptr, v) }

    var langPack: String?
        get() = ptr.readCStr(CfgOffsets.LANG_PACK)
        set(v) { lib.zsys_client_set_lang_pack(ptr, v) }

    val proxyHost: String?  get() = ptr.readCStr(CfgOffsets.PROXY_HOST)
    val proxyPort: Int      get() = ptr.getInt(CfgOffsets.PROXY_PORT)
    val proxyUser: String?  get() = ptr.readCStr(CfgOffsets.PROXY_USER)

    fun setProxy(host: String, port: Int, user: String? = null, pass: String? = null) {
        lib.zsys_client_set_proxy(ptr, host, port, user, pass)
    }

    var sleepThreshold: Int
        get() = ptr.getInt(CfgOffsets.SLEEP_THRESHOLD)
        set(v) = ptr.setInt(CfgOffsets.SLEEP_THRESHOLD, v)

    var maxConcurrent: Int
        get() = ptr.getInt(CfgOffsets.MAX_CONCURRENT)
        set(v) = ptr.setInt(CfgOffsets.MAX_CONCURRENT, v)

    // ── validation / serialisation ───────────────────────────────────────────

    /** @throws IllegalStateException if required fields are missing. */
    fun validate() {
        val buf = ByteArray(256)
        val rc = lib.zsys_client_config_validate(ptr, buf, 256L)
        if (rc != 0) {
            val msg = String(buf).trimEnd('\u0000')
            throw IllegalStateException("invalid config: $msg")
        }
    }

    fun toJson(): String =
        lib.zsys_client_config_to_json(ptr)?.readAndFreeString()
            ?: throw RuntimeException("zsys_client_config_to_json() failed")

    override fun toString() = "ClientConfig(apiId=$apiId, session=$sessionName, mode=${mode.name})"
}
