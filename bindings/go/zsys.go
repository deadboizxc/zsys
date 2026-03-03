// Package zsys provides CGo bindings to the zsys C shared library.
//
// The C library (libzsys) must be installed or available as libzsys.so.
// Build with: make build-lib (from the project root).
package zsys

// #cgo LDFLAGS: -lzsys
// #include "../../zsys/include/zsys_core.h"
// #include "../../zsys/include/zsys_user.h"
// #include "../../zsys/include/zsys_chat.h"
// #include "../../zsys/include/zsys_client.h"
// #include "../../zsys/include/zsys_storage.h"
// #include <stdlib.h>
import "C"
import "unsafe"

// ── Router ───────────────────────────────────────────────────────────────

// Router wraps ZsysRouter (open-addressing hash table: trigger → handler_id).
type Router struct {
	ptr *C.ZsysRouter
}

// NewRouter allocates a new Router. Call Free() when done.
func NewRouter() *Router {
	return &Router{ptr: C.zsys_router_new()}
}

// Free releases all resources owned by the Router.
func (r *Router) Free() {
	C.zsys_router_free(r.ptr)
}

// Add registers trigger → handlerID. Returns 0 on success.
func (r *Router) Add(trigger string, handlerID int) int {
	ct := C.CString(trigger)
	defer C.free(unsafe.Pointer(ct))
	return int(C.zsys_router_add(r.ptr, ct, C.int(handlerID)))
}

// Remove unregisters a trigger. Returns 0 on success, -1 if not found.
func (r *Router) Remove(trigger string) int {
	ct := C.CString(trigger)
	defer C.free(unsafe.Pointer(ct))
	return int(C.zsys_router_remove(r.ptr, ct))
}

// Lookup returns handlerID for trigger, or -1 (case-insensitive).
func (r *Router) Lookup(trigger string) int {
	ct := C.CString(trigger)
	defer C.free(unsafe.Pointer(ct))
	return int(C.zsys_router_lookup(r.ptr, ct))
}

// Count returns the number of registered triggers.
func (r *Router) Count() int {
	return int(C.zsys_router_count(r.ptr))
}

// Clear removes all triggers.
func (r *Router) Clear() {
	C.zsys_router_clear(r.ptr)
}

// ── Registry ─────────────────────────────────────────────────────────────

// Registry wraps ZsysRegistry (dynamic array: name → handler_id + metadata).
type Registry struct {
	ptr *C.ZsysRegistry
}

// NewRegistry allocates a new Registry. Call Free() when done.
func NewRegistry() *Registry {
	return &Registry{ptr: C.zsys_registry_new()}
}

// Free releases all resources owned by the Registry.
func (reg *Registry) Free() {
	C.zsys_registry_free(reg.ptr)
}

// Register adds or updates name → handlerID with optional description and category.
func (reg *Registry) Register(name string, handlerID int, desc, cat string) int {
	cn := C.CString(name)
	cd := C.CString(desc)
	cc := C.CString(cat)
	defer C.free(unsafe.Pointer(cn))
	defer C.free(unsafe.Pointer(cd))
	defer C.free(unsafe.Pointer(cc))
	return int(C.zsys_registry_register(reg.ptr, cn, C.int(handlerID), cd, cc))
}

// Unregister removes an entry by name. Returns 0 on success, -1 if not found.
func (reg *Registry) Unregister(name string) int {
	cn := C.CString(name)
	defer C.free(unsafe.Pointer(cn))
	return int(C.zsys_registry_unregister(reg.ptr, cn))
}

// Get returns the handler_id for name, or -1 if not found.
func (reg *Registry) Get(name string) int {
	cn := C.CString(name)
	defer C.free(unsafe.Pointer(cn))
	return int(C.zsys_registry_get(reg.ptr, cn))
}

// Count returns the number of registered entries.
func (reg *Registry) Count() int {
	return int(C.zsys_registry_count(reg.ptr))
}

// NameAt returns the name of the entry at index i, or empty string.
func (reg *Registry) NameAt(i int) string {
	r := C.zsys_registry_name_at(reg.ptr, C.size_t(i))
	if r == nil {
		return ""
	}
	return C.GoString(r)
}

// ── I18n ─────────────────────────────────────────────────────────────────

// I18n wraps ZsysI18n (flat JSON loader, per-language key→value tables).
type I18n struct {
	ptr *C.ZsysI18n
}

// NewI18n allocates a new I18n context. Call Free() when done.
func NewI18n() *I18n {
	return &I18n{ptr: C.zsys_i18n_new()}
}

// Free releases all resources owned by the I18n context.
func (i *I18n) Free() {
	C.zsys_i18n_free(i.ptr)
}

// LoadJSON loads a flat {"key":"value"} JSON file for langCode.
func (i *I18n) LoadJSON(langCode, jsonPath string) int {
	cl := C.CString(langCode)
	cp := C.CString(jsonPath)
	defer C.free(unsafe.Pointer(cl))
	defer C.free(unsafe.Pointer(cp))
	return int(C.zsys_i18n_load_json(i.ptr, cl, cp))
}

