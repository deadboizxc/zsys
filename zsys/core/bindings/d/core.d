/**
 * zsys.core.bindings.d.core — D language bindings for libzsys_core.
 *
 * Provides extern(C) declarations mirroring the C structs/enums/functions,
 * plus safe D wrapper classes (DUser, DChat, DClientConfig) that manage
 * heap allocation via RAII destructors.
 *
 * Compile:  dmd core.d -L-lzsys_core
 *           ldc2 core.d -L-lzsys_core
 */

module zsys.core;

import core.stdc.stdint : int32_t, int64_t;
import core.stdc.stdlib : free;
import std.string : fromStringz, toStringz;

// ─── extern(C) declarations ───────────────────────────────────────────────────

extern(C):

/* ── ZsysUser ────────────────────────────────────────────────────────────── */

struct ZsysUser {
    long    id;
    char*   username;
    char*   first_name;
    char*   last_name;
    char*   phone;
    char*   lang_code;
    int     is_bot;
    int     is_premium;
    long    created_at;
}

ZsysUser* zsys_user_new();
void      zsys_user_free(ZsysUser* u);
int       zsys_user_copy(ZsysUser* dst, const ZsysUser* src);
int       zsys_user_set_username(ZsysUser* u, const char* val);
int       zsys_user_set_first_name(ZsysUser* u, const char* val);
int       zsys_user_set_last_name(ZsysUser* u, const char* val);
int       zsys_user_set_phone(ZsysUser* u, const char* val);
int       zsys_user_set_lang_code(ZsysUser* u, const char* val);
char*     zsys_user_to_json(const ZsysUser* u);
int       zsys_user_from_json(ZsysUser* u, const char* json);

/* ── ZsysChat ────────────────────────────────────────────────────────────── */

enum ZsysChatType : int {
    ZSYS_CHAT_PRIVATE    = 0,
    ZSYS_CHAT_GROUP      = 1,
    ZSYS_CHAT_SUPERGROUP = 2,
    ZSYS_CHAT_CHANNEL    = 3,
    ZSYS_CHAT_BOT        = 4,
}

struct ZsysChat {
    long          id;
    ZsysChatType  type;
    char*         title;
    char*         username;
    char*         description;
    int32_t       member_count;
    int           is_restricted;
    int           is_scam;
    long          created_at;
}

ZsysChat*   zsys_chat_new();
void        zsys_chat_free(ZsysChat* c);
int         zsys_chat_copy(ZsysChat* dst, const ZsysChat* src);
int         zsys_chat_set_title(ZsysChat* c, const char* val);
int         zsys_chat_set_username(ZsysChat* c, const char* val);
int         zsys_chat_set_description(ZsysChat* c, const char* val);
const(char)* zsys_chat_type_str(ZsysChatType type);
char*       zsys_chat_to_json(const ZsysChat* c);
int         zsys_chat_from_json(ZsysChat* c, const char* json);

/* ── ZsysClientConfig ────────────────────────────────────────────────────── */

enum ZsysClientMode : int {
    ZSYS_CLIENT_USER = 0,
    ZSYS_CLIENT_BOT  = 1,
}

struct ZsysClientConfig {
    int32_t        api_id;
    char*          api_hash;
    char*          session_name;
    ZsysClientMode mode;
    char*          phone;
    char*          bot_token;
    char*          device_model;
    char*          system_version;
    char*          app_version;
    char*          lang_code;
    char*          lang_pack;
    char*          proxy_host;
    int32_t        proxy_port;
    char*          proxy_user;
    char*          proxy_pass;
    int            sleep_threshold;
    int            max_concurrent;
}

ZsysClientConfig* zsys_client_config_new();
void              zsys_client_config_free(ZsysClientConfig* cfg);
int               zsys_client_config_copy(ZsysClientConfig* dst, const ZsysClientConfig* src);
int               zsys_client_set_api_hash(ZsysClientConfig* c, const char* val);
int               zsys_client_set_session_name(ZsysClientConfig* c, const char* val);
int               zsys_client_set_phone(ZsysClientConfig* c, const char* val);
int               zsys_client_set_bot_token(ZsysClientConfig* c, const char* val);
int               zsys_client_set_device_model(ZsysClientConfig* c, const char* val);
int               zsys_client_set_system_version(ZsysClientConfig* c, const char* val);
int               zsys_client_set_app_version(ZsysClientConfig* c, const char* val);
int               zsys_client_set_lang_code(ZsysClientConfig* c, const char* val);
int               zsys_client_set_lang_pack(ZsysClientConfig* c, const char* val);
int               zsys_client_set_proxy(ZsysClientConfig* c,
                                        const char* host, int32_t port,
                                        const char* user, const char* pass);
int               zsys_client_config_validate(const ZsysClientConfig* c,
                                              char* out_err, size_t err_len);
