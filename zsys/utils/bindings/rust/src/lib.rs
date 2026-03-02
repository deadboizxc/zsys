// Rust binding for ZsysUtils — safe wrapper around libzsys_utils.
//
// Build: cargo build
//
// Usage:
//   let u = Utils::new();
//   println!("{}", u.escape_html("<b>hi</b>"));
//   println!("{}", u.format_bytes(1536));
//   let chunks = u.split_text("hello world", 4);

use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_double, c_int, c_long};

#[allow(non_upper_case_globals, non_camel_case_types, dead_code)]
mod ffi {
    use std::os::raw::{c_char, c_double, c_int, c_long};

    extern "C" {
        pub fn zsys_free(ptr: *mut c_char);

        pub fn zsys_escape_html(text: *const c_char, len: usize) -> *mut c_char;
        pub fn zsys_strip_html(text: *const c_char, len: usize) -> *mut c_char;
        pub fn zsys_truncate_text(
            text: *const c_char, len: usize,
            max_chars: usize, suffix: *const c_char,
        ) -> *mut c_char;
        pub fn zsys_split_text(
            text: *const c_char, len: usize, max_chars: usize,
        ) -> *mut *mut c_char;
        pub fn zsys_split_free(chunks: *mut *mut c_char);
        pub fn zsys_get_args(
            text: *const c_char, len: usize, max_split: c_int,
        ) -> *mut *mut c_char;

        pub fn zsys_format_bytes(size: i64) -> *mut c_char;
        pub fn zsys_format_duration(seconds: c_double) -> *mut c_char;
        pub fn zsys_human_time(seconds: c_long, short_fmt: c_int) -> *mut c_char;
        pub fn zsys_parse_duration(text: *const c_char) -> c_long;

        pub fn zsys_format_bold(text: *const c_char, len: usize, escape: c_int)
            -> *mut c_char;
        pub fn zsys_format_italic(text: *const c_char, len: usize, escape: c_int)
            -> *mut c_char;
        pub fn zsys_format_code(text: *const c_char, len: usize, escape: c_int)
            -> *mut c_char;
        pub fn zsys_format_pre(
            text: *const c_char, len: usize,
            lang: *const c_char, escape: c_int,
        ) -> *mut c_char;
        pub fn zsys_format_link(
            text: *const c_char, tlen: usize,
            url:  *const c_char, ulen: usize,
            escape: c_int,
        ) -> *mut c_char;
        pub fn zsys_format_mention(
            text: *const c_char, len: usize,
            user_id: i64, escape: c_int,
        ) -> *mut c_char;
        pub fn zsys_format_underline(text: *const c_char, len: usize) -> *mut c_char;
        pub fn zsys_format_strikethrough(text: *const c_char, len: usize) -> *mut c_char;
        pub fn zsys_format_spoiler(text: *const c_char, len: usize) -> *mut c_char;
        pub fn zsys_format_quote(text: *const c_char, len: usize) -> *mut c_char;
    }
}

/// Take ownership of a zsys heap pointer, convert to String, and free it.
unsafe fn take(ptr: *mut c_char) -> String {
    if ptr.is_null() {
        return String::new();
    }
    let s = CStr::from_ptr(ptr).to_string_lossy().into_owned();
    ffi::zsys_free(ptr);
    s
}

/// Convert a NULL-terminated char** to Vec<String> and free it.
unsafe fn take_arr(pp: *mut *mut c_char) -> Vec<String> {
    if pp.is_null() {
        return Vec::new();
    }
    let mut v = Vec::new();
    let mut i = 0;
    loop {
        let p = *pp.add(i);
        if p.is_null() { break; }
        v.push(CStr::from_ptr(p).to_string_lossy().into_owned());
        i += 1;
    }
    ffi::zsys_split_free(pp);
    v
}

/// Safe Rust wrapper for the zsys utils library.
pub struct Utils;

impl Utils {
    pub fn new() -> Self { Utils }

    // ── text / HTML ──────────────────────────────────────────────────────── //

