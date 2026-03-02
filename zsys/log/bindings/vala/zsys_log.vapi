// Vala binding for zsys_log.
//
// Usage:
//   var colored = ZsysLog.ansi_color("hello", "31");
//   var json    = ZsysLog.format_json_log("INFO", "started", "2024-01-01T00:00:00Z");
//   var boxx    = ZsysLog.print_box_str("title", 2);
//   var sep     = ZsysLog.print_separator_str("─", 40);
//   var prog    = ZsysLog.print_progress_str(7, 10, "Loading", 20);

[CCode(cheader_filename = "zsys_log.h", cprefix = "zsys_")]
namespace ZsysLog {

    [CCode(cname = "zsys_ansi_color")]
    public string? ansi_color(string text, string code);

    [CCode(cname = "zsys_format_json_log")]
    public string? format_json_log(string level, string message, string ts);

    [CCode(cname = "zsys_print_box_str")]
    public string? print_box_str(string text, int padding);

    [CCode(cname = "zsys_print_separator_str")]
    public string? print_separator_str(string ch, int length);

    [CCode(cname = "zsys_print_progress_str")]
    public string? print_progress_str(int current, int total,
                                      string? prefix, int bar_length);
}
