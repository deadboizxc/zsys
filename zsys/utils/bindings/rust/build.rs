// build.rs — auto-generate FFI bindings from zsys_utils.h via bindgen
use std::{env, path::PathBuf};

fn main() {
    println!("cargo:rustc-link-lib=zsys_utils");
    println!("cargo:rerun-if-changed=../../c/include/zsys_utils.h");

    let bindings = bindgen::Builder::default()
        .header("../../c/include/zsys_utils.h")
        .allowlist_function("zsys_free")
        .allowlist_function("zsys_split_free")
        .allowlist_function("zsys_escape_html")
        .allowlist_function("zsys_strip_html")
        .allowlist_function("zsys_truncate_text")
        .allowlist_function("zsys_split_text")
        .allowlist_function("zsys_get_args")
        .allowlist_function("zsys_format_bytes")
        .allowlist_function("zsys_format_duration")
        .allowlist_function("zsys_human_time")
        .allowlist_function("zsys_parse_duration")
        .allowlist_function("zsys_format_bold")
        .allowlist_function("zsys_format_italic")
        .allowlist_function("zsys_format_code")
        .allowlist_function("zsys_format_pre")
        .allowlist_function("zsys_format_link")
        .allowlist_function("zsys_format_mention")
        .allowlist_function("zsys_format_underline")
        .allowlist_function("zsys_format_strikethrough")
        .allowlist_function("zsys_format_spoiler")
        .allowlist_function("zsys_format_quote")
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        .generate()
        .expect("Unable to generate bindings");

    let out = PathBuf::from(env::var("OUT_DIR").unwrap());
    bindings.write_to_file(out.join("bindings.rs")).unwrap();
}
