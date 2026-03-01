// Package modules provides module loading and routing for zsys.
// Go equivalent of zsys.modules (Python).
package modules

/*
#cgo CFLAGS: -I../../include
#include "zsys_core.h"
#include <stdlib.h>
*/
import "C"
import "unsafe"

// ParseMeta parses module meta comments from Go source or Python source.
// Returns a map of key → value pairs.
func ParseMeta(source string) map[string]string {
    cs := C.CString(source)
    defer C.free(unsafe.Pointer(cs))
    pairs := C.zsys_parse_meta_comments(cs, C.size_t(len(source)))
    if pairs == nil {
        return nil
    }
    result := make(map[string]string)
    for i := 0; ; i += 2 {
        k := *(**C.char)(unsafe.Pointer(uintptr(unsafe.Pointer(pairs)) + uintptr(i)*8))
        if k == nil {
            break
        }
        v := *(**C.char)(unsafe.Pointer(uintptr(unsafe.Pointer(pairs)) + uintptr(i+1)*8))
        result[C.GoString(k)] = C.GoString(v)
    }
    C.zsys_meta_free(pairs)
    return result
}

// MatchPrefix returns true if text starts with a prefix + trigger combo.
func MatchPrefix(text string, prefixes, triggers []string) bool {
    ct := C.CString(text)
    defer C.free(unsafe.Pointer(ct))
    cpfx := make([]*C.char, len(prefixes))
    ctrg := make([]*C.char, len(triggers))
    for i, p := range prefixes {
        cpfx[i] = C.CString(p)
        defer C.free(unsafe.Pointer(cpfx[i]))
    }
    for i, t := range triggers {
        ctrg[i] = C.CString(t)
        defer C.free(unsafe.Pointer(ctrg[i]))
    }
    var pfxPtr **C.char
    var trgPtr **C.char
    if len(cpfx) > 0 { pfxPtr = &cpfx[0] }
    if len(ctrg) > 0 { trgPtr = &ctrg[0] }
    r := C.zsys_match_prefix(ct,
        pfxPtr, C.int(len(prefixes)),
        trgPtr, C.int(len(triggers)))
    return r != 0
}
