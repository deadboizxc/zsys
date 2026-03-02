// V (Vlang) binding for ZsysI18n.
//
// Build: v -cflags '-lzsys_core' main.v
// Usage:
//   mut t := i18n.new_i18n()
//   defer t.free()
//   t.load('en', '/path/to/en.json') or { panic(err) }
//   t.set_lang('en')
//   println(t.get('hello'))

module i18n

#flag -lzsys_core
#include "../../c/include/zsys_core.h"

struct C.ZsysI18n {}

fn C.zsys_i18n_new() &C.ZsysI18n
fn C.zsys_i18n_free(i &C.ZsysI18n)
fn C.zsys_i18n_load_json(i &C.ZsysI18n, lang_code &char, json_path &char) int
fn C.zsys_i18n_set_lang(i &C.ZsysI18n, lang_code &char)
fn C.zsys_i18n_get(i &C.ZsysI18n, key &char) &char
fn C.zsys_i18n_get_lang(i &C.ZsysI18n, lang_code &char, key &char) &char

// I18n is a safe V wrapper around ZsysI18n.
pub struct I18n {
mut:
    ptr &C.ZsysI18n = unsafe { nil }
}

// new_i18n creates a new I18n context.
pub fn new_i18n() &I18n {
    ptr := C.zsys_i18n_new()
    assert ptr != unsafe { nil }, 'zsys_i18n_new returned NULL'
    return &I18n{ ptr: ptr }
}

// free releases the underlying C resources.
pub fn (mut t I18n) free() {
    if t.ptr != unsafe { nil } {
        C.zsys_i18n_free(t.ptr)
        t.ptr = unsafe { nil }
    }
}

// load loads a JSON locale file for lang_code.
pub fn (mut t I18n) load(lang_code string, json_path string) ! {
    rc := C.zsys_i18n_load_json(t.ptr, lang_code.str, json_path.str)
    if rc != 0 {
        return error('failed to load locale: ${json_path}')
    }
}

// set_lang sets the active language.
pub fn (mut t I18n) set_lang(lang_code string) {
    C.zsys_i18n_set_lang(t.ptr, lang_code.str)
}

// get translates key using the active language.
pub fn (t I18n) get(key string) string {
    r := C.zsys_i18n_get(t.ptr, key.str)
    if r == unsafe { nil } { return key }
    return unsafe { cstring_to_vstring(r) }
}

// get_lang translates key in a specific language.
pub fn (t I18n) get_lang(lang_code string, key string) string {
    r := C.zsys_i18n_get_lang(t.ptr, lang_code.str, key.str)
    if r == unsafe { nil } { return key }
    return unsafe { cstring_to_vstring(r) }
}
