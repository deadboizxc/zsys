// zsys.core V bindings — wraps libzsys_core.so.
//
// Build example:
//   v -cflags "-I../../c/include" core.v
//
// The library is linked automatically via the #flag directives below.

module core

#flag -lzsys_core
#flag -I ../../c/include
#include "zsys_user.h"
#include "zsys_chat.h"
#include "zsys_client.h"

// ─── C type declarations ──────────────────────────────────────────────────────

// ZsysChatType
pub const chat_private    = 0
pub const chat_group      = 1
pub const chat_supergroup = 2
pub const chat_channel    = 3
pub const chat_bot        = 4

// ZsysClientMode
pub const client_mode_user = 0
pub const client_mode_bot  = 1

// ─── C struct mirrors (used only for C interop) ───────────────────────────────

struct C.ZsysUser {
	id         i64
	username   &char
	first_name &char
	last_name  &char
	phone      &char
	lang_code  &char
	is_bot     int
	is_premium int
	created_at i64
}

struct C.ZsysChat {
	id            i64
	@type         int   // ZsysChatType
	title         &char
	username      &char
	description   &char
	member_count  int
	is_restricted int
	is_scam       int
	created_at    i64
}

struct C.ZsysClientConfig {
	api_id          int
	api_hash        &char
	session_name    &char
	mode            int   // ZsysClientMode
	phone           &char
	bot_token       &char
	device_model    &char
	system_version  &char
	app_version     &char
	lang_code       &char
	lang_pack       &char
	proxy_host      &char
	proxy_port      int
	proxy_user      &char
	proxy_pass      &char
	sleep_threshold int
	max_concurrent  int
}

// ─── C function declarations ──────────────────────────────────────────────────

fn C.zsys_user_new() &C.ZsysUser
fn C.zsys_user_free(u &C.ZsysUser)
fn C.zsys_user_set_username(u &C.ZsysUser, val &char) int
fn C.zsys_user_set_first_name(u &C.ZsysUser, val &char) int
fn C.zsys_user_set_last_name(u &C.ZsysUser, val &char) int
fn C.zsys_user_set_phone(u &C.ZsysUser, val &char) int
fn C.zsys_user_set_lang_code(u &C.ZsysUser, val &char) int
fn C.zsys_user_to_json(u &C.ZsysUser) &char
fn C.zsys_user_from_json(u &C.ZsysUser, json &char) int

fn C.zsys_chat_new() &C.ZsysChat
fn C.zsys_chat_free(c &C.ZsysChat)
fn C.zsys_chat_set_title(c &C.ZsysChat, val &char) int
fn C.zsys_chat_set_username(c &C.ZsysChat, val &char) int
fn C.zsys_chat_set_description(c &C.ZsysChat, val &char) int
fn C.zsys_chat_type_str(t int) &char
fn C.zsys_chat_to_json(c &C.ZsysChat) &char
fn C.zsys_chat_from_json(c &C.ZsysChat, json &char) int

fn C.zsys_client_config_new() &C.ZsysClientConfig
fn C.zsys_client_config_free(cfg &C.ZsysClientConfig)
fn C.zsys_client_set_api_hash(c &C.ZsysClientConfig, val &char) int
fn C.zsys_client_set_session_name(c &C.ZsysClientConfig, val &char) int
fn C.zsys_client_set_phone(c &C.ZsysClientConfig, val &char) int
fn C.zsys_client_set_bot_token(c &C.ZsysClientConfig, val &char) int
fn C.zsys_client_set_device_model(c &C.ZsysClientConfig, val &char) int
fn C.zsys_client_set_system_version(c &C.ZsysClientConfig, val &char) int
fn C.zsys_client_set_app_version(c &C.ZsysClientConfig, val &char) int
fn C.zsys_client_set_lang_code(c &C.ZsysClientConfig, val &char) int
fn C.zsys_client_set_lang_pack(c &C.ZsysClientConfig, val &char) int
fn C.zsys_client_set_proxy(c &C.ZsysClientConfig, host &char, port int, user &char, pass &char) int
fn C.zsys_client_config_validate(c &C.ZsysClientConfig, out_err &char, err_len usize) int
fn C.zsys_client_config_to_json(c &C.ZsysClientConfig) &char
fn C.zsys_client_config_from_json(c &C.ZsysClientConfig, json &char) int

