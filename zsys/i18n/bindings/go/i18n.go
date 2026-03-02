// Go binding for ZsysI18n via cgo.
//
// Usage:
//   t := i18n.New()
//   defer t.Free()
//   t.Load("en", "/path/to/en.json")
//   t.SetLang("en")
//   fmt.Println(t.Get("hello"))

package i18n

/*
#cgo LDFLAGS: -lzsys_core
#include "../../c/include/zsys_core.h"
#include <stdlib.h>
*/
import "C"
import (
	"fmt"
	"unsafe"
)

// I18n is a safe Go wrapper around ZsysI18n.
type I18n struct {
	ptr *C.ZsysI18n
}

// New creates a new I18n context.
func New() *I18n {
	ptr := C.zsys_i18n_new()
	if ptr == nil {
		panic("zsys_i18n_new returned NULL")
	}
	return &I18n{ptr: ptr}
}

// Free releases the underlying C resources.
func (t *I18n) Free() {
	if t.ptr != nil {
		C.zsys_i18n_free(t.ptr)
		t.ptr = nil
	}
}

// Load loads a JSON locale file for langCode.
func (t *I18n) Load(langCode, jsonPath string) error {
	lc := C.CString(langCode)
	jp := C.CString(jsonPath)
	defer C.free(unsafe.Pointer(lc))
	defer C.free(unsafe.Pointer(jp))
	if rc := C.zsys_i18n_load_json(t.ptr, lc, jp); rc != 0 {
		return fmt.Errorf("failed to load locale: %s", jsonPath)
	}
	return nil
}

// SetLang sets the active language.
func (t *I18n) SetLang(langCode string) {
	lc := C.CString(langCode)
	defer C.free(unsafe.Pointer(lc))
	C.zsys_i18n_set_lang(t.ptr, lc)
}

// Get translates key using the active language.
func (t *I18n) Get(key string) string {
	k := C.CString(key)
	defer C.free(unsafe.Pointer(k))
	r := C.zsys_i18n_get(t.ptr, k)
	if r == nil {
		return key
	}
	return C.GoString(r)
}

// GetLang translates key in a specific language.
func (t *I18n) GetLang(langCode, key string) string {
	lc := C.CString(langCode)
	k  := C.CString(key)
	defer C.free(unsafe.Pointer(lc))
	defer C.free(unsafe.Pointer(k))
	r := C.zsys_i18n_get_lang(t.ptr, lc, k)
	if r == nil {
		return key
	}
	return C.GoString(r)
}
