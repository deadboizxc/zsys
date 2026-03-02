// Package storage provides cgo bindings for the zsys/storage ZsysKV
// key-value store.
package storage

/*
#cgo LDFLAGS: -lzsys_storage
#include "../../c/include/zsys_storage.h"
#include <stdlib.h>

// Go cannot use variadic-C-function pointers directly, so we declare a
// static trampoline that is callable from Go via cgo.
extern int goIterCallback(const char *key, const char *value, void *ctx);
*/
import "C"
import (
	"errors"
	"runtime"
	"unsafe"
)

// IterFunc is the callback type used by KV.Foreach.
// Return false to stop iteration.
type IterFunc func(key, value string) bool

// KV wraps a ZsysKV opaque pointer and provides a safe Go interface.
type KV struct {
	ptr *C.ZsysKV
}

// New creates a new, empty KV store.
// initialCap = 0 uses the library default (16 slots).
func New(initialCap int) (*KV, error) {
	ptr := C.zsys_kv_new(C.size_t(initialCap))
	if ptr == nil {
		return nil, errors.New("zsys_kv_new: allocation failure")
	}
	kv := &KV{ptr: ptr}
	runtime.SetFinalizer(kv, (*KV).Free)
	return kv, nil
}

// Free releases the KV store and all owned memory.
// Safe to call multiple times.
func (kv *KV) Free() {
	if kv.ptr != nil {
		C.zsys_kv_free(kv.ptr)
		kv.ptr = nil
	}
	runtime.SetFinalizer(kv, nil)
}

// Set inserts or updates a key-value pair.
func (kv *KV) Set(key, value string) error {
	k := C.CString(key)
	v := C.CString(value)
	defer C.free(unsafe.Pointer(k))
	defer C.free(unsafe.Pointer(v))
	if rc := C.zsys_kv_set(kv.ptr, k, v); rc != 0 {
		return errors.New("zsys_kv_set: allocation failure")
	}
	return nil
}

// Get returns the value for key, or ("", false) if not found.
func (kv *KV) Get(key string) (string, bool) {
	k := C.CString(key)
	defer C.free(unsafe.Pointer(k))
	ptr := C.zsys_kv_get(kv.ptr, k)
	if ptr == nil {
		return "", false
	}
	return C.GoString(ptr), true
}

// Del deletes a key. Returns an error if the key was not found.
func (kv *KV) Del(key string) error {
	k := C.CString(key)
	defer C.free(unsafe.Pointer(k))
	if rc := C.zsys_kv_del(kv.ptr, k); rc != 0 {
		return errors.New("zsys_kv_del: key not found: " + key)
	}
	return nil
}

// Has returns true if the key exists.
func (kv *KV) Has(key string) bool {
	k := C.CString(key)
	defer C.free(unsafe.Pointer(k))
	return C.zsys_kv_has(kv.ptr, k) == 1
}

// Count returns the number of entries in the store.
func (kv *KV) Count() int {
	return int(C.zsys_kv_count(kv.ptr))
}

// Clear removes all entries.
func (kv *KV) Clear() {
	C.zsys_kv_clear(kv.ptr)
}

// iterState is heap-allocated so its pointer survives the cgo boundary.
type iterState struct {
	fn  IterFunc
	err error
}

//export goIterCallback
func goIterCallback(key, value *C.char, ctx unsafe.Pointer) C.int {
	state := (*iterState)(ctx)
	if !state.fn(C.GoString(key), C.GoString(value)) {
		return 1
	}
	return 0
}

// Foreach iterates over all key-value pairs in undefined order.
// Stops early if fn returns false.
func (kv *KV) Foreach(fn IterFunc) {
	state := &iterState{fn: fn}
	C.zsys_kv_foreach(
		kv.ptr,
		(C.ZsysKVIterFn)(C.goIterCallback),
		unsafe.Pointer(state),
	)
}

// Items returns all key-value pairs as a slice of [2]string.
func (kv *KV) Items() [][2]string {
	out := make([][2]string, 0, kv.Count())
	kv.Foreach(func(k, v string) bool {
		out = append(out, [2]string{k, v})
		return true
	})
	return out
}

// ToJSON serialises the store to a JSON string.
// The caller receives a Go string; no manual free is needed.
func (kv *KV) ToJSON() (string, error) {
	ptr := C.zsys_kv_to_json(kv.ptr)
	if ptr == nil {
		return "", errors.New("zsys_kv_to_json: failure")
	}
	s := C.GoString(ptr)
	C.zsys_free(unsafe.Pointer(ptr))
	return s, nil
}

// FromJSON deserialises and merges a JSON string into this store.
func (kv *KV) FromJSON(json string) error {
	j := C.CString(json)
	defer C.free(unsafe.Pointer(j))
	if rc := C.zsys_kv_from_json(kv.ptr, j); rc != 0 {
		return errors.New("zsys_kv_from_json: parse or allocation error")
	}
	return nil
}
