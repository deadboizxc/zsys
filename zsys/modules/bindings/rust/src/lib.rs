//! Safe Rust wrappers for `ZsysRouter` and `ZsysRegistry`.
//!
//! Both types implement `Drop` (automatic `*_free`) and `Send`.
//! Ownership is exclusive; there is no shared-reference API to avoid
//! aliasing issues with the opaque C pointers.

#![allow(non_upper_case_globals, non_camel_case_types, non_snake_case)]

mod ffi {
    include!(concat!(env!("OUT_DIR"), "/bindings.rs"));
}

use std::ffi::{CStr, CString, NulError};

// ── error type ────────────────────────────────────────────────────────────

#[derive(Debug)]
pub enum ZsysError {
    NulByte(NulError),
    OperationFailed(&'static str),
    NotFound,
    AllocationFailed,
}

impl std::fmt::Display for ZsysError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ZsysError::NulByte(e)           => write!(f, "NUL byte in string: {e}"),
            ZsysError::OperationFailed(msg) => write!(f, "operation failed: {msg}"),
            ZsysError::NotFound             => write!(f, "entry not found"),
            ZsysError::AllocationFailed     => write!(f, "allocation failed"),
        }
    }
}

impl std::error::Error for ZsysError {}

impl From<NulError> for ZsysError {
    fn from(e: NulError) -> Self { ZsysError::NulByte(e) }
}

// ── Router ────────────────────────────────────────────────────────────────

/// Trigger → handler_id open-addressing hash table.
/// Lookup is case-insensitive.
pub struct Router {
    ptr: *mut ffi::ZsysRouter,
}

// SAFETY: ZsysRouter is not internally thread-shared; the pointer is
// owned exclusively by this wrapper.
unsafe impl Send for Router {}

impl Router {
    /// Create an empty router.
    pub fn new() -> Result<Self, ZsysError> {
        let ptr = unsafe { ffi::zsys_router_new() };
        if ptr.is_null() {
            return Err(ZsysError::AllocationFailed);
        }
        Ok(Self { ptr })
    }

    /// Add or update a trigger → handler_id mapping.
    pub fn add(&mut self, trigger: &str, handler_id: i32) -> Result<(), ZsysError> {
        let c = CString::new(trigger)?;
        let rc = unsafe { ffi::zsys_router_add(self.ptr, c.as_ptr(), handler_id) };
        if rc != 0 { Err(ZsysError::OperationFailed("zsys_router_add")) } else { Ok(()) }
    }

    /// Remove a trigger. Returns `Ok(())` if found, `Err(NotFound)` otherwise.
    pub fn remove(&mut self, trigger: &str) -> Result<(), ZsysError> {
        let c = CString::new(trigger)?;
        let rc = unsafe { ffi::zsys_router_remove(self.ptr, c.as_ptr()) };
        if rc != 0 { Err(ZsysError::NotFound) } else { Ok(()) }
    }

    /// Look up handler_id for a trigger (case-insensitive).
    /// Returns `None` if not found.
    pub fn lookup(&mut self, trigger: &str) -> Result<Option<i32>, ZsysError> {
        let c = CString::new(trigger)?;
        let id = unsafe { ffi::zsys_router_lookup(self.ptr, c.as_ptr()) };
        Ok(if id == -1 { None } else { Some(id) })
    }

    /// Number of registered triggers.
    pub fn count(&self) -> usize {
        unsafe { ffi::zsys_router_count(self.ptr) }
    }

    /// Remove all entries.
    pub fn clear(&mut self) {
        unsafe { ffi::zsys_router_clear(self.ptr) }
    }
}

impl Drop for Router {
    fn drop(&mut self) {
        if !self.ptr.is_null() {
            unsafe { ffi::zsys_router_free(self.ptr) };
            self.ptr = std::ptr::null_mut();
        }
    }
}

impl Default for Router {
    fn default() -> Self { Self::new().expect("zsys_router_new") }
}

// ── Registry ──────────────────────────────────────────────────────────────

/// Dynamic array of name → handler_id entries with optional
/// description and category metadata.
pub struct Registry {
    ptr: *mut ffi::ZsysRegistry,
}

