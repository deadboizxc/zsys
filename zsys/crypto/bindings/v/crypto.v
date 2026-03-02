// V (Vlang) binding for zsys/crypto.
//
// Build: v -cflags '-lzsys_crypto -lssl -lcrypto' main.v
//
// Usage:
//   key := 'my-32-byte-secret-key-padded!!!!'.bytes()
//   aes := crypto.new_aes(key)
//   ct  := aes.encrypt('Hello'.bytes()) or { panic(err) }
//   pt  := aes.decrypt(ct) or { panic(err) }
//
//   priv, pub := crypto.rsa_generate(2048) or { panic(err) }
//   ct := crypto.rsa_encrypt(pub, 'secret'.bytes()) or { panic(err) }
//
//   priv, pub := crypto.ecc_generate() or { panic(err) }
//   ct := crypto.ecc_encrypt(pub, 'secret'.bytes()) or { panic(err) }

module crypto

#flag -lzsys_crypto -lssl -lcrypto
#include "../../c/include/zsys_crypto.h"

fn C.zsys_aes_encrypt(key &u8, key_len usize, plaintext &u8, pt_len usize, out_len &usize) &u8
fn C.zsys_aes_decrypt(key &u8, key_len usize, ciphertext &u8, ct_len usize, out_len &usize) &u8

fn C.zsys_rsa_generate(key_bits int, pub_pem &&char) &char
fn C.zsys_rsa_encrypt(pub_pem &char, plaintext &u8, pt_len usize, out_len &usize) &u8
fn C.zsys_rsa_decrypt(priv_pem &char, ciphertext &u8, ct_len usize, out_len &usize) &u8

fn C.zsys_ecc_generate(pub_pem &&char) &char
fn C.zsys_ecc_encrypt(pub_pem &char, plaintext &u8, pt_len usize, out_len &usize) &u8
fn C.zsys_ecc_decrypt(priv_pem &char, ciphertext &u8, ct_len usize, out_len &usize) &u8

fn C.free(ptr voidptr)

// ── internal helpers ─────────────────────────────────────────────────── //

// Copy a C-heap buffer into a V []u8 and free it.
fn c_buf_to_vbytes(ptr &u8, n usize) []u8 {
	if ptr == unsafe { nil } { return [] }
	result := unsafe { ptr.vbytes(int(n)).clone() }
	C.free(ptr)
	return result
}

// ── AES-256-CBC ──────────────────────────────────────────────────────── //

// AES provides AES-256-CBC symmetric encryption.
pub struct AES {
mut:
	key []u8
}

// new_aes creates an AES context bound to the given key.
pub fn new_aes(key []u8) &AES {
	return &AES{ key: key.clone() }
}

// encrypt encrypts data with AES-256-CBC. Returns IV (16 B) + ciphertext.
pub fn (a &AES) encrypt(data []u8) ![]u8 {
	mut out_len := usize(0)
	ptr := C.zsys_aes_encrypt(a.key.data, usize(a.key.len),
		data.data, usize(data.len), &out_len)
	if ptr == unsafe { nil } {
		return error('zsys_aes_encrypt failed')
	}
	return c_buf_to_vbytes(ptr, out_len)
}

// decrypt decrypts AES-256-CBC ciphertext produced by encrypt().
pub fn (a &AES) decrypt(data []u8) ![]u8 {
	mut out_len := usize(0)
	ptr := C.zsys_aes_decrypt(a.key.data, usize(a.key.len),
		data.data, usize(data.len), &out_len)
	if ptr == unsafe { nil } {
		return error('zsys_aes_decrypt failed')
	}
	return c_buf_to_vbytes(ptr, out_len)
}

// ── RSA-OAEP ─────────────────────────────────────────────────────────── //

// rsa_generate generates an RSA key pair. Returns (priv_pem, pub_pem).
pub fn rsa_generate(bits int) !(string, string) {
	mut pub_ptr := &char(0)
	priv_ptr := C.zsys_rsa_generate(bits, &&pub_ptr)
	if priv_ptr == unsafe { nil } {
		return error('zsys_rsa_generate failed')
	}
	priv_pem := unsafe { cstring_to_vstring(priv_ptr) }
	pub_pem  := unsafe { cstring_to_vstring(pub_ptr) }
	C.free(priv_ptr)
	C.free(pub_ptr)
	return priv_pem, pub_pem
}

// rsa_encrypt encrypts data with RSA-OAEP using a PEM public key.
pub fn rsa_encrypt(pub_pem string, data []u8) ![]u8 {
	mut out_len := usize(0)
	ptr := C.zsys_rsa_encrypt(pub_pem.str, data.data, usize(data.len), &out_len)
	if ptr == unsafe { nil } {
		return error('zsys_rsa_encrypt failed')
	}
	return c_buf_to_vbytes(ptr, out_len)
}

// rsa_decrypt decrypts RSA-OAEP ciphertext using a PEM private key.
pub fn rsa_decrypt(priv_pem string, data []u8) ![]u8 {
	mut out_len := usize(0)
	ptr := C.zsys_rsa_decrypt(priv_pem.str, data.data, usize(data.len), &out_len)
	if ptr == unsafe { nil } {
		return error('zsys_rsa_decrypt failed')
	}
	return c_buf_to_vbytes(ptr, out_len)
}

// ── ECC (ECDH P-256 + AES-256-GCM) ──────────────────────────────────── //

// ecc_generate generates an EC P-256 key pair. Returns (priv_pem, pub_pem).
pub fn ecc_generate() !(string, string) {
	mut pub_ptr := &char(0)
	priv_ptr := C.zsys_ecc_generate(&&pub_ptr)
	if priv_ptr == unsafe { nil } {
		return error('zsys_ecc_generate failed')
	}
	priv_pem := unsafe { cstring_to_vstring(priv_ptr) }
	pub_pem  := unsafe { cstring_to_vstring(pub_ptr) }
	C.free(priv_ptr)
	C.free(pub_ptr)
	return priv_pem, pub_pem
}

// ecc_encrypt encrypts data with ECDH + AES-256-GCM using a PEM public key.
// Output: eph_pub (65 B) + nonce (12 B) + ciphertext + GCM tag (16 B).
pub fn ecc_encrypt(pub_pem string, data []u8) ![]u8 {
	mut out_len := usize(0)
	ptr := C.zsys_ecc_encrypt(pub_pem.str, data.data, usize(data.len), &out_len)
	if ptr == unsafe { nil } {
		return error('zsys_ecc_encrypt failed')
	}
	return c_buf_to_vbytes(ptr, out_len)
}

// ecc_decrypt decrypts ECDH + AES-256-GCM ciphertext using a PEM private key.
pub fn ecc_decrypt(priv_pem string, data []u8) ![]u8 {
	mut out_len := usize(0)
	ptr := C.zsys_ecc_decrypt(priv_pem.str, data.data, usize(data.len), &out_len)
	if ptr == unsafe { nil } {
		return error('zsys_ecc_decrypt failed')
	}
	return c_buf_to_vbytes(ptr, out_len)
}
