/**
 * ZsysCore.java — Java/JNA bindings for libzsys_core.so.
 *
 * Contains three public static classes:
 *   ZsysCore.User          — wraps ZsysUser
 *   ZsysCore.Chat          — wraps ZsysChat (+ChatType enum)
 *   ZsysCore.ClientConfig  — wraps ZsysClientConfig (+ClientMode enum)
 *
 * Dependencies:
 *   net.java.dev.jna:jna:5.14.0  (or newer)
 *
 * The shared library (libzsys_core.so) must be on LD_LIBRARY_PATH or
 * in a JNA-searchable location.
 */

package zsys.core;

import com.sun.jna.Library;
import com.sun.jna.Native;
import com.sun.jna.Pointer;

public final class ZsysCore {

    private ZsysCore() {}

    // ─── Raw JNA interface ────────────────────────────────────────────────────

    interface Lib extends Library {

        Lib INSTANCE = Native.load("zsys_core", Lib.class);

        /* ZsysUser */
        Pointer zsys_user_new();
        void    zsys_user_free(Pointer u);
        int     zsys_user_copy(Pointer dst, Pointer src);
        int     zsys_user_set_username(Pointer u, String val);
        int     zsys_user_set_first_name(Pointer u, String val);
        int     zsys_user_set_last_name(Pointer u, String val);
        int     zsys_user_set_phone(Pointer u, String val);
        int     zsys_user_set_lang_code(Pointer u, String val);
        Pointer zsys_user_to_json(Pointer u);
        int     zsys_user_from_json(Pointer u, String json);

        /* ZsysChat */
        Pointer zsys_chat_new();
        void    zsys_chat_free(Pointer c);
        int     zsys_chat_copy(Pointer dst, Pointer src);
        int     zsys_chat_set_title(Pointer c, String val);
        int     zsys_chat_set_username(Pointer c, String val);
        int     zsys_chat_set_description(Pointer c, String val);
        String  zsys_chat_type_str(int type);
        Pointer zsys_chat_to_json(Pointer c);
        int     zsys_chat_from_json(Pointer c, String json);

        /* ZsysClientConfig */
        Pointer zsys_client_config_new();
        void    zsys_client_config_free(Pointer cfg);
        int     zsys_client_config_copy(Pointer dst, Pointer src);
        int     zsys_client_set_api_hash(Pointer c, String val);
        int     zsys_client_set_session_name(Pointer c, String val);
        int     zsys_client_set_phone(Pointer c, String val);
        int     zsys_client_set_bot_token(Pointer c, String val);
        int     zsys_client_set_device_model(Pointer c, String val);
        int     zsys_client_set_system_version(Pointer c, String val);
        int     zsys_client_set_app_version(Pointer c, String val);
        int     zsys_client_set_lang_code(Pointer c, String val);
        int     zsys_client_set_lang_pack(Pointer c, String val);
        int     zsys_client_set_proxy(Pointer c, String host, int port, String user, String pass);
        int     zsys_client_config_validate(Pointer c, byte[] outErr, long errLen);
        Pointer zsys_client_config_to_json(Pointer c);
        int     zsys_client_config_from_json(Pointer c, String json);

        /* shared */
        void zsys_free(Pointer ptr);
    }

    // ─── Enumerations ─────────────────────────────────────────────────────────

    /** Mirrors ZsysChatType. */
    public enum ChatType {
        PRIVATE(0), GROUP(1), SUPERGROUP(2), CHANNEL(3), BOT(4);

        public final int value;
        ChatType(int v) { this.value = v; }

        public static ChatType fromInt(int v) {
            for (ChatType t : values()) if (t.value == v) return t;
            return PRIVATE;
        }
    }

    /** Mirrors ZsysClientMode. */
    public enum ClientMode {
        USER(0), BOT(1);

        public final int value;
        ClientMode(int v) { this.value = v; }

        public static ClientMode fromInt(int v) {
            for (ClientMode m : values()) if (m.value == v) return m;
            return USER;
        }
    }

    // ─── Struct field offsets ─────────────────────────────────────────────────
    // Based on 64-bit LP64 layout (8-byte pointer size, natural alignment).

    private static final long U_ID          = 0;
    private static final long U_USERNAME    = 8;
    private static final long U_FIRST_NAME  = 16;
    private static final long U_LAST_NAME   = 24;
    private static final long U_PHONE       = 32;
    private static final long U_LANG_CODE   = 40;
    private static final long U_IS_BOT      = 48;
    private static final long U_IS_PREMIUM  = 52;
    private static final long U_CREATED_AT  = 56;

