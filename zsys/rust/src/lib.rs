//! zsys — Rust bindings to the zsys C core library.
//!
//! Generated FFI is in `bindings` (from build.rs + bindgen).
//! This module wraps the unsafe C calls in safe Rust functions.

#![allow(non_upper_case_globals, non_camel_case_types, dead_code)]

use std::ffi::{CStr, CString};

mod bindings {
    #![allow(non_upper_case_globals, non_camel_case_types, dead_code)]
    include!(concat!(env!("OUT_DIR"), "/zsys_bindings.rs"));
}

fn to_cstr(s: &str) -> CString {
    CString::new(s).unwrap_or_default()
}

fn from_zsys_ptr(ptr: *mut i8) -> Option<String> {
    if ptr.is_null() {
        return None;
    }
    let s = unsafe { CStr::from_ptr(ptr) }
        .to_string_lossy()
        .into_owned();
    unsafe { bindings::zsys_free(ptr) };
    Some(s)
}

/// Escape HTML special characters.
pub fn escape_html(text: &str) -> String {
    let cs = to_cstr(text);
    let r = unsafe { bindings::zsys_escape_html(cs.as_ptr(), text.len()) };
    from_zsys_ptr(r).unwrap_or_else(|| text.to_owned())
}

/// Format bytes as human-readable string ("1.5 KB").
pub fn format_bytes(size: i64) -> String {
    let r = unsafe { bindings::zsys_format_bytes(size) };
    from_zsys_ptr(r).unwrap_or_default()
}

/// Format seconds as "1h 2m 3s".
pub fn format_duration(seconds: f64) -> String {
    let r = unsafe { bindings::zsys_format_duration(seconds) };
    from_zsys_ptr(r).unwrap_or_default()
}

/// Format seconds as Russian human time.
pub fn human_time(seconds: i64, short: bool) -> String {
    let r = unsafe { bindings::zsys_human_time(seconds as _, short as _) };
    from_zsys_ptr(r).unwrap_or_default()
}

/// Parse duration string ("30m", "1h30m") → seconds. Returns None on error.
pub fn parse_duration(text: &str) -> Option<i64> {
    let cs = to_cstr(text);
    let r = unsafe { bindings::zsys_parse_duration(cs.as_ptr()) };
    if r < 0 { None } else { Some(r as i64) }
}

/// Wrap text in HTML <b> tags.
pub fn format_bold(text: &str, escape: bool) -> String {
    let cs = to_cstr(text);
    let r = unsafe { bindings::zsys_format_bold(cs.as_ptr(), text.len(), escape as _) };
    from_zsys_ptr(r).unwrap_or_else(|| text.to_owned())
}

/// Wrap text in HTML <code> tags.
pub fn format_code(text: &str, escape: bool) -> String {
    let cs = to_cstr(text);
    let r = unsafe { bindings::zsys_format_code(cs.as_ptr(), text.len(), escape as _) };
    from_zsys_ptr(r).unwrap_or_else(|| text.to_owned())
}

/// Wrap text with ANSI color escape.
pub fn ansi_color(text: &str, code: &str) -> String {
    let ct = to_cstr(text);
    let cc = to_cstr(code);
    let r = unsafe { bindings::zsys_ansi_color(ct.as_ptr(), cc.as_ptr()) };
    from_zsys_ptr(r).unwrap_or_else(|| text.to_owned())
}

/// Returns true if text starts with one of prefixes followed by a trigger.
pub fn match_prefix(text: &str, prefixes: &[&str], triggers: &[&str]) -> bool {
    let ct = to_cstr(text);
    let cpfx: Vec<CString> = prefixes.iter().map(|s| to_cstr(s)).collect();
    let ctrg: Vec<CString> = triggers.iter().map(|s| to_cstr(s)).collect();
    let pfx_ptrs: Vec<*const i8> = cpfx.iter().map(|s| s.as_ptr()).collect();
    let trg_ptrs: Vec<*const i8> = ctrg.iter().map(|s| s.as_ptr()).collect();
    let r = unsafe {
        bindings::zsys_match_prefix(
            ct.as_ptr(),
            pfx_ptrs.as_ptr(), pfx_ptrs.len() as _,
            trg_ptrs.as_ptr(), trg_ptrs.len() as _,
        )
    };
    r != 0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_escape_html() {
        assert_eq!(escape_html("<b>test</b>"), "&lt;b&gt;test&lt;/b&gt;");
    }

    #[test]
    fn test_format_bytes() {
        assert_eq!(format_bytes(1536), "1.5 KB");
    }

    #[test]
    fn test_parse_duration() {
        assert_eq!(parse_duration("1h30m"), Some(5400));
        assert_eq!(parse_duration("30s"), Some(30));
    }

    #[test]
    fn test_format_bold() {
        assert_eq!(format_bold("hello", false), "<b>hello</b>");
    }
}
