// D binding for zsys_log via extern(C).
//
// Build: dmd log.d -L-lzsys_log
//
// Usage:
//   auto log = new Log();
//   writeln(log.ansiColor("hello", "31"));
//   writeln(log.formatJsonLog("INFO", "started", "2024-01-01T00:00:00Z"));
//   writeln(log.printBox("title", 2));
//   writeln(log.printSeparator("─", 40));
//   writeln(log.printProgress(7, 10, "Loading", 20));

module zsys.log;

import core.stdc.stdlib : free;
import std.string : toStringz, fromStringz;

// ── raw C declarations ───────────────────────────────────────────────────── //

extern(C) {
    char* zsys_ansi_color(const char* text, const char* code);
    char* zsys_format_json_log(const char* level, const char* message,
                               const char* ts);
    char* zsys_print_box_str(const char* text, int padding);
    char* zsys_print_separator_str(const char* ch, int length);
    char* zsys_print_progress_str(int current, int total,
                                  const char* prefix, int bar_length);
}

// ── safe D wrapper ───────────────────────────────────────────────────────── //

private string take(char* p) {
    assert(p, "zsys function returned NULL");
    scope(exit) free(p);
    return fromStringz(p).idup;
}

class Log {
    /// Wrap text with an ANSI escape sequence (e.g. code="31" for red).
    string ansiColor(string text, string code) {
        return take(zsys_ansi_color(text.toStringz, code.toStringz));
    }

    /// Format a JSON log line: {"level":"…","message":"…","ts":"…"}.
    string formatJsonLog(string level, string message, string ts) {
        return take(zsys_format_json_log(
            level.toStringz, message.toStringz, ts.toStringz));
    }

    /// Render a Unicode box (╔══╗ style) around text.
    string printBox(string text, int padding = 1) {
        return take(zsys_print_box_str(text.toStringz, padding));
    }

    /// Repeat ch length times to build a separator line.
    string printSeparator(string ch, int length) {
        return take(zsys_print_separator_str(ch.toStringz, length));
    }

    /// Render a text progress bar: [###---] current/total (N%).
    string printProgress(int current, int total,
                         string prefix = "", int barLength = 20) {
        return take(zsys_print_progress_str(
            current, total, prefix.toStringz, barLength));
    }
}
