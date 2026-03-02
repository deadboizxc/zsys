// Rust binding for zsys_crypto — AES-256-CBC, RSA-OAEP, ECDH/AES-256-GCM.
//
// Build: cargo build  (build.rs links libzsys_crypto via bindgen)
//
// Usage:
//   let aes = Aes::new(b"my-32-byte-secret-key-padded!!!!");
//   let ct  = aes.encrypt(b"Hello, world!").unwrap();
//   let pt  = aes.decrypt(&ct).unwrap();
//
//   let (priv_pem, pub_pem) = Rsa::generate(2048).unwrap();
//   let ct = Rsa::encrypt(&pub_pem, b"secret").unwrap();
//
//   let (priv_pem, pub_pem) = Ecc::generate().unwrap();
//   let ct = Ecc::encrypt(&pub_pem, b"secret").unwrap();

use std::ffi::CString;
use std::os::raw::{c_char, c_int, c_void};
use std::slice;

// ── raw FFI declarations ──────────────────────────────────────────────── //

#[allow(non_upper_case_globals, non_camel_case_types, dead_code)]
mod ffi {
    use std::os::raw::{c_char, c_int, c_void};

    extern "C" {
        pub fn free(ptr: *mut c_void);

        pub fn zsys_aes_encrypt(
            key: *const u8, key_len: usize,
            plaintext: *const u8, pt_len: usize,
            out_len: *mut usize,
        ) -> *mut u8;

        pub fn zsys_aes_decrypt(
            key: *const u8, key_len: usize,
            ciphertext: *const u8, ct_len: usize,
            out_len: *mut usize,
        ) -> *mut u8;

        pub fn zsys_rsa_generate(key_bits: c_int, pub_pem: *mut *mut c_char) -> *mut c_char;
        pub fn zsys_rsa_encrypt(
            pub_pem: *const c_char,
            plaintext: *const u8, pt_len: usize,
            out_len: *mut usize,
        ) -> *mut u8;
        pub fn zsys_rsa_decrypt(
            priv_pem: *const c_char,
            ciphertext: *const u8, ct_len: usize,
            out_len: *mut usize,
        ) -> *mut u8;

        pub fn zsys_ecc_generate(pub_pem: *mut *mut c_char) -> *mut c_char;
        pub fn zsys_ecc_encrypt(
            pub_pem: *const c_char,
            plaintext: *const u8, pt_len: usize,
            out_len: *mut usize,
        ) -> *mut u8;
        pub fn zsys_ecc_decrypt(
            priv_pem: *const c_char,
            ciphertext: *const u8, ct_len: usize,
            out_len: *mut usize,
        ) -> *mut u8;
    }
}

// ── internal helpers ──────────────────────────────────────────────────── //

/// Copy a C-heap buffer into Vec<u8>, then free it.
unsafe fn c_buf_to_vec(ptr: *mut u8, len: usize) -> Vec<u8> {
    let v = slice::from_raw_parts(ptr, len).to_vec();
    ffi::free(ptr as *mut c_void);
    v
}

/// Copy a C-heap string into a Rust String, then free it.
unsafe fn c_str_to_owned(ptr: *mut c_char) -> String {
    let s = std::ffi::CStr::from_ptr(ptr)
        .to_string_lossy()
        .into_owned();
    ffi::free(ptr as *mut c_void);
    s
}

// ── AES-256-CBC ───────────────────────────────────────────────────────── //

/// AES-256-CBC symmetric encryption.
///
/// The key is used as-is (truncated or zero-padded to 32 bytes in C).
/// `encrypt` output: 16-byte IV + PKCS7-padded ciphertext.
pub struct Aes {
    key: Vec<u8>,
}

impl Aes {
    pub fn new(key: &[u8]) -> Self {
        Self { key: key.to_vec() }
    }

    /// Encrypt plaintext. Returns `IV (16 B) || ciphertext`.
    pub fn encrypt(&self, data: &[u8]) -> Result<Vec<u8>, String> {
        let mut out_len: usize = 0;
        let ptr = unsafe {
            ffi::zsys_aes_encrypt(
                self.key.as_ptr(), self.key.len(),
                data.as_ptr(), data.len(),
                &mut out_len,
            )
        };
        if ptr.is_null() {
            Err("zsys_aes_encrypt failed".into())
        } else {
            Ok(unsafe { c_buf_to_vec(ptr, out_len) })
        }
    }

    /// Decrypt ciphertext produced by [`Aes::encrypt`].
    pub fn decrypt(&self, data: &[u8]) -> Result<Vec<u8>, String> {
        let mut out_len: usize = 0;
        let ptr = unsafe {
            ffi::zsys_aes_decrypt(
                self.key.as_ptr(), self.key.len(),
                data.as_ptr(), data.len(),
                &mut out_len,
            )
        };
        if ptr.is_null() {
            Err("zsys_aes_decrypt failed".into())
        } else {
            Ok(unsafe { c_buf_to_vec(ptr, out_len) })
        }
    }
}

