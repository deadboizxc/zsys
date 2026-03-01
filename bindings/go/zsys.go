// Package zsys provides CGo bindings to the zsys C shared library.
//
// The C library (libzsys) must be installed or available as libzsys.so.
// Build with: make build-lib (from the project root).
package zsys

// #cgo LDFLAGS: -lzsys
// #include "../../zsys/include/zsys_core.h"
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
