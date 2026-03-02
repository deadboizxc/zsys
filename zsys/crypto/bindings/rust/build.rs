// build.rs — link libzsys_crypto and optionally generate bindgen bindings.
use std::{env, path::PathBuf};

fn main() {
    println!("cargo:rustc-link-lib=zsys_crypto");
    println!("cargo:rerun-if-changed=../../c/include/zsys_crypto.h");

    let bindings = bindgen::Builder::default()
        .header("../../c/include/zsys_crypto.h")
        .allowlist_function("zsys_aes_.*|zsys_rsa_.*|zsys_ecc_.*")
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        .generate()
        .expect("Unable to generate bindings");

    let out = PathBuf::from(env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out.join("bindings.rs"))
        .unwrap();
}
