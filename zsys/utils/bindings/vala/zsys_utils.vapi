// Vala binding for ZsysUtils
//
// Usage:
//   var u = new Zsys.Utils();
//   print(u.escape_html("<b>hi</b>"));
//   print(u.format_bytes(1536));

[CCode(cheader_filename = "zsys_utils.h", cprefix = "zsys_")]
namespace Zsys {

    [CCode(cname = "zsys_free")]
    public static void free_str([CCode(type = "char*")] string ptr);

    [CCode(cname = "zsys_split_free")]
    public static void split_free([CCode(array_null_terminated = true)] string[] chunks);

    namespace Utils {

        [CCode(cname = "zsys_escape_html")]
        public static string escape_html(string text, size_t len);

        [CCode(cname = "zsys_strip_html")]
        public static string strip_html(string text, size_t len);

        [CCode(cname = "zsys_truncate_text")]
        public static string truncate_text(string text, size_t len,
            size_t max_chars, string? suffix);

        [CCode(cname = "zsys_split_text", array_null_terminated = true)]
        public static string[] split_text(string text, size_t len,
            size_t max_chars);

        [CCode(cname = "zsys_get_args", array_null_terminated = true)]
        public static string[] get_args(string text, size_t len, int max_split);

        [CCode(cname = "zsys_format_bytes")]
        public static string format_bytes(int64 size);

        [CCode(cname = "zsys_format_duration")]
        public static string format_duration(double seconds);

        [CCode(cname = "zsys_human_time")]
        public static string human_time(long seconds, int short_fmt);

        [CCode(cname = "zsys_parse_duration")]
        public static long parse_duration(string text);

        [CCode(cname = "zsys_format_bold")]
        public static string format_bold(string text, size_t len, int escape);

        [CCode(cname = "zsys_format_italic")]
        public static string format_italic(string text, size_t len, int escape);

        [CCode(cname = "zsys_format_code")]
        public static string format_code(string text, size_t len, int escape);

        [CCode(cname = "zsys_format_pre")]
        public static string format_pre(string text, size_t len,
            string? lang, int escape);

        [CCode(cname = "zsys_format_link")]
        public static string format_link(string text, size_t tlen,
            string url, size_t ulen, int escape);

        [CCode(cname = "zsys_format_mention")]
        public static string format_mention(string text, size_t len,
            int64 user_id, int escape);

        [CCode(cname = "zsys_format_underline")]
        public static string format_underline(string text, size_t len);

        [CCode(cname = "zsys_format_strikethrough")]
        public static string format_strikethrough(string text, size_t len);

        [CCode(cname = "zsys_format_spoiler")]
        public static string format_spoiler(string text, size_t len);

        [CCode(cname = "zsys_format_quote")]
        public static string format_quote(string text, size_t len);
    }
}
