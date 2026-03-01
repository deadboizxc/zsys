//! build.rs — generates Rust FFI bindings from zsys_core.h via bindgen.
use std::path::PathBuf;

fn main() {
    let header = PathBuf::from("../../zsys/include/zsys_core.h");
    println!("cargo:rerun-if-changed={}", header.display());
    println!("cargo:rustc-link-lib=zsys");

    let bindings = bindgen::Builder::default()
        .header(header.to_string_lossy())
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        .generate()
        .expect("Unable to generate bindings from zsys_core.h");

    let out = PathBuf::from(std::env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out.join("zsys_bindings.rs"))
        .expect("Couldn't write bindings file");
}