    private static final long C_ID            = 0;
    private static final long C_TYPE          = 8;
    private static final long C_TITLE         = 16;
    private static final long C_USERNAME      = 24;
    private static final long C_DESCRIPTION   = 32;
    private static final long C_MEMBER_COUNT  = 40;
    private static final long C_IS_RESTRICTED = 44;
    private static final long C_IS_SCAM       = 48;
    private static final long C_CREATED_AT    = 56;

    private static final long CFG_API_ID          = 0;
    private static final long CFG_API_HASH        = 8;
    private static final long CFG_SESSION_NAME    = 16;
    private static final long CFG_MODE            = 24;
    private static final long CFG_PHONE           = 32;
    private static final long CFG_BOT_TOKEN       = 40;
    private static final long CFG_DEVICE_MODEL    = 48;
    private static final long CFG_SYSTEM_VERSION  = 56;
    private static final long CFG_APP_VERSION     = 64;
    private static final long CFG_LANG_CODE       = 72;
    private static final long CFG_LANG_PACK       = 80;
    private static final long CFG_PROXY_HOST      = 88;
    private static final long CFG_PROXY_PORT      = 96;
    private static final long CFG_PROXY_USER      = 104;
    private static final long CFG_PROXY_PASS      = 112;
    private static final long CFG_SLEEP_THRESHOLD = 120;
    private static final long CFG_MAX_CONCURRENT  = 124;

    // ─── helper ───────────────────────────────────────────────────────────────

    private static String readCStr(Pointer base, long offset) {
        Pointer p = base.getPointer(offset);
        return p == null ? null : p.getString(0);
    }

    private static String consumeJsonPtr(Pointer raw) {
        if (raw == null) return null;
        String s = raw.getString(0);
        Lib.INSTANCE.zsys_free(raw);
        return s;
    }

    // ═══════════════════════════════ User ════════════════════════════════════

    /**
     * Java wrapper for ZsysUser.
     * Implements {@link AutoCloseable} so it works in try-with-resources.
     */
    public static final class User implements AutoCloseable {

        private Pointer ptr;

        private User(Pointer ptr) { this.ptr = ptr; }

        /** Allocate a new zero-initialised User. */
        public static User create() {
            Pointer p = Lib.INSTANCE.zsys_user_new();
            if (p == null) throw new OutOfMemoryError("zsys_user_new() returned NULL");
            return new User(p);
        }

        /** Deserialise from a JSON string. */
        public static User fromJson(String json) {
            User u = create();
            if (Lib.INSTANCE.zsys_user_from_json(u.ptr, json) != 0) {
                u.close();
                throw new IllegalArgumentException("zsys_user_from_json() parse error");
            }
            return u;
        }

        @Override
        public void close() {
            if (ptr != null) {
                Lib.INSTANCE.zsys_user_free(ptr);
                ptr = null;
            }
        }

        // ── getters / setters ────────────────────────────────────────────────

        public long getId()            { return ptr.getLong(U_ID); }
        public void setId(long v)      { ptr.setLong(U_ID, v); }

        public String getUsername()    { return readCStr(ptr, U_USERNAME); }
        public void setUsername(String v) { Lib.INSTANCE.zsys_user_set_username(ptr, v); }

        public String getFirstName()   { return readCStr(ptr, U_FIRST_NAME); }
        public void setFirstName(String v) { Lib.INSTANCE.zsys_user_set_first_name(ptr, v); }

        public String getLastName()    { return readCStr(ptr, U_LAST_NAME); }
        public void setLastName(String v) { Lib.INSTANCE.zsys_user_set_last_name(ptr, v); }

        public String getPhone()       { return readCStr(ptr, U_PHONE); }
        public void setPhone(String v) { Lib.INSTANCE.zsys_user_set_phone(ptr, v); }

        public String getLangCode()    { return readCStr(ptr, U_LANG_CODE); }
        public void setLangCode(String v) { Lib.INSTANCE.zsys_user_set_lang_code(ptr, v); }

        public boolean isBot()         { return ptr.getInt(U_IS_BOT) != 0; }
        public void setBot(boolean v)  { ptr.setInt(U_IS_BOT, v ? 1 : 0); }

