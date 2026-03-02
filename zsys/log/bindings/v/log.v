// V (Vlang) binding for zsys_log.
//
// Build: v -cflags '-lzsys_log' main.v
//
// Usage:
//   mut log := zsyslog.new_log()
//   println(log.ansi_color('hello', '31'))
//   println(log.format_json_log('INFO', 'started', '2024-01-01T00:00:00Z'))
//   println(log.print_box('title', 2))
//   println(log.print_separator('─', 40))
//   println(log.print_progress(7, 10, 'Loading', 20))

module zsyslog

#flag -lzsys_log
#include "../../c/include/zsys_log.h"

fn C.zsys_ansi_color(text &char, code &char) &char
fn C.zsys_format_json_log(level &char, message &char, ts &char) &char
fn C.zsys_print_box_str(text &char, padding int) &char
fn C.zsys_print_separator_str(ch &char, length int) &char
fn C.zsys_print_progress_str(current int, total int, prefix &char, bar_length int) &char

pub struct Log {}

pub fn new_log() Log {
    return Log{}
}

fn take(p &char) string {
    assert p != unsafe { nil }, 'zsys function returned NULL'
    s := unsafe { cstring_to_vstring(p) }
    unsafe { C.free(p) }
    return s
}

// ansi_color wraps text with an ANSI escape sequence (e.g. code="31" for red).
pub fn (l Log) ansi_color(text string, code string) string {
    return take(C.zsys_ansi_color(text.str, code.str))
}

// format_json_log formats a JSON log line: {"level":"…","message":"…","ts":"…"}.
pub fn (l Log) format_json_log(level string, message string, ts string) string {
    return take(C.zsys_format_json_log(level.str, message.str, ts.str))
}

// print_box renders a Unicode box (╔══╗ style) around text.
pub fn (l Log) print_box(text string, padding int) string {
    return take(C.zsys_print_box_str(text.str, padding))
}

// print_separator repeats ch length times to build a separator line.
pub fn (l Log) print_separator(ch string, length int) string {
    return take(C.zsys_print_separator_str(ch.str, length))
}

// print_progress renders a text progress bar: [###---] current/total (N%).
pub fn (l Log) print_progress(current int, total int, prefix string, bar_length int) string {
    return take(C.zsys_print_progress_str(current, total, prefix.str, bar_length))
}