// SetLang sets the active language for Get().
func (i *I18n) SetLang(langCode string) {
	cl := C.CString(langCode)
	defer C.free(unsafe.Pointer(cl))
	C.zsys_i18n_set_lang(i.ptr, cl)
}

// Get returns the translation for key in the active language, or key itself.
func (i *I18n) Get(key string) string {
	ck := C.CString(key)
	defer C.free(unsafe.Pointer(ck))
	r := C.zsys_i18n_get(i.ptr, ck)
	if r == nil {
		return key
	}
	return C.GoString(r)
}

// GetLang returns the translation for key in the specified language, or key.
func (i *I18n) GetLang(langCode, key string) string {
	cl := C.CString(langCode)
	ck := C.CString(key)
	defer C.free(unsafe.Pointer(cl))
	defer C.free(unsafe.Pointer(ck))
	r := C.zsys_i18n_get_lang(i.ptr, cl, ck)
	if r == nil {
		return key
	}
	return C.GoString(r)
}

// ── User ─────────────────────────────────────────────────────────────────

// User wraps ZsysUser (heap-allocated Telegram user/account representation).
type User struct {
ptr *C.ZsysUser
}

// NewUser allocates a new, zero-initialised User. Call Free() when done.
func NewUser() *User {
return &User{ptr: C.zsys_user_new()}
}

// Free releases all resources owned by the User.
func (u *User) Free() {
C.zsys_user_free(u.ptr)
}

// SetUsername sets the @username field (NULL clears it). Returns 0 on success.
func (u *User) SetUsername(v string) int {
cv := C.CString(v)
defer C.free(unsafe.Pointer(cv))
return int(C.zsys_user_set_username(u.ptr, cv))
}

// SetFirstName sets the first_name field. Returns 0 on success.
func (u *User) SetFirstName(v string) int {
cv := C.CString(v)
defer C.free(unsafe.Pointer(cv))
return int(C.zsys_user_set_first_name(u.ptr, cv))
}

// SetLastName sets the last_name field (NULL clears it). Returns 0 on success.
func (u *User) SetLastName(v string) int {
cv := C.CString(v)
defer C.free(unsafe.Pointer(cv))
return int(C.zsys_user_set_last_name(u.ptr, cv))
}

// SetPhone sets the phone field (NULL clears it). Returns 0 on success.
func (u *User) SetPhone(v string) int {
cv := C.CString(v)
defer C.free(unsafe.Pointer(cv))
return int(C.zsys_user_set_phone(u.ptr, cv))
}

// SetLangCode sets the lang_code field. Returns 0 on success.
func (u *User) SetLangCode(v string) int {
cv := C.CString(v)
defer C.free(unsafe.Pointer(cv))
return int(C.zsys_user_set_lang_code(u.ptr, cv))
}

// ID returns the Telegram user ID.
func (u *User) ID() int64 { return int64(u.ptr.id) }

// IsBot returns true if this is a bot account.
func (u *User) IsBot() bool { return u.ptr.is_bot != 0 }

// IsPremium returns true if the user has Telegram Premium.
func (u *User) IsPremium() bool { return u.ptr.is_premium != 0 }

// ToJSON serialises the user to a flat JSON string. Caller must not free the result.
func (u *User) ToJSON() string {
r := C.zsys_user_to_json(u.ptr)
if r == nil {
return "{}"
}
defer C.zsys_free(unsafe.Pointer(r))
return C.GoString(r)
}

// ── Chat ─────────────────────────────────────────────────────────────────

// ChatType mirrors ZsysChatType.
type ChatType int

const (
ChatPrivate    ChatType = 0
ChatGroup      ChatType = 1
ChatSupergroup ChatType = 2
ChatChannel    ChatType = 3
ChatBot        ChatType = 4
)

// Chat wraps ZsysChat (heap-allocated Telegram chat/group/channel).
type Chat struct {
ptr *C.ZsysChat
}

// NewChat allocates a new, zero-initialised Chat. Call Free() when done.
func NewChat() *Chat {
return &Chat{ptr: C.zsys_chat_new()}
}

// Free releases all resources owned by the Chat.
func (c *Chat) Free() {
C.zsys_chat_free(c.ptr)
}

// SetTitle sets the title field. Returns 0 on success.
func (c *Chat) SetTitle(v string) int {
cv := C.CString(v)
defer C.free(unsafe.Pointer(cv))
return int(C.zsys_chat_set_title(c.ptr, cv))
}

// SetUsername sets the @username field. Returns 0 on success.
func (c *Chat) SetUsername(v string) int {
cv := C.CString(v)
defer C.free(unsafe.Pointer(cv))
return int(C.zsys_chat_set_username(c.ptr, cv))
}

// ID returns the Telegram chat ID.
func (c *Chat) ID() int64 { return int64(c.ptr.id) }

// Type returns the chat type (private/group/supergroup/channel/bot).
func (c *Chat) Type() ChatType { return ChatType(c.ptr._type) }

