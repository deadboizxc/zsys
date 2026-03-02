/**
 * zsys_core.vapi — Vala API bindings for libzsys_core.
 *
 * Covers ZsysUser, ZsysChat (+ ZsysChatType), and ZsysClientConfig (+ ZsysClientMode).
 * All three types are [Compact] classes that own their C heap allocation.
 *
 * Link flags:  valac --pkg zsys_core  (requires a .pc file), or pass
 *              -X -lzsys_core  manually.
 */

[CCode (cheader_filename = "zsys_user.h,zsys_chat.h,zsys_client.h",
        lower_case_cprefix = "zsys_",
        cprefix = "Zsys")]
namespace Zsys {

    /* ══════════════════════════ Enumerations ═══════════════════════════════ */

    [CCode (cname = "ZsysChatType", cprefix = "ZSYS_CHAT_", has_type_id = false)]
    public enum ChatType {
        PRIVATE,
        GROUP,
        SUPERGROUP,
        CHANNEL,
        BOT;

        [CCode (cname = "zsys_chat_type_str")]
        public unowned string to_string ();
    }

    [CCode (cname = "ZsysClientMode", cprefix = "ZSYS_CLIENT_", has_type_id = false)]
    public enum ClientMode {
        USER,
        BOT
    }

    /* ══════════════════════════ ZsysUser ═══════════════════════════════════ */

    /**
     * Represents a Telegram user or bot account.
     *
     * Heap-allocated; ownership transferred to this wrapper.
     * Free automatically when the last reference drops (Compact class semantics).
     */
    [CCode (cname = "ZsysUser", free_function = "zsys_user_free", has_type_id = false)]
    [Compact]
    public class User {
        /** Unique Telegram user ID. */
        public int64 id;

        /** @username without '@', or null. */
        public unowned string? username;

        /** First name (always present). */
        public unowned string? first_name;

        /** Last name, or null. */
        public unowned string? last_name;

        /** Phone number, or null. */
        public unowned string? phone;

        /** IETF language tag, e.g. "ru". */
        public unowned string? lang_code;

        /** 1 if this is a bot account. */
        public int is_bot;

        /** 1 if the user has Telegram Premium. */
        public int is_premium;

        /** Unix timestamp of record creation (0 = unknown). */
        public int64 created_at;

        /** Allocate a new zero-initialised User. */
        [CCode (cname = "zsys_user_new")]
        public User ();

        /** Shallow-copy src into this instance (strings are strdup-ed). */
        [CCode (cname = "zsys_user_copy")]
        public int copy (User src);

        [CCode (cname = "zsys_user_set_username")]
        public int set_username (string? val);

        [CCode (cname = "zsys_user_set_first_name")]
        public int set_first_name (string val);

        [CCode (cname = "zsys_user_set_last_name")]
        public int set_last_name (string? val);

        [CCode (cname = "zsys_user_set_phone")]
        public int set_phone (string? val);

        [CCode (cname = "zsys_user_set_lang_code")]
        public int set_lang_code (string? val);

        /**
         * Serialise to a JSON string.
         * The returned string is heap-allocated; call zsys_free() when done.
         */
        [CCode (cname = "zsys_user_to_json")]
        public string? to_json ();

        /**
         * Deserialise from a flat JSON string in-place.
         * Returns 0 on success, -1 on parse error.
         */
        [CCode (cname = "zsys_user_from_json")]
        public int from_json (string json);
    }

    /* ══════════════════════════ ZsysChat ═══════════════════════════════════ */

    /**
     * Represents a Telegram chat entity (private/group/supergroup/channel/bot).
     */
    [CCode (cname = "ZsysChat", free_function = "zsys_chat_free", has_type_id = false)]
    [Compact]
    public class Chat {
        /** Unique Telegram chat ID. */
        public int64 id;

        /** Chat type. */
        [CCode (cname = "type")]
        public ChatType chat_type;

        /** Chat title, or null for private chats. */
        public unowned string? title;

        /** @username without '@', or null. */
        public unowned string? username;

        /** Chat description, or null. */
        public unowned string? description;

        /** Number of members (-1 = unknown). */
        public int32 member_count;

        /** 1 if the chat is restricted. */
        public int is_restricted;

        /** 1 if Telegram flagged as scam. */
        public int is_scam;

        /** Unix timestamp of record creation. */
        public int64 created_at;

        /** Allocate a new zero-initialised Chat. */
        [CCode (cname = "zsys_chat_new")]
        public Chat ();

