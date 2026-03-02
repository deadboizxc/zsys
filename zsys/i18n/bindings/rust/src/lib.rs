// Rust binding for ZsysI18n — generated via bindgen from zsys_core.h
// Build: cargo build (bindgen runs automatically via build.rs)
//
// Usage:
//   let mut t = I18n::new();
//   t.load("en", "/path/to/en.json").unwrap();
//   t.set_lang("en");
//   println!("{}", t.get("hello"));

use std::ffi::{CStr, CString};
use std::ptr::NonNull;

// Raw bindgen-generated bindings (build.rs generates this)
#[allow(non_upper_case_globals, non_camel_case_types, dead_code)]
mod ffi {
    use std::os::raw::{c_char, c_int, c_void};

    pub enum ZsysI18n {}

    extern "C" {
        pub fn zsys_i18n_new() -> *mut ZsysI18n;
        pub fn zsys_i18n_free(i: *mut ZsysI18n);
        pub fn zsys_i18n_load_json(
            i: *mut ZsysI18n,
            lang_code: *const c_char,
            json_path: *const c_char,
        ) -> c_int;
        pub fn zsys_i18n_set_lang(i: *mut ZsysI18n, lang_code: *const c_char);
        pub fn zsys_i18n_get(i: *mut ZsysI18n, key: *const c_char) -> *const c_char;
        pub fn zsys_i18n_get_lang(
            i: *mut ZsysI18n,
            lang_code: *const c_char,
            key: *const c_char,
        ) -> *const c_char;
    }
}

/// Safe Rust wrapper for ZsysI18n.
pub struct I18n {
    ptr: NonNull<ffi::ZsysI18n>,
}

impl I18n {
    pub fn new() -> Self {
        let ptr = unsafe { ffi::zsys_i18n_new() };
        Self {
            ptr: NonNull::new(ptr).expect("zsys_i18n_new returned NULL"),
        }
    }

    /// Load a JSON locale file for lang_code.
    pub fn load(&mut self, lang_code: &str, json_path: &str) -> Result<(), String> {
        let lc = CString::new(lang_code).unwrap();
        let jp = CString::new(json_path).unwrap();
        let rc = unsafe {
            ffi::zsys_i18n_load_json(self.ptr.as_ptr(), lc.as_ptr(), jp.as_ptr())
        };
        if rc == 0 { Ok(()) } else { Err(format!("Failed to load: {json_path}")) }
    }

    /// Set the active language.
    pub fn set_lang(&mut self, lang_code: &str) {
        let lc = CString::new(lang_code).unwrap();
        unsafe { ffi::zsys_i18n_set_lang(self.ptr.as_ptr(), lc.as_ptr()) };
    }

    /// Translate key using the active language.
    pub fn get(&self, key: &str) -> &str {
        let k = CString::new(key).unwrap();
        let r = unsafe { ffi::zsys_i18n_get(self.ptr.as_ptr(), k.as_ptr()) };
        if r.is_null() { key }
        else { unsafe { CStr::from_ptr(r) }.to_str().unwrap_or(key) }
    }

    /// Translate key in a specific language.
    pub fn get_lang<'a>(&self, lang_code: &str, key: &'a str) -> &'a str {
        let lc = CString::new(lang_code).unwrap();
        let k  = CString::new(key).unwrap();
        let r  = unsafe {
            ffi::zsys_i18n_get_lang(self.ptr.as_ptr(), lc.as_ptr(), k.as_ptr())
        };
        if r.is_null() { key }
        else { unsafe { CStr::from_ptr(r) }.to_str().unwrap_or(key) }
    }
}

impl Default for I18n {
    fn default() -> Self { Self::new() }
}

impl Drop for I18n {
    fn drop(&mut self) {
        unsafe { ffi::zsys_i18n_free(self.ptr.as_ptr()) };
    }
}

// SAFETY: ZsysI18n внутри не шарит состояние между потоками
unsafe impl Send for I18n {}
