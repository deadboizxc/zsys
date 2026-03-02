// Package core provides Go (cgo) bindings for libzsys_core.
// It wraps ZsysUser, ZsysChat, and ZsysClientConfig.
package core

/*
#cgo LDFLAGS: -lzsys_core
#include "../../c/include/zsys_user.h"
#include "../../c/include/zsys_chat.h"
#include "../../c/include/zsys_client.h"
#include <stdlib.h>
*/
import "C"
import (
	"errors"
	"runtime"
	"unsafe"
)

// ─── helpers ─────────────────────────────────────────────────────────────────

func cStrOpt(s string) *C.char {
	if s == "" {
		return nil
	}
	return C.CString(s)
}

func goStr(p *C.char) string {
	if p == nil {
		return ""
	}
	return C.GoString(p)
}

// ═══════════════════════════════ ChatType ═════════════════════════════════════

// ChatType mirrors ZsysChatType.
type ChatType int

const (
	ChatPrivate    ChatType = 0
	ChatGroup      ChatType = 1
	ChatSupergroup ChatType = 2
	ChatChannel    ChatType = 3
	ChatBot        ChatType = 4
)

// ═══════════════════════════════ ClientMode ═══════════════════════════════════

// ClientMode mirrors ZsysClientMode.
type ClientMode int

const (
	ClientModeUser ClientMode = 0
	ClientModeBot  ClientMode = 1
)

// ═══════════════════════════════ User ════════════════════════════════════════

// User wraps a heap-allocated ZsysUser.  Use NewUser() to create one.
type User struct {
	ptr *C.ZsysUser
}

// NewUser allocates a zero-initialised User.
func NewUser() (*User, error) {
	p := C.zsys_user_new()
	if p == nil {
		return nil, errors.New("zsys_user_new() returned NULL")
	}
	u := &User{ptr: p}
	runtime.SetFinalizer(u, (*User).Free)
	return u, nil
}

// Free releases the underlying C allocation immediately.
func (u *User) Free() {
	if u.ptr != nil {
		C.zsys_user_free(u.ptr)
		u.ptr = nil
	}
}

// ID returns the Telegram user ID.
func (u *User) ID() int64 { return int64(u.ptr.id) }

// SetID sets the Telegram user ID.
func (u *User) SetID(v int64) { u.ptr.id = C.int64_t(v) }

// Username returns the @username without '@', or "".
func (u *User) Username() string { return goStr(u.ptr.username) }

// SetUsername sets the username (empty string clears the field).
func (u *User) SetUsername(v string) {
	cs := cStrOpt(v)
	C.zsys_user_set_username(u.ptr, cs)
	if cs != nil {
		C.free(unsafe.Pointer(cs))
	}
}

// FirstName returns the first name.
func (u *User) FirstName() string { return goStr(u.ptr.first_name) }

// SetFirstName sets the first name.
func (u *User) SetFirstName(v string) {
	cs := C.CString(v)
	defer C.free(unsafe.Pointer(cs))
	C.zsys_user_set_first_name(u.ptr, cs)
}

// LastName returns the last name, or "".
func (u *User) LastName() string { return goStr(u.ptr.last_name) }

// SetLastName sets the last name (empty clears the field).
func (u *User) SetLastName(v string) {
	cs := cStrOpt(v)
	C.zsys_user_set_last_name(u.ptr, cs)
	if cs != nil {
		C.free(unsafe.Pointer(cs))
	}
}

// Phone returns the phone number, or "".
func (u *User) Phone() string { return goStr(u.ptr.phone) }

// SetPhone sets the phone number (empty clears the field).
func (u *User) SetPhone(v string) {
	cs := cStrOpt(v)
	C.zsys_user_set_phone(u.ptr, cs)
	if cs != nil {
		C.free(unsafe.Pointer(cs))
	}
}

// LangCode returns the IETF language tag, or "".
func (u *User) LangCode() string { return goStr(u.ptr.lang_code) }

// SetLangCode sets the language code.
func (u *User) SetLangCode(v string) {
	cs := cStrOpt(v)
	C.zsys_user_set_lang_code(u.ptr, cs)
	if cs != nil {
		C.free(unsafe.Pointer(cs))
	}
}

// IsBot returns true if this is a bot account.
func (u *User) IsBot() bool { return u.ptr.is_bot != 0 }

// SetIsBot marks the user as a bot.
func (u *User) SetIsBot(v bool) {
	if v {
		u.ptr.is_bot = 1
	} else {
		u.ptr.is_bot = 0
	}
}

// IsPremium returns true if the user has Telegram Premium.
func (u *User) IsPremium() bool { return u.ptr.is_premium != 0 }

