// Go binding for zsys_log via cgo.
//
// Usage:
//   colored := zsyslog.AnsiColor("hello", "31")
//   json    := zsyslog.FormatJsonLog("INFO", "started", "2024-01-01T00:00:00Z")
//   boxx    := zsyslog.PrintBox("title", 2)
//   sep     := zsyslog.PrintSeparator("─", 40)
//   prog    := zsyslog.PrintProgress(7, 10, "Loading", 20)

package zsyslog

/*
#cgo LDFLAGS: -lzsys_log
#include "../../c/include/zsys_log.h"
#include <stdlib.h>
*/
import "C"
import "unsafe"

// AnsiColor wraps text with an ANSI escape sequence (e.g. code="31" for red).
func AnsiColor(text, code string) string {
	t := C.CString(text)
	c := C.CString(code)
	defer C.free(unsafe.Pointer(t))
	defer C.free(unsafe.Pointer(c))
	r := C.zsys_ansi_color(t, c)
	defer C.free(unsafe.Pointer(r))
	return C.GoString(r)
}

// FormatJsonLog formats a JSON log line: {"level":"…","message":"…","ts":"…"}.
func FormatJsonLog(level, message, ts string) string {
	l := C.CString(level)
	m := C.CString(message)
	t := C.CString(ts)
	defer C.free(unsafe.Pointer(l))
	defer C.free(unsafe.Pointer(m))
	defer C.free(unsafe.Pointer(t))
	r := C.zsys_format_json_log(l, m, t)
	defer C.free(unsafe.Pointer(r))
	return C.GoString(r)
}

// PrintBox renders a Unicode box (╔══╗ style) around text.
func PrintBox(text string, padding int) string {
	t := C.CString(text)
	defer C.free(unsafe.Pointer(t))
	r := C.zsys_print_box_str(t, C.int(padding))
	defer C.free(unsafe.Pointer(r))
	return C.GoString(r)
}

// PrintSeparator repeats ch length times to build a separator line.
func PrintSeparator(ch string, length int) string {
	c := C.CString(ch)
	defer C.free(unsafe.Pointer(c))
	r := C.zsys_print_separator_str(c, C.int(length))
	defer C.free(unsafe.Pointer(r))
	return C.GoString(r)
}

// PrintProgress renders a text progress bar: [###---] current/total (N%).
func PrintProgress(current, total int, prefix string, barLength int) string {
	p := C.CString(prefix)
	defer C.free(unsafe.Pointer(p))
	r := C.zsys_print_progress_str(C.int(current), C.int(total), p, C.int(barLength))
	defer C.free(unsafe.Pointer(r))
	return C.GoString(r)
}
