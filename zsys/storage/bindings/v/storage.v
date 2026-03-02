// V bindings for zsys/storage (ZsysKV key-value store).
//
// Build with: v -cflags '-I../../c/include' storage.v

module storage

#flag -lzsys_storage
#include "../../c/include/zsys_storage.h"

// ── C declarations ────────────────────────────────────────────────────────────

struct C.ZsysKV {}

type ZsysKVIterFn = fn (key &i8, value &i8, ctx voidptr) int

fn C.zsys_kv_new(initial_cap usize) &C.ZsysKV
fn C.zsys_kv_free(kv &C.ZsysKV)
fn C.zsys_kv_set(kv &C.ZsysKV, key &i8, value &i8) int
fn C.zsys_kv_get(kv &C.ZsysKV, key &i8) &i8
fn C.zsys_kv_del(kv &C.ZsysKV, key &i8) int
fn C.zsys_kv_has(kv &C.ZsysKV, key &i8) int
fn C.zsys_kv_count(kv &C.ZsysKV) usize
fn C.zsys_kv_clear(kv &C.ZsysKV)
fn C.zsys_kv_foreach(kv &C.ZsysKV, fn_ ZsysKVIterFn, ctx voidptr)
fn C.zsys_kv_to_json(kv &C.ZsysKV) &i8
fn C.zsys_kv_from_json(kv &C.ZsysKV, json &i8) int
fn C.zsys_free(ptr voidptr)

// ── Safe V wrapper ────────────────────────────────────────────────────────────

// KV is a safe wrapper around a ZsysKV handle.
pub struct KV {
mut:
	ptr &C.ZsysKV = unsafe { nil }
}

// new creates a new, empty KV store.
// initial_cap = 0 uses the library default (16 slots).
pub fn new_kv(initial_cap usize) !KV {
	ptr := C.zsys_kv_new(initial_cap)
	if ptr == unsafe { nil } {
		return error('zsys_kv_new: allocation failure')
	}
	return KV{ ptr: ptr }
}

// free releases the KV store and all owned memory.
pub fn (mut kv KV) free() {
	if kv.ptr != unsafe { nil } {
		C.zsys_kv_free(kv.ptr)
		kv.ptr = unsafe { nil }
	}
}

// set inserts or updates a key-value pair.
pub fn (kv &KV) set(key string, value string) ! {
	rc := C.zsys_kv_set(kv.ptr, key.str, value.str)
	if rc != 0 {
		return error('zsys_kv_set: allocation failure')
	}
}

// get returns the value for key, or an error if not found.
pub fn (kv &KV) get(key string) !string {
	ptr := C.zsys_kv_get(kv.ptr, key.str)
	if ptr == unsafe { nil } {
		return error('key not found: ${key}')
	}
	return unsafe { cstring_to_vstring(ptr) }
}

// del removes a key; returns an error if not found.
pub fn (kv &KV) del(key string) ! {
	rc := C.zsys_kv_del(kv.ptr, key.str)
	if rc != 0 {
		return error('zsys_kv_del: key not found: ${key}')
	}
}

// has returns true if the key exists.
pub fn (kv &KV) has(key string) bool {
	return C.zsys_kv_has(kv.ptr, key.str) == 1
}

// count returns the number of entries in the store.
pub fn (kv &KV) count() usize {
	return C.zsys_kv_count(kv.ptr)
}

// clear removes all entries.
pub fn (kv &KV) clear() {
	C.zsys_kv_clear(kv.ptr)
}

// IterPair holds one key-value pair collected during foreach.
pub struct IterPair {
pub:
	key   string
	value string
}

// items collects all key-value pairs into a slice.
// (V does not yet support passing arbitrary closures across the C boundary,
// so we use a static trampoline that writes into a heap-allocated buffer.)
pub fn (kv &KV) items() []IterPair {
	mut buf := []IterPair{}
	buf_ptr := &buf

	C.zsys_kv_foreach(kv.ptr, fn (key &i8, value &i8, ctx voidptr) int {
		mut out := unsafe { &[]IterPair(ctx) }
		k := unsafe { cstring_to_vstring(key) }
		v := unsafe { cstring_to_vstring(value) }
		out << IterPair{ key: k, value: v }
		return 0
	}, buf_ptr)

	return buf
}

// to_json serialises the store to a JSON string.
pub fn (kv &KV) to_json() !string {
	ptr := C.zsys_kv_to_json(kv.ptr)
	if ptr == unsafe { nil } {
		return error('zsys_kv_to_json: failure')
	}
	s := unsafe { cstring_to_vstring(ptr) }
	C.zsys_free(ptr)
	return s
}

// from_json deserialises and merges a JSON string into this store.
pub fn (kv &KV) from_json(json string) ! {
	rc := C.zsys_kv_from_json(kv.ptr, json.str)
	if rc != 0 {
		return error('zsys_kv_from_json: parse or allocation error')
	}
}
