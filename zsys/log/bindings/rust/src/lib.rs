// Rust binding for zsys_log — safe wrapper around libzsys_log.so
//
// Build: cargo build
//
// Usage:
//   let colored = Log::ansi_color("hello", "31");
//   let json    = Log::format_json_log("INFO", "started", "2024-01-01T00:00:00Z");
//   let boxx    = Log::print_box("title", 2);
//   let sep     = Log::print_separator("─", 40);
//   let prog    = Log::print_progress(7, 10, "Loading", 20);

use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_int};

#[allow(non_upper_case_globals, non_camel_case_types, dead_code)]
mod ffi {
    use std::os::raw::{c_char, c_int};

    extern "C" {
        pub fn zsys_ansi_color(text: *const c_char, code: *const c_char) -> *mut c_char;
        pub fn zsys_format_json_log(
            level:   *const c_char,
            message: *const c_char,
            ts:      *const c_char,
        ) -> *mut c_char;
        pub fn zsys_print_box_str(text: *const c_char, padding: c_int) -> *mut c_char;
        pub fn zsys_print_separator_str(ch: *const c_char, length: c_int) -> *mut c_char;
        pub fn zsys_print_progress_str(
            current:    c_int,
            total:      c_int,
            prefix:     *const c_char,
            bar_length: c_int,
        ) -> *mut c_char;
        pub fn free(ptr: *mut std::os::raw::c_void);
    }
}

/// Owned heap string returned by a zsys_log function.
struct ZsysString(*mut c_char);

impl ZsysString {
    fn as_str(&self) -> &str {
        unsafe { CStr::from_ptr(self.0).to_str().unwrap_or("") }
    }
    fn into_string(self) -> String {
        self.as_str().to_owned()
    }
}

impl Drop for ZsysString {
    fn drop(&mut self) {
        if !self.0.is_null() {
            unsafe { ffi::free(self.0 as *mut _) };
        }
    }
}

/// Stateless wrapper around the zsys_log C functions.
pub struct Log;

impl Log {
    /// Wrap text with an ANSI escape sequence (e.g. code="31" for red).
    pub fn ansi_color(text: &str, code: &str) -> String {
        let t = CString::new(text).unwrap();
        let c = CString::new(code).unwrap();
        let r = unsafe { ffi::zsys_ansi_color(t.as_ptr(), c.as_ptr()) };
        assert!(!r.is_null(), "zsys_ansi_color returned NULL");
        ZsysString(r).into_string()
    }

    /// Format a JSON log line: {"level":"…","message":"…","ts":"…"}.
    pub fn format_json_log(level: &str, message: &str, ts: &str) -> String {
        let l = CString::new(level).unwrap();
        let m = CString::new(message).unwrap();
        let t = CString::new(ts).unwrap();
        let r = unsafe { ffi::zsys_format_json_log(l.as_ptr(), m.as_ptr(), t.as_ptr()) };
        assert!(!r.is_null(), "zsys_format_json_log returned NULL");
        ZsysString(r).into_string()
    }

    /// Render a Unicode box (╔══╗ style) around text.
    pub fn print_box(text: &str, padding: i32) -> String {
        let t = CString::new(text).unwrap();
        let r = unsafe { ffi::zsys_print_box_str(t.as_ptr(), padding as c_int) };
        assert!(!r.is_null(), "zsys_print_box_str returned NULL");
        ZsysString(r).into_string()
    }

    /// Repeat ch length times to build a separator line.
    pub fn print_separator(ch: &str, length: i32) -> String {
        let c = CString::new(ch).unwrap();
        let r = unsafe { ffi::zsys_print_separator_str(c.as_ptr(), length as c_int) };
        assert!(!r.is_null(), "zsys_print_separator_str returned NULL");
        ZsysString(r).into_string()
    }

    /// Render a text progress bar: [###---] current/total (N%).
    pub fn print_progress(current: i32, total: i32, prefix: &str, bar_length: i32) -> String {
        let p = CString::new(prefix).unwrap();
        let r = unsafe {
            ffi::zsys_print_progress_str(
                current as c_int, total as c_int,
                p.as_ptr(), bar_length as c_int,
            )
        };
        assert!(!r.is_null(), "zsys_print_progress_str returned NULL");
        ZsysString(r).into_string()
    }
}