// SetIsPremium marks the user as a premium subscriber.
func (u *User) SetIsPremium(v bool) {
	if v {
		u.ptr.is_premium = 1
	} else {
		u.ptr.is_premium = 0
	}
}

// CreatedAt returns the Unix timestamp of record creation.
func (u *User) CreatedAt() int64 { return int64(u.ptr.created_at) }

// SetCreatedAt sets the creation timestamp.
func (u *User) SetCreatedAt(v int64) { u.ptr.created_at = C.int64_t(v) }

// ToJSON serialises the user to a JSON string.
func (u *User) ToJSON() (string, error) {
	raw := C.zsys_user_to_json(u.ptr)
	if raw == nil {
		return "", errors.New("zsys_user_to_json() failed")
	}
	s := C.GoString(raw)
	C.zsys_free(unsafe.Pointer(raw))
	return s, nil
}

// UserFromJSON deserialises a User from a JSON string.
func UserFromJSON(json string) (*User, error) {
	u, err := NewUser()
	if err != nil {
		return nil, err
	}
	cs := C.CString(json)
	defer C.free(unsafe.Pointer(cs))
	if C.zsys_user_from_json(u.ptr, cs) != 0 {
		u.Free()
		return nil, errors.New("zsys_user_from_json() parse error")
	}
	return u, nil
}

// ═══════════════════════════════ Chat ════════════════════════════════════════

// Chat wraps a heap-allocated ZsysChat.
type Chat struct {
	ptr *C.ZsysChat
}

// NewChat allocates a zero-initialised Chat.
func NewChat() (*Chat, error) {
	p := C.zsys_chat_new()
	if p == nil {
		return nil, errors.New("zsys_chat_new() returned NULL")
	}
	c := &Chat{ptr: p}
	runtime.SetFinalizer(c, (*Chat).Free)
	return c, nil
}

// Free releases the underlying C allocation immediately.
func (c *Chat) Free() {
	if c.ptr != nil {
		C.zsys_chat_free(c.ptr)
		c.ptr = nil
	}
}

// ID returns the Telegram chat ID.
func (c *Chat) ID() int64 { return int64(c.ptr.id) }

// SetID sets the chat ID.
func (c *Chat) SetID(v int64) { c.ptr.id = C.int64_t(v) }

// Type returns the chat type.
func (c *Chat) Type() ChatType { return ChatType(c.ptr._type) }

// SetType sets the chat type.
func (c *Chat) SetType(v ChatType) { c.ptr._type = C.ZsysChatType(v) }

// TypeStr returns a human-readable chat type name.
func (c *Chat) TypeStr() string {
	return C.GoString(C.zsys_chat_type_str(c.ptr._type))
}

// Title returns the chat title, or "".
func (c *Chat) Title() string { return goStr(c.ptr.title) }

// SetTitle sets the chat title (empty clears the field).
func (c *Chat) SetTitle(v string) {
	cs := cStrOpt(v)
	C.zsys_chat_set_title(c.ptr, cs)
	if cs != nil {
		C.free(unsafe.Pointer(cs))
	}
}

// Username returns the @username, or "".
func (c *Chat) Username() string { return goStr(c.ptr.username) }

// SetUsername sets the username (empty clears the field).
func (c *Chat) SetUsername(v string) {
	cs := cStrOpt(v)
	C.zsys_chat_set_username(c.ptr, cs)
	if cs != nil {
		C.free(unsafe.Pointer(cs))
	}
}

// Description returns the chat description, or "".
func (c *Chat) Description() string { return goStr(c.ptr.description) }

// SetDescription sets the description (empty clears the field).
func (c *Chat) SetDescription(v string) {
	cs := cStrOpt(v)
	C.zsys_chat_set_description(c.ptr, cs)
	if cs != nil {
		C.free(unsafe.Pointer(cs))
	}
}

// MemberCount returns the number of members (-1 = unknown).
func (c *Chat) MemberCount() int32 { return int32(c.ptr.member_count) }

// SetMemberCount sets the member count.
func (c *Chat) SetMemberCount(v int32) { c.ptr.member_count = C.int32_t(v) }

// IsRestricted returns true if the chat is restricted.
func (c *Chat) IsRestricted() bool { return c.ptr.is_restricted != 0 }

// IsScam returns true if Telegram flagged the chat as a scam.
func (c *Chat) IsScam() bool { return c.ptr.is_scam != 0 }

// CreatedAt returns the Unix timestamp of record creation.
func (c *Chat) CreatedAt() int64 { return int64(c.ptr.created_at) }