    pub fn escape_html(&self, text: &str) -> String {
        unsafe { take(ffi::zsys_escape_html(text.as_ptr() as _, text.len())) }
    }

    pub fn strip_html(&self, text: &str) -> String {
        unsafe { take(ffi::zsys_strip_html(text.as_ptr() as _, text.len())) }
    }

    pub fn truncate(&self, text: &str, max_chars: usize, suffix: &str) -> String {
        let suf = CString::new(suffix).unwrap();
        unsafe {
            take(ffi::zsys_truncate_text(
                text.as_ptr() as _, text.len(), max_chars, suf.as_ptr(),
            ))
        }
    }

    pub fn split_text(&self, text: &str, max_chars: usize) -> Vec<String> {
        unsafe {
            take_arr(ffi::zsys_split_text(text.as_ptr() as _, text.len(), max_chars))
        }
    }

    pub fn get_args(&self, text: &str, max_split: i32) -> Vec<String> {
        unsafe {
            take_arr(ffi::zsys_get_args(text.as_ptr() as _, text.len(), max_split))
        }
    }

    // ── numeric formatters ───────────────────────────────────────────────── //

    pub fn format_bytes(&self, size: i64) -> String {
        unsafe { take(ffi::zsys_format_bytes(size)) }
    }

    pub fn format_duration(&self, seconds: f64) -> String {
        unsafe { take(ffi::zsys_format_duration(seconds)) }
    }

    pub fn human_time(&self, seconds: i64, short_fmt: bool) -> String {
        unsafe { take(ffi::zsys_human_time(seconds as c_long, short_fmt as c_int)) }
    }

    pub fn parse_duration(&self, text: &str) -> i64 {
        let c = CString::new(text).unwrap();
        unsafe { ffi::zsys_parse_duration(c.as_ptr()) as i64 }
    }

    // ── HTML formatters ──────────────────────────────────────────────────── //

    pub fn bold(&self, text: &str, escape: bool) -> String {
        unsafe { take(ffi::zsys_format_bold(text.as_ptr() as _, text.len(), escape as _)) }
    }

    pub fn italic(&self, text: &str, escape: bool) -> String {
        unsafe { take(ffi::zsys_format_italic(text.as_ptr() as _, text.len(), escape as _)) }
    }

    pub fn code(&self, text: &str, escape: bool) -> String {
        unsafe { take(ffi::zsys_format_code(text.as_ptr() as _, text.len(), escape as _)) }
    }

    pub fn pre(&self, text: &str, lang: &str, escape: bool) -> String {
        let l = CString::new(lang).unwrap();
        unsafe {
            take(ffi::zsys_format_pre(
                text.as_ptr() as _, text.len(), l.as_ptr(), escape as _,
            ))
        }
    }

    pub fn link(&self, text: &str, url: &str, escape: bool) -> String {
        unsafe {
            take(ffi::zsys_format_link(
                text.as_ptr() as _, text.len(),
                url.as_ptr()  as _, url.len(),
                escape as _,
            ))
        }
    }

    pub fn mention(&self, text: &str, user_id: i64, escape: bool) -> String {
        unsafe {
            take(ffi::zsys_format_mention(
                text.as_ptr() as _, text.len(), user_id, escape as _,
            ))
        }
    }

    pub fn underline(&self, text: &str) -> String {
        unsafe { take(ffi::zsys_format_underline(text.as_ptr() as _, text.len())) }
    }

    pub fn strikethrough(&self, text: &str) -> String {
        unsafe { take(ffi::zsys_format_strikethrough(text.as_ptr() as _, text.len())) }
    }

    pub fn spoiler(&self, text: &str) -> String {
        unsafe { take(ffi::zsys_format_spoiler(text.as_ptr() as _, text.len())) }
    }

    pub fn quote(&self, text: &str) -> String {
        unsafe { take(ffi::zsys_format_quote(text.as_ptr() as _, text.len())) }
    }
}

impl Default for Utils {
    fn default() -> Self { Self::new() }
}

// SAFETY: Utils holds no state — all C functions are thread-safe for reading.
unsafe impl Send for Utils {}
unsafe impl Sync for Utils {}
