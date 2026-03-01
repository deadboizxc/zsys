// Package utils provides utility functions via zsys C core.
// Go equivalent of zsys.utils (Python).
package utils

/*
#cgo CFLAGS: -I../../include
#include "zsys_core.h"
#include <stdlib.h>
*/
import "C"
import "unsafe"

// EscapeHTML escapes HTML special characters.
func EscapeHTML(text string) string {
    cs := C.CString(text)
    defer C.free(unsafe.Pointer(cs))
    r := C.zsys_escape_html(cs, C.size_t(len(text)))
    if r == nil { return text }
    defer C.zsys_free(r)
    return C.GoString(r)
}

// FormatBytes formats bytes as human-readable string.
func FormatBytes(size int64) string {
    r := C.zsys_format_bytes(C.int64_t(size))
    if r == nil { return "" }
    defer C.zsys_free(r)
    return C.GoString(r)
}

// FormatDuration formats seconds as "1h 2m 3s".
func FormatDuration(seconds float64) string {
    r := C.zsys_format_duration(C.double(seconds))
    if r == nil { return "" }
    defer C.zsys_free(r)
    return C.GoString(r)
}

// FormatBold wraps text in <b> tags.
func FormatBold(text string, escape bool) string {
    cs := C.CString(text)
    defer C.free(unsafe.Pointer(cs))
    esc := 0
    if escape { esc = 1 }
    r := C.zsys_format_bold(cs, C.size_t(len(text)), C.int(esc))
    if r == nil { return text }
    defer C.zsys_free(r)
    return C.GoString(r)
}

// TruncateText truncates text to maxChars codepoints, appending suffix.
func TruncateText(text string, maxChars int, suffix string) string {
    ct := C.CString(text)
    cs := C.CString(suffix)
    defer C.free(unsafe.Pointer(ct))
    defer C.free(unsafe.Pointer(cs))
    r := C.zsys_truncate_text(ct, C.size_t(len(text)), C.size_t(maxChars), cs)
    if r == nil { return text }
    defer C.zsys_free(r)
    return C.GoString(r)
}

// SplitText splits text into chunks of maxChars codepoints.
func SplitText(text string, maxChars int) []string {
    cs := C.CString(text)
    defer C.free(unsafe.Pointer(cs))
    chunks := C.zsys_split_text(cs, C.size_t(len(text)), C.size_t(maxChars))
    if chunks == nil { return []string{text} }
    defer C.zsys_split_free(chunks)
    var result []string
    for i := 0; ; i++ {
        p := *(**C.char)(unsafe.Pointer(uintptr(unsafe.Pointer(chunks)) + uintptr(i)*8))
        if p == nil { break }
        result = append(result, C.GoString(p))
    }
    return result
}
