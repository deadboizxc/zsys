// zsys modules bindings for V
// Wraps ZsysRouter and ZsysRegistry from libzsys_core.so.
//
// Build: v -cflags '-I../../c/include' modules.v

module modules

#flag -lzsys_core
#include "zsys_core.h"

// ── C declarations ────────────────────────────────────────────────────────

struct C.ZsysRouter {}
struct C.ZsysRegistry {}

fn C.zsys_router_new() &C.ZsysRouter
fn C.zsys_router_free(r &C.ZsysRouter)
fn C.zsys_router_add(r &C.ZsysRouter, trigger &char, handler_id int) int
fn C.zsys_router_remove(r &C.ZsysRouter, trigger &char) int
fn C.zsys_router_lookup(r &C.ZsysRouter, trigger &char) int
fn C.zsys_router_count(r &C.ZsysRouter) usize
fn C.zsys_router_clear(r &C.ZsysRouter)

fn C.zsys_registry_new() &C.ZsysRegistry
fn C.zsys_registry_free(reg &C.ZsysRegistry)
fn C.zsys_registry_register(reg &C.ZsysRegistry, name &char, handler_id int, description &char, category &char) int
fn C.zsys_registry_unregister(reg &C.ZsysRegistry, name &char) int
fn C.zsys_registry_get(reg &C.ZsysRegistry, name &char) int
fn C.zsys_registry_info(reg &C.ZsysRegistry, name &char, out_desc &char, desc_len usize, out_cat &char, cat_len usize) int
fn C.zsys_registry_count(reg &C.ZsysRegistry) usize
fn C.zsys_registry_name_at(reg &C.ZsysRegistry, i usize) &char

// ── Router ────────────────────────────────────────────────────────────────

// Router wraps ZsysRouter — trigger → handler_id open-addressing hash table.
// Lookup is case-insensitive.
pub struct Router {
mut:
	ptr &C.ZsysRouter
}

// new_router creates an empty Router.
pub fn new_router() !Router {
	ptr := C.zsys_router_new()
	if ptr == unsafe { nil } {
		return error('zsys_router_new() returned null')
	}
	return Router{ ptr: ptr }
}

// free releases the underlying C resource. Call when done.
pub fn (mut r Router) free() {
	if r.ptr != unsafe { nil } {
		C.zsys_router_free(r.ptr)
		r.ptr = unsafe { nil }
	}
}

// add adds or updates a trigger → handler_id mapping.
pub fn (mut r Router) add(trigger string, handler_id int) ! {
	if C.zsys_router_add(r.ptr, trigger.str, handler_id) != 0 {
		return error('zsys_router_add failed for trigger: ${trigger}')
	}
}

// remove removes a trigger. Returns true if it existed.
pub fn (mut r Router) remove(trigger string) bool {
	return C.zsys_router_remove(r.ptr, trigger.str) == 0
}

// lookup returns handler_id for trigger (case-insensitive), or -1 if absent.
pub fn (mut r Router) lookup(trigger string) int {
	return C.zsys_router_lookup(r.ptr, trigger.str)
}

// count returns the number of registered triggers.
pub fn (r &Router) count() usize {
	return C.zsys_router_count(r.ptr)
}

// clear removes all entries.
pub fn (mut r Router) clear() {
	C.zsys_router_clear(r.ptr)
}

// ── Registry ──────────────────────────────────────────────────────────────

// Registry wraps ZsysRegistry — dynamic array of name → handler_id entries.
pub struct Registry {
mut:
	ptr &C.ZsysRegistry
}

// new_registry creates an empty Registry.
pub fn new_registry() !Registry {
	ptr := C.zsys_registry_new()
	if ptr == unsafe { nil } {
		return error('zsys_registry_new() returned null')
	}
	return Registry{ ptr: ptr }
}

// free releases the underlying C resource. Call when done.
pub fn (mut reg Registry) free() {
	if reg.ptr != unsafe { nil } {
		C.zsys_registry_free(reg.ptr)
		reg.ptr = unsafe { nil }
	}
}

// register registers a handler. Pass '' for description/category to omit.
pub fn (mut reg Registry) register(name string, handler_id int, description string, category string) ! {
	d := if description.len > 0 { description.str } else { unsafe { &char(0) } }
	c := if category.len > 0    { category.str }    else { unsafe { &char(0) } }
	if C.zsys_registry_register(reg.ptr, name.str, handler_id, d, c) != 0 {
		return error('zsys_registry_register failed for: ${name}')
	}
}

// unregister removes a handler by name. Returns true if it existed.
pub fn (mut reg Registry) unregister(name string) bool {
	return C.zsys_registry_unregister(reg.ptr, name.str) == 0
}

// get returns the handler_id for name, or -1 if not found.
pub fn (mut reg Registry) get(name string) int {
	return C.zsys_registry_get(reg.ptr, name.str)
}

// info returns (description, category) for a registered name.
pub fn (mut reg Registry) info(name string) !(string, string) {
	desc_buf := []u8{len: 256}
	cat_buf  := []u8{len: 128}
	rc := C.zsys_registry_info(
		reg.ptr, name.str,
		unsafe { &char(desc_buf.data) }, usize(desc_buf.len),
		unsafe { &char(cat_buf.data) },  usize(cat_buf.len),
	)
	if rc != 0 {
		return error('zsys_registry_info: not found: ${name}')
	}
	desc := unsafe { cstring_to_vstring(&char(desc_buf.data)) }
	cat  := unsafe { cstring_to_vstring(&char(cat_buf.data)) }
	return desc, cat
}

// count returns the number of registered entries.
pub fn (reg &Registry) count() usize {
	return C.zsys_registry_count(reg.ptr)
}

// name_at returns the handler name at index i, or '' if out of bounds.
pub fn (reg &Registry) name_at(i usize) string {
	p := C.zsys_registry_name_at(reg.ptr, i)
	if p == unsafe { nil } {
		return ''
	}
	return unsafe { cstring_to_vstring(p) }
}

// names returns all registered handler names.
pub fn (reg &Registry) names() []string {
	n := reg.count()
	mut result := []string{cap: int(n)}
	for i := usize(0); i < n; i++ {
		s := reg.name_at(i)
		if s != '' {
			result << s
		}
	}
	return result
}
