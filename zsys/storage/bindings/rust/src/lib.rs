//! Safe Rust bindings for zsys/storage (ZsysKV key-value store).

#![allow(non_upper_case_globals, non_camel_case_types, non_snake_case)]

mod sys {
    include!(concat!(env!("OUT_DIR"), "/bindings.rs"));
}

use std::ffi::{CStr, CString};
use std::ops::{Index, IndexMut};

// ── Error type ────────────────────────────────────────────────────────────────

#[derive(Debug)]
pub enum KvError {
    AllocationFailure,
    KeyNotFound(String),
    ParseError,
    NulError(std::ffi::NulError),
}

impl From<std::ffi::NulError> for KvError {
    fn from(e: std::ffi::NulError) -> Self {
        KvError::NulError(e)
    }
}

impl std::fmt::Display for KvError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            KvError::AllocationFailure => write!(f, "allocation failure"),
            KvError::KeyNotFound(k) => write!(f, "key not found: {k}"),
            KvError::ParseError => write!(f, "JSON parse error"),
            KvError::NulError(e) => write!(f, "nul in string: {e}"),
        }
    }
}

impl std::error::Error for KvError {}

// ── KV wrapper ────────────────────────────────────────────────────────────────

/// Safe, owned wrapper around a `ZsysKV` handle.
///
/// Implements [`Drop`] (calls `zsys_kv_free`) and is [`Send`]-safe.
pub struct KV {
    ptr: *mut sys::ZsysKV,
}

// SAFETY: ZsysKV has no thread-local state; access is serialised by Rust's
// borrow checker through &mut KV.
unsafe impl Send for KV {}

impl KV {
    /// Create a new, empty KV store.
    ///
    /// `initial_cap = 0` uses the library default (16 slots).
    pub fn new(initial_cap: usize) -> Result<Self, KvError> {
        let ptr = unsafe { sys::zsys_kv_new(initial_cap) };
        if ptr.is_null() {
            Err(KvError::AllocationFailure)
        } else {
            Ok(KV { ptr })
        }
    }

    /// Insert or update a key-value pair.
    pub fn set(&mut self, key: &str, value: &str) -> Result<(), KvError> {
        let k = CString::new(key)?;
        let v = CString::new(value)?;
        let rc = unsafe { sys::zsys_kv_set(self.ptr, k.as_ptr(), v.as_ptr()) };
        if rc == 0 { Ok(()) } else { Err(KvError::AllocationFailure) }
    }

    /// Look up a value by key; returns `None` if not present.
    pub fn get(&self, key: &str) -> Option<String> {
        let k = CString::new(key).ok()?;
        let ptr = unsafe { sys::zsys_kv_get(self.ptr, k.as_ptr()) };
        if ptr.is_null() {
            None
        } else {
            Some(unsafe { CStr::from_ptr(ptr) }.to_string_lossy().into_owned())
        }
    }

    /// Delete a key; returns `Err` if the key was not found.
    pub fn del(&mut self, key: &str) -> Result<(), KvError> {
        let k = CString::new(key)?;
        let rc = unsafe { sys::zsys_kv_del(self.ptr, k.as_ptr()) };
        if rc == 0 {
            Ok(())
        } else {
            Err(KvError::KeyNotFound(key.to_owned()))
        }
    }

    /// Return `true` if the key exists.
    pub fn has(&self, key: &str) -> bool {
        let Ok(k) = CString::new(key) else { return false };
        unsafe { sys::zsys_kv_has(self.ptr, k.as_ptr()) } == 1
    }

    /// Number of entries in the store.
    pub fn count(&self) -> usize {
        unsafe { sys::zsys_kv_count(self.ptr) }
    }

    /// Remove all entries.
    pub fn clear(&mut self) {
        unsafe { sys::zsys_kv_clear(self.ptr) }
    }