        public boolean isPremium()     { return ptr.getInt(U_IS_PREMIUM) != 0; }
        public void setPremium(boolean v) { ptr.setInt(U_IS_PREMIUM, v ? 1 : 0); }

        public long getCreatedAt()        { return ptr.getLong(U_CREATED_AT); }
        public void setCreatedAt(long v)  { ptr.setLong(U_CREATED_AT, v); }

        // ── serialisation ────────────────────────────────────────────────────

        public String toJson() {
            String s = consumeJsonPtr(Lib.INSTANCE.zsys_user_to_json(ptr));
            if (s == null) throw new RuntimeException("zsys_user_to_json() failed");
            return s;
        }

        @Override
        public String toString() {
            return "User{id=" + getId() + ", username=" + getUsername()
                   + ", firstName=" + getFirstName() + "}";
        }
    }

    // ═══════════════════════════════ Chat ════════════════════════════════════

    /**
     * Java wrapper for ZsysChat.
     */
    public static final class Chat implements AutoCloseable {

        private Pointer ptr;

        private Chat(Pointer ptr) { this.ptr = ptr; }

        public static Chat create() {
            Pointer p = Lib.INSTANCE.zsys_chat_new();
            if (p == null) throw new OutOfMemoryError("zsys_chat_new() returned NULL");
            return new Chat(p);
        }

        public static Chat fromJson(String json) {
            Chat c = create();
            if (Lib.INSTANCE.zsys_chat_from_json(c.ptr, json) != 0) {
                c.close();
                throw new IllegalArgumentException("zsys_chat_from_json() parse error");
            }
            return c;
        }

        @Override
        public void close() {
            if (ptr != null) {
                Lib.INSTANCE.zsys_chat_free(ptr);
                ptr = null;
            }
        }

        // ── getters / setters ────────────────────────────────────────────────

        public long getId()           { return ptr.getLong(C_ID); }
        public void setId(long v)     { ptr.setLong(C_ID, v); }

        public ChatType getType()     { return ChatType.fromInt(ptr.getInt(C_TYPE)); }
        public void setType(ChatType v) { ptr.setInt(C_TYPE, v.value); }

        public String getTypeStr() {
            return Lib.INSTANCE.zsys_chat_type_str(ptr.getInt(C_TYPE));
        }

        public String getTitle()      { return readCStr(ptr, C_TITLE); }
        public void setTitle(String v) { Lib.INSTANCE.zsys_chat_set_title(ptr, v); }

        public String getUsername()   { return readCStr(ptr, C_USERNAME); }
        public void setUsername(String v) { Lib.INSTANCE.zsys_chat_set_username(ptr, v); }

        public String getDescription()   { return readCStr(ptr, C_DESCRIPTION); }
        public void setDescription(String v) { Lib.INSTANCE.zsys_chat_set_description(ptr, v); }

        public int getMemberCount()   { return ptr.getInt(C_MEMBER_COUNT); }
        public void setMemberCount(int v) { ptr.setInt(C_MEMBER_COUNT, v); }

        public boolean isRestricted() { return ptr.getInt(C_IS_RESTRICTED) != 0; }
        public boolean isScam()       { return ptr.getInt(C_IS_SCAM) != 0; }

        public long getCreatedAt()    { return ptr.getLong(C_CREATED_AT); }

        // ── serialisation ────────────────────────────────────────────────────

        public String toJson() {
            String s = consumeJsonPtr(Lib.INSTANCE.zsys_chat_to_json(ptr));
            if (s == null) throw new RuntimeException("zsys_chat_to_json() failed");
            return s;
        }

        @Override
        public String toString() {
            return "Chat{id=" + getId() + ", type=" + getType().name()
                   + ", title=" + getTitle() + "}";
        }
    }

    // ═══════════════════════════════ ClientConfig ═════════════════════════════

    /**
     * Java wrapper for ZsysClientConfig.
     */
    public static final class ClientConfig implements AutoCloseable {

        private Pointer ptr;

        private ClientConfig(Pointer ptr) { this.ptr = ptr; }

        public static ClientConfig create() {
            Pointer p = Lib.INSTANCE.zsys_client_config_new();
            if (p == null) throw new OutOfMemoryError("zsys_client_config_new() returned NULL");
            return new ClientConfig(p);
        }