// ToJSON serialises the chat to a JSON string.
func (c *Chat) ToJSON() (string, error) {
	raw := C.zsys_chat_to_json(c.ptr)
	if raw == nil {
		return "", errors.New("zsys_chat_to_json() failed")
	}
	s := C.GoString(raw)
	C.zsys_free(unsafe.Pointer(raw))
	return s, nil
}

// ChatFromJSON deserialises a Chat from a JSON string.
func ChatFromJSON(json string) (*Chat, error) {
	c, err := NewChat()
	if err != nil {
		return nil, err
	}
	cs := C.CString(json)
	defer C.free(unsafe.Pointer(cs))
	if C.zsys_chat_from_json(c.ptr, cs) != 0 {
		c.Free()
		return nil, errors.New("zsys_chat_from_json() parse error")
	}
	return c, nil
}

// ═══════════════════════════════ ClientConfig ═════════════════════════════════

// ClientConfig wraps a heap-allocated ZsysClientConfig.
type ClientConfig struct {
	ptr *C.ZsysClientConfig
}

// NewClientConfig allocates a ClientConfig with sensible defaults.
func NewClientConfig() (*ClientConfig, error) {
	p := C.zsys_client_config_new()
	if p == nil {
		return nil, errors.New("zsys_client_config_new() returned NULL")
	}
	cfg := &ClientConfig{ptr: p}
	runtime.SetFinalizer(cfg, (*ClientConfig).Free)
	return cfg, nil
}

// Free releases the underlying C allocation immediately.
func (cfg *ClientConfig) Free() {
	if cfg.ptr != nil {
		C.zsys_client_config_free(cfg.ptr)
		cfg.ptr = nil
	}
}

// APIID returns the Telegram API ID.
func (cfg *ClientConfig) APIID() int32 { return int32(cfg.ptr.api_id) }

// SetAPIID sets the Telegram API ID.
func (cfg *ClientConfig) SetAPIID(v int32) { cfg.ptr.api_id = C.int32_t(v) }

// APIHash returns the Telegram API hash.
func (cfg *ClientConfig) APIHash() string { return goStr(cfg.ptr.api_hash) }

// SetAPIHash sets the Telegram API hash.
func (cfg *ClientConfig) SetAPIHash(v string) {
	cs := C.CString(v)
	defer C.free(unsafe.Pointer(cs))
	C.zsys_client_set_api_hash(cfg.ptr, cs)
}

// SessionName returns the session file name.
func (cfg *ClientConfig) SessionName() string { return goStr(cfg.ptr.session_name) }

// SetSessionName sets the session file name.
func (cfg *ClientConfig) SetSessionName(v string) {
	cs := C.CString(v)
	defer C.free(unsafe.Pointer(cs))
	C.zsys_client_set_session_name(cfg.ptr, cs)
}

// Mode returns the client mode (user or bot).
func (cfg *ClientConfig) Mode() ClientMode { return ClientMode(cfg.ptr.mode) }

// SetMode sets the client mode.
func (cfg *ClientConfig) SetMode(v ClientMode) { cfg.ptr.mode = C.ZsysClientMode(v) }

// Phone returns the phone number, or "".
func (cfg *ClientConfig) Phone() string { return goStr(cfg.ptr.phone) }

// SetPhone sets the phone number (empty clears the field).
func (cfg *ClientConfig) SetPhone(v string) {
	cs := cStrOpt(v)
	C.zsys_client_set_phone(cfg.ptr, cs)
	if cs != nil {
		C.free(unsafe.Pointer(cs))
	}
}

// BotToken returns the bot token, or "".
func (cfg *ClientConfig) BotToken() string { return goStr(cfg.ptr.bot_token) }

// SetBotToken sets the bot token (empty clears the field).
func (cfg *ClientConfig) SetBotToken(v string) {
	cs := cStrOpt(v)
	C.zsys_client_set_bot_token(cfg.ptr, cs)
	if cs != nil {
		C.free(unsafe.Pointer(cs))
	}
}

// DeviceModel returns the device model string.
func (cfg *ClientConfig) DeviceModel() string { return goStr(cfg.ptr.device_model) }

// SetDeviceModel sets the device model.
func (cfg *ClientConfig) SetDeviceModel(v string) {
	cs := cStrOpt(v)
	C.zsys_client_set_device_model(cfg.ptr, cs)
	if cs != nil {
		C.free(unsafe.Pointer(cs))
	}
}

// SystemVersion returns the OS/system version string.
func (cfg *ClientConfig) SystemVersion() string { return goStr(cfg.ptr.system_version) }

