// Go binding for ZsysUtils via cgo.
//
// Usage:
//   u := utils.New()
//   defer u.Free()
//   fmt.Println(u.EscapeHTML("<b>hi</b>"))
//   fmt.Println(u.FormatBytes(1536))
//   chunks := u.SplitText("hello world", 4)

package zsysutils

/*
#cgo LDFLAGS: -lzsys_utils
#include "../../c/include/zsys_utils.h"
#include <stdlib.h>
*/
import "C"
import "unsafe"

// Utils is a stateless Go wrapper around libzsys_utils.
type Utils struct{}

// New returns a new Utils handle.
func New() *Utils { return &Utils{} }

// Free is a no-op (Utils holds no C state), provided for API consistency.
func (u *Utils) Free() {}

// ── helpers ──────────────────────────────────────────────────────────────── //

func goStr(p *C.char) string {
	if p == nil {
		return ""
	}
	s := C.GoString(p)
	C.zsys_free(p)
	return s
}

func goArr(pp **C.char) []string {
	if pp == nil {
		return nil
	}
	var result []string
	for i := 0; ; i++ {
		p := *(**C.char)(unsafe.Pointer(uintptr(unsafe.Pointer(pp)) +
			uintptr(i)*unsafe.Sizeof(pp)))
		if p == nil {
			break
		}
		result = append(result, C.GoString(p))
	}
	C.zsys_split_free(pp)
	return result
}

// ── text / HTML ───────────────────────────────────────────────────────────── //

// EscapeHTML escapes & < > " in text.
func (u *Utils) EscapeHTML(text string) string {
	cs := C.CString(text)
	defer C.free(unsafe.Pointer(cs))
	return goStr(C.zsys_escape_html(cs, C.size_t(len(text))))
}

// StripHTML strips HTML tags and unescapes basic entities.
func (u *Utils) StripHTML(text string) string {
	cs := C.CString(text)
	defer C.free(unsafe.Pointer(cs))
	return goStr(C.zsys_strip_html(cs, C.size_t(len(text))))
}

// Truncate truncates UTF-8 text to maxChars codepoints.
func (u *Utils) Truncate(text string, maxChars int, suffix string) string {
	cs := C.CString(text)
	sf := C.CString(suffix)
	defer C.free(unsafe.Pointer(cs))
	defer C.free(unsafe.Pointer(sf))
	return goStr(C.zsys_truncate_text(cs, C.size_t(len(text)),
		C.size_t(maxChars), sf))
}

// SplitText splits text into chunks of at most maxChars codepoints each.
func (u *Utils) SplitText(text string, maxChars int) []string {
	cs := C.CString(text)
	defer C.free(unsafe.Pointer(cs))
	pp := C.zsys_split_text(cs, C.size_t(len(text)), C.size_t(maxChars))
	return goArr(pp)
}

// GetArgs extracts whitespace-split args after the first word.
func (u *Utils) GetArgs(text string, maxSplit int) []string {
	cs := C.CString(text)
	defer C.free(unsafe.Pointer(cs))
	pp := C.zsys_get_args(cs, C.size_t(len(text)), C.int(maxSplit))
	return goArr(pp)
}

// ── numeric formatters ────────────────────────────────────────────────────── //

// FormatBytes formats a byte count as "1.5 KB", "3.2 MB" etc.
func (u *Utils) FormatBytes(size int64) string {
	return goStr(C.zsys_format_bytes(C.int64_t(size)))
}

// FormatDuration formats seconds as "1h 2m 3s".
func (u *Utils) FormatDuration(seconds float64) string {
	return goStr(C.zsys_format_duration(C.double(seconds)))
}

// HumanTime formats seconds as Russian human time.
func (u *Utils) HumanTime(seconds int64, shortFmt bool) string {
	sf := C.int(0)
	if shortFmt {
		sf = 1
	}
	return goStr(C.zsys_human_time(C.long(seconds), sf))
}

// ParseDuration parses "30m", "1h30m" → seconds. Returns -1 on error.
func (u *Utils) ParseDuration(text string) int64 {
	cs := C.CString(text)
	defer C.free(unsafe.Pointer(cs))
	return int64(C.zsys_parse_duration(cs))
}

// ── HTML formatters ───────────────────────────────────────────────────────── //

// Bold wraps text in <b>…</b>.
func (u *Utils) Bold(text string, escape bool) string {
	cs := C.CString(text)
	defer C.free(unsafe.Pointer(cs))
	e := C.int(0)
	if escape { e = 1 }
	return goStr(C.zsys_format_bold(cs, C.size_t(len(text)), e))
}

// Italic wraps text in <i>…</i>.
func (u *Utils) Italic(text string, escape bool) string {
	cs := C.CString(text)
	defer C.free(unsafe.Pointer(cs))
	e := C.int(0)
	if escape { e = 1 }
	return goStr(C.zsys_format_italic(cs, C.size_t(len(text)), e))
}

// Code wraps text in <code>…</code>.
func (u *Utils) Code(text string, escape bool) string {
	cs := C.CString(text)
	defer C.free(unsafe.Pointer(cs))
	e := C.int(0)
	if escape { e = 1 }
	return goStr(C.zsys_format_code(cs, C.size_t(len(text)), e))
}

// Pre wraps text in <pre>…</pre> (optionally with a language class).
func (u *Utils) Pre(text, lang string, escape bool) string {
	cs := C.CString(text)
	cl := C.CString(lang)
	defer C.free(unsafe.Pointer(cs))
	defer C.free(unsafe.Pointer(cl))
	e := C.int(0)
	if escape { e = 1 }
	return goStr(C.zsys_format_pre(cs, C.size_t(len(text)), cl, e))
}

// Link builds <a href="url">text</a>.
func (u *Utils) Link(text, url string, escape bool) string {
	ct := C.CString(text)
	cu := C.CString(url)
	defer C.free(unsafe.Pointer(ct))
	defer C.free(unsafe.Pointer(cu))
	e := C.int(0)
	if escape { e = 1 }
	return goStr(C.zsys_format_link(ct, C.size_t(len(text)),
		cu, C.size_t(len(url)), e))
}

// Mention builds an inline Telegram mention link.
func (u *Utils) Mention(text string, userID int64, escape bool) string {
	cs := C.CString(text)
	defer C.free(unsafe.Pointer(cs))
	e := C.int(0)
	if escape { e = 1 }
	return goStr(C.zsys_format_mention(cs, C.size_t(len(text)),
		C.int64_t(userID), e))
}

// Underline wraps text in <u>…</u>.
func (u *Utils) Underline(text string) string {
	cs := C.CString(text)
	defer C.free(unsafe.Pointer(cs))
	return goStr(C.zsys_format_underline(cs, C.size_t(len(text))))
}

// Strikethrough wraps text in <s>…</s>.
func (u *Utils) Strikethrough(text string) string {
	cs := C.CString(text)
	defer C.free(unsafe.Pointer(cs))
	return goStr(C.zsys_format_strikethrough(cs, C.size_t(len(text))))
}

// Spoiler wraps text in <spoiler>…</spoiler>.
func (u *Utils) Spoiler(text string) string {
	cs := C.CString(text)
	defer C.free(unsafe.Pointer(cs))
	return goStr(C.zsys_format_spoiler(cs, C.size_t(len(text))))
}

// Quote wraps text in <blockquote>…</blockquote>.
func (u *Utils) Quote(text string) string {
	cs := C.CString(text)
	defer C.free(unsafe.Pointer(cs))
	return goStr(C.zsys_format_quote(cs, C.size_t(len(text))))
}