        public static ClientConfig fromJson(String json) {
            ClientConfig cfg = create();
            if (Lib.INSTANCE.zsys_client_config_from_json(cfg.ptr, json) != 0) {
                cfg.close();
                throw new IllegalArgumentException("zsys_client_config_from_json() parse error");
            }
            return cfg;
        }

        @Override
        public void close() {
            if (ptr != null) {
                Lib.INSTANCE.zsys_client_config_free(ptr);
                ptr = null;
            }
        }

        // ── getters / setters ────────────────────────────────────────────────

        public int getApiId()           { return ptr.getInt(CFG_API_ID); }
        public void setApiId(int v)     { ptr.setInt(CFG_API_ID, v); }

        public String getApiHash()      { return readCStr(ptr, CFG_API_HASH); }
        public void setApiHash(String v) { Lib.INSTANCE.zsys_client_set_api_hash(ptr, v); }

        public String getSessionName()  { return readCStr(ptr, CFG_SESSION_NAME); }
        public void setSessionName(String v) { Lib.INSTANCE.zsys_client_set_session_name(ptr, v); }

        public ClientMode getMode()     { return ClientMode.fromInt(ptr.getInt(CFG_MODE)); }
        public void setMode(ClientMode v) { ptr.setInt(CFG_MODE, v.value); }

        public String getPhone()        { return readCStr(ptr, CFG_PHONE); }
        public void setPhone(String v)  { Lib.INSTANCE.zsys_client_set_phone(ptr, v); }

        public String getBotToken()     { return readCStr(ptr, CFG_BOT_TOKEN); }
        public void setBotToken(String v) { Lib.INSTANCE.zsys_client_set_bot_token(ptr, v); }

        public String getDeviceModel()  { return readCStr(ptr, CFG_DEVICE_MODEL); }
        public void setDeviceModel(String v) { Lib.INSTANCE.zsys_client_set_device_model(ptr, v); }

        public String getSystemVersion() { return readCStr(ptr, CFG_SYSTEM_VERSION); }
        public void setSystemVersion(String v) { Lib.INSTANCE.zsys_client_set_system_version(ptr, v); }

        public String getAppVersion()   { return readCStr(ptr, CFG_APP_VERSION); }
        public void setAppVersion(String v) { Lib.INSTANCE.zsys_client_set_app_version(ptr, v); }

        public String getLangCode()     { return readCStr(ptr, CFG_LANG_CODE); }
        public void setLangCode(String v) { Lib.INSTANCE.zsys_client_set_lang_code(ptr, v); }

        public String getLangPack()     { return readCStr(ptr, CFG_LANG_PACK); }
        public void setLangPack(String v) { Lib.INSTANCE.zsys_client_set_lang_pack(ptr, v); }

        public String getProxyHost()    { return readCStr(ptr, CFG_PROXY_HOST); }
        public int getProxyPort()       { return ptr.getInt(CFG_PROXY_PORT); }
        public String getProxyUser()    { return readCStr(ptr, CFG_PROXY_USER); }

        public void setProxy(String host, int port, String user, String pass) {
            Lib.INSTANCE.zsys_client_set_proxy(ptr, host, port, user, pass);
        }

        public int getSleepThreshold()     { return ptr.getInt(CFG_SLEEP_THRESHOLD); }
        public void setSleepThreshold(int v) { ptr.setInt(CFG_SLEEP_THRESHOLD, v); }

        public int getMaxConcurrent()      { return ptr.getInt(CFG_MAX_CONCURRENT); }
        public void setMaxConcurrent(int v) { ptr.setInt(CFG_MAX_CONCURRENT, v); }

        // ── validation / serialisation ───────────────────────────────────────

        /**
         * @throws IllegalStateException if required fields are missing.
         */
        public void validate() {
            byte[] buf = new byte[256];
            int rc = Lib.INSTANCE.zsys_client_config_validate(ptr, buf, 256L);
            if (rc != 0) {
                String msg = new String(buf).trim().replace("\0", "");
                throw new IllegalStateException("invalid config: " + msg);
            }
        }

        public String toJson() {
            String s = consumeJsonPtr(Lib.INSTANCE.zsys_client_config_to_json(ptr));
            if (s == null) throw new RuntimeException("zsys_client_config_to_json() failed");
            return s;
        }

        @Override
        public String toString() {
            return "ClientConfig{apiId=" + getApiId() + ", session=" + getSessionName()
                   + ", mode=" + getMode().name() + "}";
        }
    }
}