fn C.zsys_free(ptr voidptr)

// ─── helpers ──────────────────────────────────────────────────────────────────

fn cstr(s string) &char {
	return unsafe { &char(s.str) }
}

fn cstr_opt(s string) &char {
	if s == '' {
		return unsafe { &char(0) }
	}
	return unsafe { &char(s.str) }
}

fn from_cstr(p &char) string {
	if unsafe { p == &char(0) } {
		return ''
	}
	return unsafe { cstring_to_vstring(p) }
}

// ═══════════════════════════════ User ════════════════════════════════════════

// User is a V wrapper around ZsysUser.
pub struct User {
mut:
	ptr &C.ZsysUser = unsafe { nil }
}

// new_user allocates a zero-initialised User.
pub fn new_user() !User {
	p := C.zsys_user_new()
	if unsafe { p == nil } {
		return error('zsys_user_new() returned null')
	}
	return User{ ptr: p }
}

// free releases the underlying C allocation.
pub fn (mut u User) free() {
	if unsafe { u.ptr != nil } {
		C.zsys_user_free(u.ptr)
		unsafe { u.ptr = nil }
	}
}

pub fn (u &User) id() i64          { return u.ptr.id }
pub fn (mut u User) set_id(v i64)  { u.ptr.id = v }

pub fn (u &User) username() string { return from_cstr(u.ptr.username) }
pub fn (mut u User) set_username(v string) {
	C.zsys_user_set_username(u.ptr, cstr_opt(v))
}

pub fn (u &User) first_name() string { return from_cstr(u.ptr.first_name) }
pub fn (mut u User) set_first_name(v string) {
	C.zsys_user_set_first_name(u.ptr, cstr(v))
}

pub fn (u &User) last_name() string { return from_cstr(u.ptr.last_name) }
pub fn (mut u User) set_last_name(v string) {
	C.zsys_user_set_last_name(u.ptr, cstr_opt(v))
}

pub fn (u &User) phone() string { return from_cstr(u.ptr.phone) }
pub fn (mut u User) set_phone(v string) {
	C.zsys_user_set_phone(u.ptr, cstr_opt(v))
}

pub fn (u &User) lang_code() string { return from_cstr(u.ptr.lang_code) }
pub fn (mut u User) set_lang_code(v string) {
	C.zsys_user_set_lang_code(u.ptr, cstr_opt(v))
}

pub fn (u &User) is_bot() bool      { return u.ptr.is_bot != 0 }
pub fn (mut u User) set_is_bot(v bool) { u.ptr.is_bot = if v { 1 } else { 0 } }

pub fn (u &User) is_premium() bool       { return u.ptr.is_premium != 0 }
pub fn (mut u User) set_is_premium(v bool) { u.ptr.is_premium = if v { 1 } else { 0 } }

pub fn (u &User) created_at() i64        { return u.ptr.created_at }
pub fn (mut u User) set_created_at(v i64) { u.ptr.created_at = v }

pub fn (u &User) to_json() !string {
	raw := C.zsys_user_to_json(u.ptr)
	if unsafe { raw == &char(0) } {
		return error('zsys_user_to_json() failed')
	}
	s := from_cstr(raw)
	C.zsys_free(raw)
	return s
}

pub fn user_from_json(json string) !User {
	mut obj := new_user()!
	if C.zsys_user_from_json(obj.ptr, cstr(json)) != 0 {
		obj.free()
		return error('zsys_user_from_json() parse error')
	}
	return obj
}

pub fn (u &User) str() string {
	return 'User(id=${u.id()}, username=${u.username()}, first_name=${u.first_name()})'
}

// ═══════════════════════════════ Chat ════════════════════════════════════════

// Chat is a V wrapper around ZsysChat.
pub struct Chat {
mut:
	ptr &C.ZsysChat = unsafe { nil }
}

pub fn new_chat() !Chat {
	p := C.zsys_chat_new()
	if unsafe { p == nil } {
		return error('zsys_chat_new() returned null')
	}
	return Chat{ ptr: p }
}

