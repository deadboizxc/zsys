// build.rs — link libzsys_log and (optionally) generate bindings via bindgen.
use std::{env, path::PathBuf};

fn main() {
    println!("cargo:rustc-link-lib=zsys_log");
    println!("cargo:rerun-if-changed=../../c/include/zsys_log.h");

    let bindings = bindgen::Builder::default()
        .header("../../c/include/zsys_log.h")
        .allowlist_function("zsys_ansi_color")
        .allowlist_function("zsys_format_json_log")
        .allowlist_function("zsys_print_box_str")
        .allowlist_function("zsys_print_separator_str")
        .allowlist_function("zsys_print_progress_str")
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        .generate()
        .expect("Unable to generate bindings");

    let out = PathBuf::from(env::var("OUT_DIR").unwrap());
    bindings.write_to_file(out.join("bindings.rs")).unwrap();
}
