// Package log provides logging utilities via zsys C core.
// Go equivalent of zsys.log (Python).
package log

/*
#cgo CFLAGS: -I../../include
#include "zsys_core.h"
#include <stdlib.h>
*/
import "C"
import (
    "fmt"
    "time"
    "unsafe"
)

// Level constants.
const (
    DEBUG = "DEBUG"
    INFO  = "INFO"
    WARN  = "WARN"
    ERROR = "ERROR"
)

// FormatJSON returns a JSON log line.
func FormatJSON(level, message string) string {
    ts := time.Now().UTC().Format(time.RFC3339)
    cl := C.CString(level)
    cm := C.CString(message)
    ct := C.CString(ts)
    defer C.free(unsafe.Pointer(cl))
    defer C.free(unsafe.Pointer(cm))
    defer C.free(unsafe.Pointer(ct))
    r := C.zsys_format_json_log(cl, cm, ct)
    if r == nil {
        return fmt.Sprintf(`{"level":%q,"message":%q,"ts":%q}`, level, message, ts)
    }
    defer C.zsys_free(r)
    return C.GoString(r)
}

// Box prints text in a box.
func Box(text string, padding int) string {
    cs := C.CString(text)
    defer C.free(unsafe.Pointer(cs))
    r := C.zsys_print_box_str(cs, C.int(padding))
    if r == nil {
        return text
    }
    defer C.zsys_free(r)
    return C.GoString(r)
}

// Separator returns a separator string.
func Separator(ch string, length int) string {
    cs := C.CString(ch)
    defer C.free(unsafe.Pointer(cs))
    r := C.zsys_print_separator_str(cs, C.int(length))
    if r == nil {
        return ""
    }
    defer C.zsys_free(r)
    return C.GoString(r)
}