// ── RSA-OAEP ─────────────────────────────────────────────────────────── //

/// RSA-OAEP (SHA-256) asymmetric encryption — all methods are associated.
pub struct Rsa;

impl Rsa {
    /// Generate RSA key pair of `bits` size. Returns `(priv_pem, pub_pem)`.
    pub fn generate(bits: u32) -> Result<(String, String), String> {
        let mut pub_ptr: *mut c_char = std::ptr::null_mut();
        let priv_ptr = unsafe { ffi::zsys_rsa_generate(bits as c_int, &mut pub_ptr) };
        if priv_ptr.is_null() {
            return Err("zsys_rsa_generate failed".into());
        }
        let priv_pem = unsafe { c_str_to_owned(priv_ptr) };
        let pub_pem  = unsafe { c_str_to_owned(pub_ptr) };
        Ok((priv_pem, pub_pem))
    }

    /// Encrypt `data` with RSA-OAEP using PEM public key.
    pub fn encrypt(pub_pem: &str, data: &[u8]) -> Result<Vec<u8>, String> {
        let pem = CString::new(pub_pem).map_err(|e| e.to_string())?;
        let mut out_len: usize = 0;
        let ptr = unsafe {
            ffi::zsys_rsa_encrypt(pem.as_ptr(), data.as_ptr(), data.len(), &mut out_len)
        };
        if ptr.is_null() {
            Err("zsys_rsa_encrypt failed".into())
        } else {
            Ok(unsafe { c_buf_to_vec(ptr, out_len) })
        }
    }

    /// Decrypt RSA-OAEP ciphertext with PEM private key.
    pub fn decrypt(priv_pem: &str, data: &[u8]) -> Result<Vec<u8>, String> {
        let pem = CString::new(priv_pem).map_err(|e| e.to_string())?;
        let mut out_len: usize = 0;
        let ptr = unsafe {
            ffi::zsys_rsa_decrypt(pem.as_ptr(), data.as_ptr(), data.len(), &mut out_len)
        };
        if ptr.is_null() {
            Err("zsys_rsa_decrypt failed".into())
        } else {
            Ok(unsafe { c_buf_to_vec(ptr, out_len) })
        }
    }
}

// ── ECC (ECDH P-256 + AES-256-GCM) ──────────────────────────────────── //

/// ECDH P-256 + AES-256-GCM hybrid encryption — all methods are associated.
///
/// Ciphertext layout: `eph_pub (65 B) || nonce (12 B) || ciphertext || GCM tag (16 B)`.
pub struct Ecc;

impl Ecc {
    /// Generate EC P-256 key pair. Returns `(priv_pem, pub_pem)`.
    pub fn generate() -> Result<(String, String), String> {
        let mut pub_ptr: *mut c_char = std::ptr::null_mut();
        let priv_ptr = unsafe { ffi::zsys_ecc_generate(&mut pub_ptr) };
        if priv_ptr.is_null() {
            return Err("zsys_ecc_generate failed".into());
        }
        let priv_pem = unsafe { c_str_to_owned(priv_ptr) };
        let pub_pem  = unsafe { c_str_to_owned(pub_ptr) };
        Ok((priv_pem, pub_pem))
    }

    /// Encrypt `data` with ECDH + AES-256-GCM using PEM public key.
    pub fn encrypt(pub_pem: &str, data: &[u8]) -> Result<Vec<u8>, String> {
        let pem = CString::new(pub_pem).map_err(|e| e.to_string())?;
        let mut out_len: usize = 0;
        let ptr = unsafe {
            ffi::zsys_ecc_encrypt(pem.as_ptr(), data.as_ptr(), data.len(), &mut out_len)
        };
        if ptr.is_null() {
            Err("zsys_ecc_encrypt failed".into())
        } else {
            Ok(unsafe { c_buf_to_vec(ptr, out_len) })
        }
    }

    /// Decrypt ECDH + AES-256-GCM ciphertext with PEM private key.
    pub fn decrypt(priv_pem: &str, data: &[u8]) -> Result<Vec<u8>, String> {
        let pem = CString::new(priv_pem).map_err(|e| e.to_string())?;
        let mut out_len: usize = 0;
        let ptr = unsafe {
            ffi::zsys_ecc_decrypt(pem.as_ptr(), data.as_ptr(), data.len(), &mut out_len)
        };
        if ptr.is_null() {
            Err("zsys_ecc_decrypt failed".into())
        } else {
            Ok(unsafe { c_buf_to_vec(ptr, out_len) })
        }
    }
}
