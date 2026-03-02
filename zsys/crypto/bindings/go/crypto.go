// Go binding for zsys/crypto via cgo.
// Package zsyscrypto wraps AES-256-CBC, RSA-OAEP, and ECDH/AES-256-GCM.
//
// Usage:
//   aes := zsyscrypto.NewAES(key)
//   ct, err := aes.Encrypt(plaintext)
//   pt, err := aes.Decrypt(ct)
//
//   priv, pub, err := zsyscrypto.RSAGenerate(2048)
//   ct, err := zsyscrypto.RSAEncrypt(pub, plaintext)
//
//   priv, pub, err := zsyscrypto.ECCGenerate()
//   ct, err := zsyscrypto.ECCEncrypt(pub, plaintext)

package zsyscrypto

/*
#cgo LDFLAGS: -lzsys_crypto
#include "../../c/include/zsys_crypto.h"
#include <stdlib.h>
*/
import "C"
import (
	"fmt"
	"unsafe"
)

// ── AES-256-CBC ───────────────────────────────────────────────────────── //

// AES wraps zsys AES-256-CBC operations.
type AES struct {
	key []byte
}

// NewAES creates an AES context bound to the given key.
func NewAES(key []byte) *AES {
	k := make([]byte, len(key))
	copy(k, key)
	return &AES{key: k}
}

// Encrypt encrypts data with AES-256-CBC. Returns IV (16 B) + ciphertext.
func (a *AES) Encrypt(data []byte) ([]byte, error) {
	var outLen C.size_t
	ptr := C.zsys_aes_encrypt(
		(*C.uint8_t)(unsafe.Pointer(&a.key[0])), C.size_t(len(a.key)),
		(*C.uint8_t)(unsafe.Pointer(&data[0])), C.size_t(len(data)),
		&outLen,
	)
	if ptr == nil {
		return nil, fmt.Errorf("zsys_aes_encrypt failed")
	}
	defer C.free(unsafe.Pointer(ptr))
	return C.GoBytes(unsafe.Pointer(ptr), C.int(outLen)), nil
}

// Decrypt decrypts AES-256-CBC ciphertext (IV prepended) produced by Encrypt.
func (a *AES) Decrypt(data []byte) ([]byte, error) {
	var outLen C.size_t
	ptr := C.zsys_aes_decrypt(
		(*C.uint8_t)(unsafe.Pointer(&a.key[0])), C.size_t(len(a.key)),
		(*C.uint8_t)(unsafe.Pointer(&data[0])), C.size_t(len(data)),
		&outLen,
	)
	if ptr == nil {
		return nil, fmt.Errorf("zsys_aes_decrypt failed")
	}
	defer C.free(unsafe.Pointer(ptr))
	return C.GoBytes(unsafe.Pointer(ptr), C.int(outLen)), nil
}

// ── RSA-OAEP ─────────────────────────────────────────────────────────── //

// RSAGenerate generates an RSA key pair of the given bit size.
// Returns (privPEM, pubPEM, error).
func RSAGenerate(bits int) (priv, pub string, err error) {
	var pubPtr *C.char
	privPtr := C.zsys_rsa_generate(C.int(bits), &pubPtr)
	if privPtr == nil {
		return "", "", fmt.Errorf("zsys_rsa_generate failed")
	}
	defer C.free(unsafe.Pointer(privPtr))
	defer C.free(unsafe.Pointer(pubPtr))
	return C.GoString(privPtr), C.GoString(pubPtr), nil
}

// RSAEncrypt encrypts data with RSA-OAEP using a PEM public key.
func RSAEncrypt(pubPEM string, data []byte) ([]byte, error) {
	pem := C.CString(pubPEM)
	defer C.free(unsafe.Pointer(pem))
	var outLen C.size_t
	ptr := C.zsys_rsa_encrypt(
		pem,
		(*C.uint8_t)(unsafe.Pointer(&data[0])), C.size_t(len(data)),
		&outLen,
	)
	if ptr == nil {
		return nil, fmt.Errorf("zsys_rsa_encrypt failed")
	}
	defer C.free(unsafe.Pointer(ptr))
	return C.GoBytes(unsafe.Pointer(ptr), C.int(outLen)), nil
}

// RSADecrypt decrypts RSA-OAEP ciphertext using a PEM private key.
func RSADecrypt(privPEM string, data []byte) ([]byte, error) {
	pem := C.CString(privPEM)
	defer C.free(unsafe.Pointer(pem))
	var outLen C.size_t
	ptr := C.zsys_rsa_decrypt(
		pem,
		(*C.uint8_t)(unsafe.Pointer(&data[0])), C.size_t(len(data)),
		&outLen,
	)
	if ptr == nil {
		return nil, fmt.Errorf("zsys_rsa_decrypt failed")
	}
	defer C.free(unsafe.Pointer(ptr))
	return C.GoBytes(unsafe.Pointer(ptr), C.int(outLen)), nil
}

// ── ECC (ECDH P-256 + AES-256-GCM) ──────────────────────────────────── //

// ECCGenerate generates an EC P-256 key pair.
// Returns (privPEM, pubPEM, error).
func ECCGenerate() (priv, pub string, err error) {
	var pubPtr *C.char
	privPtr := C.zsys_ecc_generate(&pubPtr)
	if privPtr == nil {
		return "", "", fmt.Errorf("zsys_ecc_generate failed")
	}
	defer C.free(unsafe.Pointer(privPtr))
	defer C.free(unsafe.Pointer(pubPtr))
	return C.GoString(privPtr), C.GoString(pubPtr), nil
}

// ECCEncrypt encrypts data with ECDH + AES-256-GCM using a PEM public key.
// Output: eph_pub (65 B) + nonce (12 B) + ciphertext + GCM tag (16 B).
func ECCEncrypt(pubPEM string, data []byte) ([]byte, error) {
	pem := C.CString(pubPEM)
	defer C.free(unsafe.Pointer(pem))
	var outLen C.size_t
	ptr := C.zsys_ecc_encrypt(
		pem,
		(*C.uint8_t)(unsafe.Pointer(&data[0])), C.size_t(len(data)),
		&outLen,
	)
	if ptr == nil {
		return nil, fmt.Errorf("zsys_ecc_encrypt failed")
	}
	defer C.free(unsafe.Pointer(ptr))
	return C.GoBytes(unsafe.Pointer(ptr), C.int(outLen)), nil
}

// ECCDecrypt decrypts ECDH + AES-256-GCM ciphertext using a PEM private key.
func ECCDecrypt(privPEM string, data []byte) ([]byte, error) {
	pem := C.CString(privPEM)
	defer C.free(unsafe.Pointer(pem))
	var outLen C.size_t
	ptr := C.zsys_ecc_decrypt(
		pem,
		(*C.uint8_t)(unsafe.Pointer(&data[0])), C.size_t(len(data)),
		&outLen,
	)
	if ptr == nil {
		return nil, fmt.Errorf("zsys_ecc_decrypt failed")
	}
	defer C.free(unsafe.Pointer(ptr))
	return C.GoBytes(unsafe.Pointer(ptr), C.int(outLen)), nil
}
