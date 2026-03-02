// build.rs — auto-generate FFI bindings from zsys_core.h via bindgen
use std::{env, path::PathBuf};

fn main() {
    println!("cargo:rustc-link-lib=zsys_core");
    println!("cargo:rerun-if-changed=../../c/include/zsys_core.h");

    let bindings = bindgen::Builder::default()
        .header("../../c/include/zsys_core.h")
        .allowlist_type("ZsysI18n")
        .allowlist_function("zsys_i18n_.*")
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        .generate()
        .expect("Unable to generate bindings");

    let out = PathBuf::from(env::var("OUT_DIR").unwrap());
    bindings.write_to_file(out.join("bindings.rs")).unwrap();
}