char*             zsys_client_config_to_json(const ZsysClientConfig* c);
int               zsys_client_config_from_json(ZsysClientConfig* c, const char* json);

void zsys_free(void* ptr);

// ─── D wrappers ───────────────────────────────────────────────────────────────

extern(D):

private string optStr(const(char)* p) nothrow @nogc {
    return p is null ? null : cast(string) p[0 .. strlen(p)];
}

private extern(C) size_t strlen(const(char)* s) pure nothrow @nogc;

/* ══════════════════════════════ User ════════════════════════════════════════ */

/// Safe D wrapper for ZsysUser.  Frees the C allocation on scope exit.
class DUser {
private:
    ZsysUser* _p;

public:
    /// Allocate a new zero-initialised user.
    this() {
        _p = zsys_user_new();
        if (_p is null) throw new Exception("zsys_user_new() returned null");
    }

    ~this() {
        if (_p !is null) {
            zsys_user_free(_p);
            _p = null;
        }
    }

    // ── properties ──────────────────────────────────────────────────────────

    @property long id() const         { return _p.id; }
    @property void id(long v)         { _p.id = v; }

    @property string username() const { return optStr(_p.username); }
    @property void username(string v) {
        zsys_user_set_username(_p, v.length ? v.toStringz : null);
    }

    @property string firstName() const { return optStr(_p.first_name); }
    @property void firstName(string v) {
        zsys_user_set_first_name(_p, v.toStringz);
    }

    @property string lastName() const { return optStr(_p.last_name); }
    @property void lastName(string v) {
        zsys_user_set_last_name(_p, v.length ? v.toStringz : null);
    }

    @property string phone() const { return optStr(_p.phone); }
    @property void phone(string v) {
        zsys_user_set_phone(_p, v.length ? v.toStringz : null);
    }

    @property string langCode() const { return optStr(_p.lang_code); }
    @property void langCode(string v) {
        zsys_user_set_lang_code(_p, v.length ? v.toStringz : null);
    }

    @property bool isBot() const    { return _p.is_bot != 0; }
    @property void isBot(bool v)    { _p.is_bot = v ? 1 : 0; }

    @property bool isPremium() const  { return _p.is_premium != 0; }
    @property void isPremium(bool v)  { _p.is_premium = v ? 1 : 0; }

    @property long createdAt() const  { return _p.created_at; }
    @property void createdAt(long v)  { _p.created_at = v; }

    // ── serialisation ────────────────────────────────────────────────────────

    string toJson() {
        char* raw = zsys_user_to_json(_p);
        if (raw is null) throw new Exception("zsys_user_to_json() failed");
        scope(exit) zsys_free(raw);
        return raw.fromStringz.idup;
    }

    static DUser fromJson(string json) {
        auto obj = new DUser();
        if (zsys_user_from_json(obj._p, json.toStringz) != 0)
            throw new Exception("zsys_user_from_json() parse error");
        return obj;
    }

    override string toString() const {
        import std.format : format;
        return format("DUser(id=%d, username=%s, firstName=%s)", id, username, firstName);
    }
}

/* ══════════════════════════════ Chat ════════════════════════════════════════ */

/// Chat type enum re-exported as a D enum.
alias DChatType = ZsysChatType;

/// Safe D wrapper for ZsysChat.
class DChat {
private:
    ZsysChat* _p;

public:
    this() {
        _p = zsys_chat_new();
        if (_p is null) throw new Exception("zsys_chat_new() returned null");
    }

    ~this() {
        if (_p !is null) {
            zsys_chat_free(_p);
            _p = null;
        }
    }

    // ── properties ──────────────────────────────────────────────────────────

    @property long id() const       { return _p.id; }
    @property void id(long v)       { _p.id = v; }

    @property ZsysChatType chatType() const    { return _p.type; }
    @property void chatType(ZsysChatType v)    { _p.type = v; }

    @property string typeStr() const {
        return zsys_chat_type_str(_p.type).fromStringz.idup;
    }

    @property string title() const { return optStr(_p.title); }
    @property void title(string v) {
        zsys_chat_set_title(_p, v.length ? v.toStringz : null);
    }

    @property string username() const { return optStr(_p.username); }
    @property void username(string v) {
        zsys_chat_set_username(_p, v.length ? v.toStringz : null);
    }

    @property string description() const { return optStr(_p.description); }
    @property void description(string v) {
        zsys_chat_set_description(_p, v.length ? v.toStringz : null);
    }

    @property int memberCount() const   { return _p.member_count; }
    @property void memberCount(int v)   { _p.member_count = v; }

    @property bool isRestricted() const { return _p.is_restricted != 0; }
    @property bool isScam() const       { return _p.is_scam != 0; }

    @property long createdAt() const    { return _p.created_at; }
    @property void createdAt(long v)    { _p.created_at = v; }

