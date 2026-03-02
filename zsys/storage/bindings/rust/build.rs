use std::env;
use std::path::PathBuf;

fn main() {
    println!("cargo:rustc-link-lib=zsys_storage");
    println!("cargo:rerun-if-changed=../../c/include/zsys_storage.h");

    let bindings = bindgen::Builder::default()
        .header("../../c/include/zsys_storage.h")
        .allowlist_function("zsys_kv_.*")
        .allowlist_function("zsys_free")
        .allowlist_type("ZsysKV")
        .allowlist_type("ZsysKVIterFn")
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        .generate()
        .expect("Unable to generate bindings");

    let out = PathBuf::from(env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out.join("bindings.rs"))
        .expect("Couldn't write bindings");
}