        /** Shallow-copy src into this instance. */
        [CCode (cname = "zsys_chat_copy")]
        public int copy (Chat src);

        [CCode (cname = "zsys_chat_set_title")]
        public int set_title (string? val);

        [CCode (cname = "zsys_chat_set_username")]
        public int set_username (string? val);

        [CCode (cname = "zsys_chat_set_description")]
        public int set_description (string? val);

        /** Serialise to a JSON string (heap-allocated; caller frees). */
        [CCode (cname = "zsys_chat_to_json")]
        public string? to_json ();

        /** Deserialise from a flat JSON string in-place. 0 = ok, -1 = error. */
        [CCode (cname = "zsys_chat_from_json")]
        public int from_json (string json);
    }

    /* ══════════════════════════ ZsysClientConfig ═══════════════════════════ */

    /**
     * All configuration required to start a Telegram client session.
     */
    [CCode (cname = "ZsysClientConfig", free_function = "zsys_client_config_free",
            has_type_id = false)]
    [Compact]
    public class ClientConfig {
        /** Telegram API ID from my.telegram.org. */
        public int32 api_id;

        /** Telegram API hash (32 hex chars). */
        public unowned string? api_hash;

        /** Session file name without extension. */
        public unowned string? session_name;

        /** User or bot mode. */
        public ClientMode mode;

        /** Phone number in international format, or null. */
        public unowned string? phone;

        /** Bot token from @BotFather, or null. */
        public unowned string? bot_token;

        /** e.g. "Samsung Galaxy S23". */
        public unowned string? device_model;

        /** e.g. "Android 14". */
        public unowned string? system_version;

        /** e.g. "1.0.0". */
        public unowned string? app_version;

        /** IETF language tag, e.g. "en". */
        public unowned string? lang_code;

        /** Telegram lang pack, e.g. "android". */
        public unowned string? lang_pack;

        /** Proxy hostname, or null. */
        public unowned string? proxy_host;

        /** Proxy port (0 = disabled). */
        public int32 proxy_port;

        /** Proxy username, or null. */
        public unowned string? proxy_user;

        /** Proxy password, or null. */
        public unowned string? proxy_pass;

        /** Max flood-wait sleep seconds (default 60). */
        public int sleep_threshold;

        /** Max concurrent workers (default 1). */
        public int max_concurrent;

        /** Allocate a new ClientConfig with sensible defaults. */
        [CCode (cname = "zsys_client_config_new")]
        public ClientConfig ();

        /** Deep-copy src into this instance. */
        [CCode (cname = "zsys_client_config_copy")]
        public int copy (ClientConfig src);

        [CCode (cname = "zsys_client_set_api_hash")]
        public int set_api_hash (string val);

        [CCode (cname = "zsys_client_set_session_name")]
        public int set_session_name (string val);

        [CCode (cname = "zsys_client_set_phone")]
        public int set_phone (string? val);

        [CCode (cname = "zsys_client_set_bot_token")]
        public int set_bot_token (string? val);

        [CCode (cname = "zsys_client_set_device_model")]
        public int set_device_model (string? val);

        [CCode (cname = "zsys_client_set_system_version")]
        public int set_system_version (string? val);

        [CCode (cname = "zsys_client_set_app_version")]
        public int set_app_version (string? val);

        [CCode (cname = "zsys_client_set_lang_code")]
        public int set_lang_code (string? val);

        [CCode (cname = "zsys_client_set_lang_pack")]
        public int set_lang_pack (string? val);

        [CCode (cname = "zsys_client_set_proxy")]
        public int set_proxy (string host, int32 port, string? user, string? pass);

        /**
         * Validate required fields.
         * @param out_err  Optional buffer for human-readable error message.
         * @param err_len  Size of out_err.
         * Returns 0 if valid, -1 if invalid.
         */
        [CCode (cname = "zsys_client_config_validate")]
        public int validate ([CCode (array_length_pos = 1.9)] char[]? out_err);

        /** Serialise to JSON (secrets not included; heap-allocated; caller frees). */
        [CCode (cname = "zsys_client_config_to_json")]
        public string? to_json ();

        /** Deserialise from JSON in-place. 0 = ok, -1 = error. */
        [CCode (cname = "zsys_client_config_from_json")]
        public int from_json (string json);
    }

    /* ══════════════════════════ Utility ════════════════════════════════════ */

    /** Free a heap-allocated string returned by to_json(). */
    [CCode (cname = "zsys_free")]
    public void free (void* ptr);
}