pub fn (mut c Chat) free() {
	if unsafe { c.ptr != nil } {
		C.zsys_chat_free(c.ptr)
		unsafe { c.ptr = nil }
	}
}

pub fn (c &Chat) id() i64          { return c.ptr.id }
pub fn (mut c Chat) set_id(v i64)  { c.ptr.id = v }

pub fn (c &Chat) chat_type() int         { return c.ptr.@type }
pub fn (mut c Chat) set_chat_type(v int) { c.ptr.@type = v }

pub fn (c &Chat) type_str() string {
	return from_cstr(C.zsys_chat_type_str(c.ptr.@type))
}

pub fn (c &Chat) title() string { return from_cstr(c.ptr.title) }
pub fn (mut c Chat) set_title(v string) {
	C.zsys_chat_set_title(c.ptr, cstr_opt(v))
}

pub fn (c &Chat) username() string { return from_cstr(c.ptr.username) }
pub fn (mut c Chat) set_username(v string) {
	C.zsys_chat_set_username(c.ptr, cstr_opt(v))
}

pub fn (c &Chat) description() string { return from_cstr(c.ptr.description) }
pub fn (mut c Chat) set_description(v string) {
	C.zsys_chat_set_description(c.ptr, cstr_opt(v))
}

pub fn (c &Chat) member_count() int        { return c.ptr.member_count }
pub fn (mut c Chat) set_member_count(v int) { c.ptr.member_count = v }

pub fn (c &Chat) is_restricted() bool { return c.ptr.is_restricted != 0 }
pub fn (c &Chat) is_scam() bool       { return c.ptr.is_scam != 0 }
pub fn (c &Chat) created_at() i64     { return c.ptr.created_at }

pub fn (c &Chat) to_json() !string {
	raw := C.zsys_chat_to_json(c.ptr)
	if unsafe { raw == &char(0) } {
		return error('zsys_chat_to_json() failed')
	}
	s := from_cstr(raw)
	C.zsys_free(raw)
	return s
}

pub fn chat_from_json(json string) !Chat {
	mut obj := new_chat()!
	if C.zsys_chat_from_json(obj.ptr, cstr(json)) != 0 {
		obj.free()
		return error('zsys_chat_from_json() parse error')
	}
	return obj
}

pub fn (c &Chat) str() string {
	return 'Chat(id=${c.id()}, type=${c.type_str()}, title=${c.title()})'
}

// ═══════════════════════════════ ClientConfig ═════════════════════════════════

// ClientConfig is a V wrapper around ZsysClientConfig.
pub struct ClientConfig {
mut:
	ptr &C.ZsysClientConfig = unsafe { nil }
}

pub fn new_client_config() !ClientConfig {
	p := C.zsys_client_config_new()
	if unsafe { p == nil } {
		return error('zsys_client_config_new() returned null')
	}
	return ClientConfig{ ptr: p }
}

pub fn (mut cfg ClientConfig) free() {
	if unsafe { cfg.ptr != nil } {
		C.zsys_client_config_free(cfg.ptr)
		unsafe { cfg.ptr = nil }
	}
}

pub fn (cfg &ClientConfig) api_id() int         { return cfg.ptr.api_id }
pub fn (mut cfg ClientConfig) set_api_id(v int) { cfg.ptr.api_id = v }

pub fn (cfg &ClientConfig) api_hash() string { return from_cstr(cfg.ptr.api_hash) }
pub fn (mut cfg ClientConfig) set_api_hash(v string) {
	C.zsys_client_set_api_hash(cfg.ptr, cstr(v))
}

pub fn (cfg &ClientConfig) session_name() string { return from_cstr(cfg.ptr.session_name) }
pub fn (mut cfg ClientConfig) set_session_name(v string) {
	C.zsys_client_set_session_name(cfg.ptr, cstr(v))
}

pub fn (cfg &ClientConfig) mode() int          { return cfg.ptr.mode }
pub fn (mut cfg ClientConfig) set_mode(v int)  { cfg.ptr.mode = v }