// SAFETY: same reasoning as Router.
unsafe impl Send for Registry {}

impl Registry {
    /// Create an empty registry.
    pub fn new() -> Result<Self, ZsysError> {
        let ptr = unsafe { ffi::zsys_registry_new() };
        if ptr.is_null() {
            return Err(ZsysError::AllocationFailed);
        }
        Ok(Self { ptr })
    }

    /// Register a handler. `description` and `category` are optional.
    pub fn register(
        &mut self,
        name: &str,
        handler_id: i32,
        description: Option<&str>,
        category: Option<&str>,
    ) -> Result<(), ZsysError> {
        let c_name = CString::new(name)?;
        let c_desc = description.map(CString::new).transpose()?;
        let c_cat  = category.map(CString::new).transpose()?;

        let desc_ptr = c_desc.as_ref().map_or(std::ptr::null(), |s| s.as_ptr());
        let cat_ptr  = c_cat.as_ref().map_or(std::ptr::null(), |s| s.as_ptr());

        let rc = unsafe {
            ffi::zsys_registry_register(self.ptr, c_name.as_ptr(), handler_id, desc_ptr, cat_ptr)
        };
        if rc != 0 { Err(ZsysError::OperationFailed("zsys_registry_register")) } else { Ok(()) }
    }

    /// Unregister by name. Returns `Err(NotFound)` if absent.
    pub fn unregister(&mut self, name: &str) -> Result<(), ZsysError> {
        let c = CString::new(name)?;
        let rc = unsafe { ffi::zsys_registry_unregister(self.ptr, c.as_ptr()) };
        if rc != 0 { Err(ZsysError::NotFound) } else { Ok(()) }
    }

    /// Return handler_id for name, or `None` if not found.
    pub fn get(&mut self, name: &str) -> Result<Option<i32>, ZsysError> {
        let c = CString::new(name)?;
        let id = unsafe { ffi::zsys_registry_get(self.ptr, c.as_ptr()) };
        Ok(if id == -1 { None } else { Some(id) })
    }

    /// Return (description, category) for name.
    pub fn info(&mut self, name: &str) -> Result<(String, String), ZsysError> {
        let c = CString::new(name)?;
        let mut desc_buf = vec![0u8; 256];
        let mut cat_buf  = vec![0u8; 128];
        let rc = unsafe {
            ffi::zsys_registry_info(
                self.ptr,
                c.as_ptr(),
                desc_buf.as_mut_ptr() as *mut i8,
                desc_buf.len(),
                cat_buf.as_mut_ptr() as *mut i8,
                cat_buf.len(),
            )
        };
        if rc != 0 {
            return Err(ZsysError::NotFound);
        }
        let desc = CStr::from_bytes_until_nul(&desc_buf)
            .map(|s| s.to_string_lossy().into_owned())
            .unwrap_or_default();
        let cat = CStr::from_bytes_until_nul(&cat_buf)
            .map(|s| s.to_string_lossy().into_owned())
            .unwrap_or_default();
        Ok((desc, cat))
    }

    /// Number of registered entries.
    pub fn count(&self) -> usize {
        unsafe { ffi::zsys_registry_count(self.ptr) }
    }

    /// Name at index, or `None` if out of bounds.
    pub fn name_at(&self, index: usize) -> Option<&str> {
        let ptr = unsafe { ffi::zsys_registry_name_at(self.ptr, index) };
        if ptr.is_null() {
            return None;
        }
        // SAFETY: pointer is valid for the lifetime of self (internal storage).
        unsafe { CStr::from_ptr(ptr) }.to_str().ok()
    }

    /// Collect all registered names.
    pub fn names(&self) -> Vec<&str> {
        (0..self.count()).filter_map(|i| self.name_at(i)).collect()
    }
}

impl Drop for Registry {
    fn drop(&mut self) {
        if !self.ptr.is_null() {
            unsafe { ffi::zsys_registry_free(self.ptr) };
            self.ptr = std::ptr::null_mut();
        }
    }
}

impl Default for Registry {
    fn default() -> Self { Self::new().expect("zsys_registry_new") }
}