    // ── serialisation ────────────────────────────────────────────────────────

    string toJson() {
        char* raw = zsys_chat_to_json(_p);
        if (raw is null) throw new Exception("zsys_chat_to_json() failed");
        scope(exit) zsys_free(raw);
        return raw.fromStringz.idup;
    }

    static DChat fromJson(string json) {
        auto obj = new DChat();
        if (zsys_chat_from_json(obj._p, json.toStringz) != 0)
            throw new Exception("zsys_chat_from_json() parse error");
        return obj;
    }

    override string toString() const {
        import std.format : format;
        return format("DChat(id=%d, type=%s, title=%s)", id, typeStr, title);
    }
}

/* ══════════════════════════════ ClientConfig ════════════════════════════════ */

/// Client mode re-exported as a D alias.
alias DClientMode = ZsysClientMode;

/// Safe D wrapper for ZsysClientConfig.
class DClientConfig {
private:
    ZsysClientConfig* _p;

public:
    this() {
        _p = zsys_client_config_new();
        if (_p is null) throw new Exception("zsys_client_config_new() returned null");
    }

    ~this() {
        if (_p !is null) {
            zsys_client_config_free(_p);
            _p = null;
        }
    }

    // ── properties ──────────────────────────────────────────────────────────

    @property int apiId() const     { return _p.api_id; }
    @property void apiId(int v)     { _p.api_id = v; }

    @property string apiHash() const { return optStr(_p.api_hash); }
    @property void apiHash(string v) {
        zsys_client_set_api_hash(_p, v.toStringz);
    }

    @property string sessionName() const { return optStr(_p.session_name); }
    @property void sessionName(string v) {
        zsys_client_set_session_name(_p, v.toStringz);
    }

    @property ZsysClientMode mode() const  { return _p.mode; }
    @property void mode(ZsysClientMode v)  { _p.mode = v; }

    @property string phone() const { return optStr(_p.phone); }
    @property void phone(string v) {
        zsys_client_set_phone(_p, v.length ? v.toStringz : null);
    }

    @property string botToken() const { return optStr(_p.bot_token); }
    @property void botToken(string v) {
        zsys_client_set_bot_token(_p, v.length ? v.toStringz : null);
    }

    @property string deviceModel() const { return optStr(_p.device_model); }
    @property void deviceModel(string v) {
        zsys_client_set_device_model(_p, v.length ? v.toStringz : null);
    }

    @property string systemVersion() const { return optStr(_p.system_version); }
    @property void systemVersion(string v) {
        zsys_client_set_system_version(_p, v.length ? v.toStringz : null);
    }

    @property string appVersion() const { return optStr(_p.app_version); }
    @property void appVersion(string v) {
        zsys_client_set_app_version(_p, v.length ? v.toStringz : null);
    }

    @property string langCode() const { return optStr(_p.lang_code); }
    @property void langCode(string v) {
        zsys_client_set_lang_code(_p, v.length ? v.toStringz : null);
    }

    @property string langPack() const { return optStr(_p.lang_pack); }
    @property void langPack(string v) {
        zsys_client_set_lang_pack(_p, v.length ? v.toStringz : null);
    }

    @property string proxyHost() const { return optStr(_p.proxy_host); }
    @property int    proxyPort() const { return _p.proxy_port; }
    @property string proxyUser() const { return optStr(_p.proxy_user); }

    void setProxy(string host, int port, string user = null, string pass = null) {
        zsys_client_set_proxy(
            _p,
            host.toStringz,
            port,
            user.length ? user.toStringz : null,
            pass.length ? pass.toStringz : null,
        );
    }

    @property int sleepThreshold() const  { return _p.sleep_threshold; }
    @property void sleepThreshold(int v)  { _p.sleep_threshold = v; }

    @property int maxConcurrent() const   { return _p.max_concurrent; }
    @property void maxConcurrent(int v)   { _p.max_concurrent = v; }

    // ── validation / serialisation ───────────────────────────────────────────

    void validate() {
        char[256] buf;
        if (zsys_client_config_validate(_p, buf.ptr, buf.length) != 0)
            throw new Exception("invalid config: " ~ buf.ptr.fromStringz.idup);
    }

    string toJson() {
        char* raw = zsys_client_config_to_json(_p);
        if (raw is null) throw new Exception("zsys_client_config_to_json() failed");
        scope(exit) zsys_free(raw);
        return raw.fromStringz.idup;
    }

    static DClientConfig fromJson(string json) {
        auto obj = new DClientConfig();
        if (zsys_client_config_from_json(obj._p, json.toStringz) != 0)
            throw new Exception("zsys_client_config_from_json() parse error");
        return obj;
    }

    override string toString() const {
        import std.format : format;
        return format("DClientConfig(apiId=%d, session=%s, mode=%s)",
                      apiId, sessionName, mode);
    }
}