// SetSystemVersion sets the system version.
func (cfg *ClientConfig) SetSystemVersion(v string) {
	cs := cStrOpt(v)
	C.zsys_client_set_system_version(cfg.ptr, cs)
	if cs != nil {
		C.free(unsafe.Pointer(cs))
	}
}

// AppVersion returns the application version string.
func (cfg *ClientConfig) AppVersion() string { return goStr(cfg.ptr.app_version) }

// SetAppVersion sets the application version.
func (cfg *ClientConfig) SetAppVersion(v string) {
	cs := cStrOpt(v)
	C.zsys_client_set_app_version(cfg.ptr, cs)
	if cs != nil {
		C.free(unsafe.Pointer(cs))
	}
}

// LangCode returns the IETF language tag.
func (cfg *ClientConfig) LangCode() string { return goStr(cfg.ptr.lang_code) }

// SetLangCode sets the language code.
func (cfg *ClientConfig) SetLangCode(v string) {
	cs := cStrOpt(v)
	C.zsys_client_set_lang_code(cfg.ptr, cs)
	if cs != nil {
		C.free(unsafe.Pointer(cs))
	}
}

// LangPack returns the Telegram lang pack name.
func (cfg *ClientConfig) LangPack() string { return goStr(cfg.ptr.lang_pack) }

// SetLangPack sets the lang pack.
func (cfg *ClientConfig) SetLangPack(v string) {
	cs := cStrOpt(v)
	C.zsys_client_set_lang_pack(cfg.ptr, cs)
	if cs != nil {
		C.free(unsafe.Pointer(cs))
	}
}

// ProxyHost returns the proxy hostname, or "".
func (cfg *ClientConfig) ProxyHost() string { return goStr(cfg.ptr.proxy_host) }

// ProxyPort returns the proxy port (0 = disabled).
func (cfg *ClientConfig) ProxyPort() int32 { return int32(cfg.ptr.proxy_port) }

// ProxyUser returns the proxy username, or "".
func (cfg *ClientConfig) ProxyUser() string { return goStr(cfg.ptr.proxy_user) }

// SetProxy configures the proxy (pass empty strings to clear optional fields).
func (cfg *ClientConfig) SetProxy(host string, port int32, user, pass string) {
	hostCS := C.CString(host)
	defer C.free(unsafe.Pointer(hostCS))
	userCS := cStrOpt(user)
	passCS := cStrOpt(pass)
	C.zsys_client_set_proxy(cfg.ptr, hostCS, C.int32_t(port), userCS, passCS)
	if userCS != nil {
		C.free(unsafe.Pointer(userCS))
	}
	if passCS != nil {
		C.free(unsafe.Pointer(passCS))
	}
}

// SleepThreshold returns the max flood-wait sleep seconds.
func (cfg *ClientConfig) SleepThreshold() int { return int(cfg.ptr.sleep_threshold) }

// SetSleepThreshold sets the flood-wait sleep threshold.
func (cfg *ClientConfig) SetSleepThreshold(v int) { cfg.ptr.sleep_threshold = C.int(v) }

// MaxConcurrent returns the max concurrent workers.
func (cfg *ClientConfig) MaxConcurrent() int { return int(cfg.ptr.max_concurrent) }

// SetMaxConcurrent sets the max concurrent workers.
func (cfg *ClientConfig) SetMaxConcurrent(v int) { cfg.ptr.max_concurrent = C.int(v) }

// Validate checks required fields; returns an error with a description on failure.
func (cfg *ClientConfig) Validate() error {
	buf := make([]byte, 256)
	rc := C.zsys_client_config_validate(
		cfg.ptr,
		(*C.char)(unsafe.Pointer(&buf[0])),
		C.size_t(len(buf)),
	)
	if rc != 0 {
		return errors.New(string(buf))
	}
	return nil
}

// ToJSON serialises the config to a JSON string (secrets not included).
func (cfg *ClientConfig) ToJSON() (string, error) {
	raw := C.zsys_client_config_to_json(cfg.ptr)
	if raw == nil {
		return "", errors.New("zsys_client_config_to_json() failed")
	}
	s := C.GoString(raw)
	C.zsys_free(unsafe.Pointer(raw))
	return s, nil
}

// ClientConfigFromJSON deserialises a ClientConfig from a JSON string.
func ClientConfigFromJSON(json string) (*ClientConfig, error) {
	cfg, err := NewClientConfig()
	if err != nil {
		return nil, err
	}
	cs := C.CString(json)
	defer C.free(unsafe.Pointer(cs))
	if C.zsys_client_config_from_json(cfg.ptr, cs) != 0 {
		cfg.Free()
		return nil, errors.New("zsys_client_config_from_json() parse error")
	}
	return cfg, nil
}