    /// Iterate over all key-value pairs, calling `f` for each.
    ///
    /// Iteration stops early if `f` returns `false`.
    pub fn foreach<F>(&self, mut f: F)
    where
        F: FnMut(&str, &str) -> bool,
    {
        // Pass a raw pointer to the closure as the ctx argument.
        let f_ptr = &mut f as *mut F as *mut std::ffi::c_void;

        unsafe extern "C" fn trampoline<F>(
            key: *const std::ffi::c_char,
            val: *const std::ffi::c_char,
            ctx: *mut std::ffi::c_void,
        ) -> std::ffi::c_int
        where
            F: FnMut(&str, &str) -> bool,
        {
            let f = &mut *(ctx as *mut F);
            let k = CStr::from_ptr(key).to_str().unwrap_or("");
            let v = CStr::from_ptr(val).to_str().unwrap_or("");
            if f(k, v) { 0 } else { 1 }
        }

        unsafe {
            sys::zsys_kv_foreach(self.ptr, Some(trampoline::<F>), f_ptr);
        }
    }

    /// Collect all key-value pairs into a `Vec`.
    pub fn items(&self) -> Vec<(String, String)> {
        let mut out = Vec::with_capacity(self.count());
        self.foreach(|k, v| {
            out.push((k.to_owned(), v.to_owned()));
            true
        });
        out
    }

    // ── Serialisation ─────────────────────────────────────────────────────

    /// Serialise the store to a JSON string.
    pub fn to_json(&self) -> Result<String, KvError> {
        let ptr = unsafe { sys::zsys_kv_to_json(self.ptr) };
        if ptr.is_null() {
            return Err(KvError::AllocationFailure);
        }
        let s = unsafe { CStr::from_ptr(ptr) }.to_string_lossy().into_owned();
        unsafe { sys::zsys_free(ptr as *mut std::ffi::c_void) };
        Ok(s)
    }

    /// Deserialise and merge a JSON string into this store.
    pub fn from_json(&mut self, json: &str) -> Result<(), KvError> {
        let j = CString::new(json)?;
        let rc = unsafe { sys::zsys_kv_from_json(self.ptr, j.as_ptr()) };
        if rc == 0 { Ok(()) } else { Err(KvError::ParseError) }
    }
}

impl Drop for KV {
    fn drop(&mut self) {
        if !self.ptr.is_null() {
            unsafe { sys::zsys_kv_free(self.ptr) };
            self.ptr = std::ptr::null_mut();
        }
    }
}

// ── Index / IndexMut ──────────────────────────────────────────────────────────

impl Index<&str> for KV {
    type Output = str;

    /// Panics if the key does not exist.
    fn index(&self, key: &str) -> &str {
        let k = CString::new(key).expect("key contains NUL");
        let ptr = unsafe { sys::zsys_kv_get(self.ptr, k.as_ptr()) };
        assert!(!ptr.is_null(), "KV: key not found: {key}");
        // SAFETY: pointer is valid until next set/del on this key.
        unsafe { CStr::from_ptr(ptr).to_str().expect("value is not UTF-8") }
    }
}

/// A temporary helper returned by `IndexMut` that writes on `Drop`.
pub struct KvEntry<'a> {
    kv: &'a mut KV,
    key: &'a str,
    value: String,
}

impl<'a> std::ops::DerefMut for KvEntry<'a> {
    fn deref_mut(&mut self) -> &mut String {
        &mut self.value
    }
}

impl<'a> std::ops::Deref for KvEntry<'a> {
    type Target = String;
    fn deref(&self) -> &String {
        &self.value
    }
}

impl<'a> Drop for KvEntry<'a> {
    fn drop(&mut self) {
        let _ = self.kv.set(self.key, &self.value);
    }
}

impl IndexMut<&str> for KV {
    fn index_mut(&mut self, key: &str) -> &mut String {
        // We cannot return a reference into the C-owned buffer, so we store
        // a local String and flush it back on Drop via KvEntry.
        // This is the idiomatic pattern when IndexMut targets C memory.
        // For ergonomic use prefer `kv.set(key, value)` directly.
        unimplemented!(
            "IndexMut on ZsysKV is not zero-cost — use kv.set(\"{key}\", value) instead"
        )
    }
}
