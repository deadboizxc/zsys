// Package modules provides cgo bindings for ZsysRouter and ZsysRegistry
// from libzsys_core.so.
package modules

/*
#cgo CFLAGS:  -I../../c/include
#cgo LDFLAGS: -lzsys_core

#include "zsys_core.h"
#include <stdlib.h>
*/
import "C"
import (
	"errors"
	"runtime"
	"unsafe"
)

// ── errors ────────────────────────────────────────────────────────────────

var (
	ErrOperationFailed = errors.New("zsys: operation failed")
	ErrNotFound        = errors.New("zsys: entry not found")
	ErrAlloc           = errors.New("zsys: allocation failed")
)

// ── Router ────────────────────────────────────────────────────────────────

// Router wraps ZsysRouter — a trigger → handler_id open-addressing hash
// table. Lookup is case-insensitive.
type Router struct {
	ptr *C.ZsysRouter
}

// NewRouter creates an empty Router.
func NewRouter() (*Router, error) {
	ptr := C.zsys_router_new()
	if ptr == nil {
		return nil, ErrAlloc
	}
	r := &Router{ptr: ptr}
	runtime.SetFinalizer(r, (*Router).Close)
	return r, nil
}

// Close releases the underlying C resource.
func (r *Router) Close() {
	if r.ptr != nil {
		C.zsys_router_free(r.ptr)
		r.ptr = nil
	}
	runtime.SetFinalizer(r, nil)
}

// Add adds or updates a trigger → handler_id mapping.
func (r *Router) Add(trigger string, handlerID int) error {
	cs := C.CString(trigger)
	defer C.free(unsafe.Pointer(cs))
	if C.zsys_router_add(r.ptr, cs, C.int(handlerID)) != 0 {
		return ErrOperationFailed
	}
	return nil
}

// Remove removes a trigger. Returns ErrNotFound if absent.
func (r *Router) Remove(trigger string) error {
	cs := C.CString(trigger)
	defer C.free(unsafe.Pointer(cs))
	if C.zsys_router_remove(r.ptr, cs) != 0 {
		return ErrNotFound
	}
	return nil
}

// Lookup returns (handlerID, true) for trigger, or (-1, false) if not found.
func (r *Router) Lookup(trigger string) (int, bool) {
	cs := C.CString(trigger)
	defer C.free(unsafe.Pointer(cs))
	id := int(C.zsys_router_lookup(r.ptr, cs))
	return id, id != -1
}

// Count returns the number of registered triggers.
func (r *Router) Count() int {
	return int(C.zsys_router_count(r.ptr))
}

// Clear removes all entries.
func (r *Router) Clear() {
	C.zsys_router_clear(r.ptr)
}

// ── Registry ──────────────────────────────────────────────────────────────

// Registry wraps ZsysRegistry — a dynamic array of name → handler_id
// entries with optional description and category metadata.
type Registry struct {
	ptr *C.ZsysRegistry
}

// NewRegistry creates an empty Registry.
func NewRegistry() (*Registry, error) {
	ptr := C.zsys_registry_new()
	if ptr == nil {
		return nil, ErrAlloc
	}
	reg := &Registry{ptr: ptr}
	runtime.SetFinalizer(reg, (*Registry).Close)
	return reg, nil
}

// Close releases the underlying C resource.
func (reg *Registry) Close() {
	if reg.ptr != nil {
		C.zsys_registry_free(reg.ptr)
		reg.ptr = nil
	}
	runtime.SetFinalizer(reg, nil)
}

// Register registers a handler. description and category may be empty strings
// to pass NULL to the C layer.
func (reg *Registry) Register(name string, handlerID int, description, category string) error {
	cs := C.CString(name)
	defer C.free(unsafe.Pointer(cs))

	var desc, cat *C.char
	if description != "" {
		desc = C.CString(description)
		defer C.free(unsafe.Pointer(desc))
	}
	if category != "" {
		cat = C.CString(category)
		defer C.free(unsafe.Pointer(cat))
	}

	if C.zsys_registry_register(reg.ptr, cs, C.int(handlerID), desc, cat) != 0 {
		return ErrOperationFailed
	}
	return nil
}

// Unregister removes a handler by name. Returns ErrNotFound if absent.
func (reg *Registry) Unregister(name string) error {
	cs := C.CString(name)
	defer C.free(unsafe.Pointer(cs))
	if C.zsys_registry_unregister(reg.ptr, cs) != 0 {
		return ErrNotFound
	}
	return nil
}

// Get returns (handlerID, true) for name, or (-1, false) if not found.
func (reg *Registry) Get(name string) (int, bool) {
	cs := C.CString(name)
	defer C.free(unsafe.Pointer(cs))
	id := int(C.zsys_registry_get(reg.ptr, cs))
	return id, id != -1
}

// Info returns the description and category strings for a registered name.
func (reg *Registry) Info(name string) (desc, cat string, err error) {
	cs := C.CString(name)
	defer C.free(unsafe.Pointer(cs))

	descBuf := make([]C.char, 256)
	catBuf  := make([]C.char, 128)

	rc := C.zsys_registry_info(
		reg.ptr, cs,
		&descBuf[0], 256,
		&catBuf[0],  128,
	)
	if rc != 0 {
		return "", "", ErrNotFound
	}
	return C.GoString(&descBuf[0]), C.GoString(&catBuf[0]), nil
}

// Count returns the number of registered entries.
func (reg *Registry) Count() int {
	return int(C.zsys_registry_count(reg.ptr))
}

// NameAt returns the handler name at index i, or "" if out of bounds.
func (reg *Registry) NameAt(i int) string {
	p := C.zsys_registry_name_at(reg.ptr, C.size_t(i))
	if p == nil {
		return ""
	}
	return C.GoString(p)
}

// Names returns all registered handler names.
func (reg *Registry) Names() []string {
	n := reg.Count()
	out := make([]string, 0, n)
	for i := 0; i < n; i++ {
		if name := reg.NameAt(i); name != "" {
			out = append(out, name)
		}
	}
	return out
}