// MemberCount returns the member count (-1 = unknown).
func (c *Chat) MemberCount() int32 { return int32(c.ptr.member_count) }

// ToJSON serialises the chat to a flat JSON string.
func (c *Chat) ToJSON() string {
r := C.zsys_chat_to_json(c.ptr)
if r == nil {
return "{}"
}
defer C.zsys_free(unsafe.Pointer(r))
return C.GoString(r)
}

// ── ClientConfig ─────────────────────────────────────────────────────────

// ClientMode mirrors ZsysClientMode.
type ClientMode int

const (
ClientUser ClientMode = 0
ClientBot  ClientMode = 1
)

// ClientConfig wraps ZsysClientConfig (Telegram session credentials).
type ClientConfig struct {
ptr *C.ZsysClientConfig
}

// NewClientConfig allocates a ClientConfig with sensible defaults.
// Defaults: mode=User, lang_code="en", sleep_threshold=60, max_concurrent=1.
func NewClientConfig() *ClientConfig {
return &ClientConfig{ptr: C.zsys_client_config_new()}
}

// Free releases all resources owned by the ClientConfig.
func (cc *ClientConfig) Free() {
C.zsys_client_config_free(cc.ptr)
}

// SetAPIHash sets the api_hash field. Returns 0 on success.
func (cc *ClientConfig) SetAPIHash(v string) int {
cv := C.CString(v)
defer C.free(unsafe.Pointer(cv))
return int(C.zsys_client_config_set_api_hash(cc.ptr, cv))
}

// SetSessionName sets the session file name. Returns 0 on success.
func (cc *ClientConfig) SetSessionName(v string) int {
cv := C.CString(v)
defer C.free(unsafe.Pointer(cv))
return int(C.zsys_client_config_set_session_name(cc.ptr, cv))
}

// SetPhone sets the phone number. Returns 0 on success.
func (cc *ClientConfig) SetPhone(v string) int {
cv := C.CString(v)
defer C.free(unsafe.Pointer(cv))
return int(C.zsys_client_config_set_phone(cc.ptr, cv))
}

// SetBotToken sets the bot token. Returns 0 on success.
func (cc *ClientConfig) SetBotToken(v string) int {
cv := C.CString(v)
defer C.free(unsafe.Pointer(cv))
return int(C.zsys_client_config_set_bot_token(cc.ptr, cv))
}

// APIID returns the Telegram API ID.
func (cc *ClientConfig) APIID() int32 { return int32(cc.ptr.api_id) }

// Mode returns the client mode (user or bot).
func (cc *ClientConfig) Mode() ClientMode { return ClientMode(cc.ptr.mode) }

// ToJSON serialises the config to a flat JSON string (tokens redacted).
func (cc *ClientConfig) ToJSON() string {
r := C.zsys_client_config_to_json(cc.ptr)
if r == nil {
return "{}"
}
defer C.zsys_free(unsafe.Pointer(r))
return C.GoString(r)
}

// ── KV Store ─────────────────────────────────────────────────────────────

// KV wraps ZsysKV (open-addressing string key-value store).
type KV struct {
ptr *C.ZsysKV
}

// NewKV allocates a new KV store. initialCap=0 uses the default (16 slots).
func NewKV(initialCap int) *KV {
return &KV{ptr: C.zsys_kv_new(C.size_t(initialCap))}
}

// Free releases all resources owned by the KV store.
func (kv *KV) Free() {
C.zsys_kv_free(kv.ptr)
}

// Set inserts or updates key→value. Returns 0 on success, -1 on alloc failure.
func (kv *KV) Set(key, value string) int {
ck := C.CString(key)
cv := C.CString(value)
defer C.free(unsafe.Pointer(ck))
defer C.free(unsafe.Pointer(cv))
return int(C.zsys_kv_set(kv.ptr, ck, cv))
}

// Get returns the value for key, or "" if not found.
func (kv *KV) Get(key string) string {
ck := C.CString(key)
defer C.free(unsafe.Pointer(ck))
r := C.zsys_kv_get(kv.ptr, ck)
if r == nil {
return ""
}
return C.GoString(r)
}

// Del removes the key. Returns 0 on success, -1 if not found.
func (kv *KV) Del(key string) int {
ck := C.CString(key)
defer C.free(unsafe.Pointer(ck))
return int(C.zsys_kv_del(kv.ptr, ck))
}

// Has returns true if the key exists.
func (kv *KV) Has(key string) bool {
ck := C.CString(key)
defer C.free(unsafe.Pointer(ck))
return C.zsys_kv_has(kv.ptr, ck) != 0
}

// Count returns the number of stored entries.
func (kv *KV) Count() int {
return int(C.zsys_kv_count(kv.ptr))
}

// ToJSON serialises all key-value pairs to a flat JSON object.
// The caller must not free the returned string.
func (kv *KV) ToJSON() string {
r := C.zsys_kv_to_json(kv.ptr)
if r == nil {
return "{}"
}
defer C.zsys_free(unsafe.Pointer(r))
return C.GoString(r)
}