pub fn (cfg &ClientConfig) phone() string { return from_cstr(cfg.ptr.phone) }
pub fn (mut cfg ClientConfig) set_phone(v string) {
	C.zsys_client_set_phone(cfg.ptr, cstr_opt(v))
}

pub fn (cfg &ClientConfig) bot_token() string { return from_cstr(cfg.ptr.bot_token) }
pub fn (mut cfg ClientConfig) set_bot_token(v string) {
	C.zsys_client_set_bot_token(cfg.ptr, cstr_opt(v))
}

pub fn (cfg &ClientConfig) device_model() string { return from_cstr(cfg.ptr.device_model) }
pub fn (mut cfg ClientConfig) set_device_model(v string) {
	C.zsys_client_set_device_model(cfg.ptr, cstr_opt(v))
}

pub fn (cfg &ClientConfig) system_version() string { return from_cstr(cfg.ptr.system_version) }
pub fn (mut cfg ClientConfig) set_system_version(v string) {
	C.zsys_client_set_system_version(cfg.ptr, cstr_opt(v))
}

pub fn (cfg &ClientConfig) app_version() string { return from_cstr(cfg.ptr.app_version) }
pub fn (mut cfg ClientConfig) set_app_version(v string) {
	C.zsys_client_set_app_version(cfg.ptr, cstr_opt(v))
}

pub fn (cfg &ClientConfig) lang_code() string { return from_cstr(cfg.ptr.lang_code) }
pub fn (mut cfg ClientConfig) set_lang_code(v string) {
	C.zsys_client_set_lang_code(cfg.ptr, cstr_opt(v))
}

pub fn (cfg &ClientConfig) lang_pack() string { return from_cstr(cfg.ptr.lang_pack) }
pub fn (mut cfg ClientConfig) set_lang_pack(v string) {
	C.zsys_client_set_lang_pack(cfg.ptr, cstr_opt(v))
}

pub fn (cfg &ClientConfig) proxy_host() string { return from_cstr(cfg.ptr.proxy_host) }
pub fn (cfg &ClientConfig) proxy_port() int    { return cfg.ptr.proxy_port }
pub fn (cfg &ClientConfig) proxy_user() string { return from_cstr(cfg.ptr.proxy_user) }

pub fn (mut cfg ClientConfig) set_proxy(host string, port int, user string, pass string) {
	C.zsys_client_set_proxy(cfg.ptr, cstr(host), port, cstr_opt(user), cstr_opt(pass))
}

pub fn (cfg &ClientConfig) sleep_threshold() int          { return cfg.ptr.sleep_threshold }
pub fn (mut cfg ClientConfig) set_sleep_threshold(v int)  { cfg.ptr.sleep_threshold = v }

pub fn (cfg &ClientConfig) max_concurrent() int           { return cfg.ptr.max_concurrent }
pub fn (mut cfg ClientConfig) set_max_concurrent(v int)   { cfg.ptr.max_concurrent = v }

pub fn (cfg &ClientConfig) validate() ! {
	mut buf := [256]u8{}
	rc := C.zsys_client_config_validate(cfg.ptr, unsafe { &char(&buf[0]) }, 256)
	if rc != 0 {
		return error(unsafe { cstring_to_vstring(&char(&buf[0])) })
	}
}

pub fn (cfg &ClientConfig) to_json() !string {
	raw := C.zsys_client_config_to_json(cfg.ptr)
	if unsafe { raw == &char(0) } {
		return error('zsys_client_config_to_json() failed')
	}
	s := from_cstr(raw)
	C.zsys_free(raw)
	return s
}

pub fn client_config_from_json(json string) !ClientConfig {
	mut obj := new_client_config()!
	if C.zsys_client_config_from_json(obj.ptr, cstr(json)) != 0 {
		obj.free()
		return error('zsys_client_config_from_json() parse error')
	}
	return obj
}

pub fn (cfg &ClientConfig) str() string {
	mode_str := if cfg.mode() == client_mode_bot { 'BOT' } else { 'USER' }
	return 'ClientConfig(api_id=${cfg.api_id()}, session=${cfg.session_name()}, mode=${mode_str})'
}
