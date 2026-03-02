// V (Vlang) binding for ZsysUtils.
//
// Build: v -cflags '-lzsys_utils' main.v
// Usage:
//   mut u := zsysutils.new_utils()
//   println(u.escape_html('<b>hi</b>'))
//   println(u.format_bytes(1536))
//   chunks := u.split_text('hello world', 4) or { panic(err) }

module zsysutils

#flag -lzsys_utils
#include "../../c/include/zsys_utils.h"

fn C.zsys_free(ptr &char)
fn C.zsys_split_free(chunks &&char)

fn C.zsys_escape_html(text &char, len usize) &char
fn C.zsys_strip_html(text &char, len usize) &char
fn C.zsys_truncate_text(text &char, len usize, max_chars usize, suffix &char) &char
fn C.zsys_split_text(text &char, len usize, max_chars usize) &&char
fn C.zsys_get_args(text &char, len usize, max_split int) &&char

fn C.zsys_format_bytes(size i64) &char
fn C.zsys_format_duration(seconds f64) &char
fn C.zsys_human_time(seconds i64, short_fmt int) &char
fn C.zsys_parse_duration(text &char) i64

fn C.zsys_format_bold(text &char, len usize, escape int) &char
fn C.zsys_format_italic(text &char, len usize, escape int) &char
fn C.zsys_format_code(text &char, len usize, escape int) &char
fn C.zsys_format_pre(text &char, len usize, lang &char, escape int) &char
fn C.zsys_format_link(text &char, tlen usize, url &char, ulen usize, escape int) &char
fn C.zsys_format_mention(text &char, len usize, user_id i64, escape int) &char
fn C.zsys_format_underline(text &char, len usize) &char
fn C.zsys_format_strikethrough(text &char, len usize) &char
fn C.zsys_format_spoiler(text &char, len usize) &char
fn C.zsys_format_quote(text &char, len usize) &char

// Utils is a stateless wrapper around libzsys_utils.
pub struct Utils {}

// new_utils returns a new Utils handle.
pub fn new_utils() &Utils {
	return &Utils{}
}

// ── helpers ──────────────────────────────────────────────────────────────── //

fn take_str(p &char) string {
	if p == unsafe { nil } { return '' }
	s := unsafe { cstring_to_vstring(p) }
	C.zsys_free(p)
	return s
}

fn take_arr(pp &&char) []string {
	if pp == unsafe { nil } { return [] }
	mut r := []string{}
	mut i := 0
	for {
		p := unsafe { pp[i] }
		if p == unsafe { nil } { break }
		r << unsafe { cstring_to_vstring(p) }
		i++
	}
	C.zsys_split_free(pp)
	return r
}

// ── text / HTML ───────────────────────────────────────────────────────────── //

pub fn (u Utils) escape_html(text string) string {
	return take_str(C.zsys_escape_html(text.str, usize(text.len)))
}

pub fn (u Utils) strip_html(text string) string {
	return take_str(C.zsys_strip_html(text.str, usize(text.len)))
}

pub fn (u Utils) truncate(text string, max_chars int, suffix string) string {
	return take_str(C.zsys_truncate_text(text.str, usize(text.len),
		usize(max_chars), suffix.str))
}

pub fn (u Utils) split_text(text string, max_chars int) ![]string {
	pp := C.zsys_split_text(text.str, usize(text.len), usize(max_chars))
	if pp == unsafe { nil } { return error('zsys_split_text returned NULL') }
	return take_arr(pp)
}

pub fn (u Utils) get_args(text string, max_split int) []string {
	pp := C.zsys_get_args(text.str, usize(text.len), max_split)
	return take_arr(pp)
}

// ── numeric formatters ────────────────────────────────────────────────────── //

pub fn (u Utils) format_bytes(size i64) string {
	return take_str(C.zsys_format_bytes(size))
}

pub fn (u Utils) format_duration(seconds f64) string {
	return take_str(C.zsys_format_duration(seconds))
}

pub fn (u Utils) human_time(seconds i64, short_fmt bool) string {
	return take_str(C.zsys_human_time(seconds, if short_fmt { 1 } else { 0 }))
}

pub fn (u Utils) parse_duration(text string) i64 {
	return C.zsys_parse_duration(text.str)
}

// ── HTML formatters ───────────────────────────────────────────────────────── //

pub fn (u Utils) bold(text string, escape bool) string {
	return take_str(C.zsys_format_bold(text.str, usize(text.len),
		if escape { 1 } else { 0 }))
}

pub fn (u Utils) italic(text string, escape bool) string {
	return take_str(C.zsys_format_italic(text.str, usize(text.len),
		if escape { 1 } else { 0 }))
}

pub fn (u Utils) code(text string, escape bool) string {
	return take_str(C.zsys_format_code(text.str, usize(text.len),
		if escape { 1 } else { 0 }))
}

pub fn (u Utils) pre(text string, lang string, escape bool) string {
	return take_str(C.zsys_format_pre(text.str, usize(text.len),
		lang.str, if escape { 1 } else { 0 }))
}

pub fn (u Utils) link(text string, url string, escape bool) string {
	return take_str(C.zsys_format_link(text.str, usize(text.len),
		url.str, usize(url.len), if escape { 1 } else { 0 }))
}

pub fn (u Utils) mention(text string, user_id i64, escape bool) string {
	return take_str(C.zsys_format_mention(text.str, usize(text.len),
		user_id, if escape { 1 } else { 0 }))
}

pub fn (u Utils) underline(text string) string {
	return take_str(C.zsys_format_underline(text.str, usize(text.len)))
}

pub fn (u Utils) strikethrough(text string) string {
	return take_str(C.zsys_format_strikethrough(text.str, usize(text.len)))
}

pub fn (u Utils) spoiler(text string) string {
	return take_str(C.zsys_format_spoiler(text.str, usize(text.len)))
}

pub fn (u Utils) quote_(text string) string {
	return take_str(C.zsys_format_quote(text.str, usize(text.len)))
}
