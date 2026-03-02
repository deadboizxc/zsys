use std::path::PathBuf;

fn main() {
    // Link against the shared library.
    println!("cargo:rustc-link-lib=zsys_core");

    // Re-run if the header changes.
    let header = "../../c/include/zsys_core.h";
    println!("cargo:rerun-if-changed={header}");

    let bindings = bindgen::Builder::default()
        .header(header)
        // Only generate bindings for Router and Registry symbols.
        .allowlist_function("zsys_router_.*")
        .allowlist_function("zsys_registry_.*")
        .allowlist_type("ZsysRouter")
        .allowlist_type("ZsysRegistry")
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        .generate()
        .expect("Unable to generate bindings");

    let out = PathBuf::from(std::env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out.join("bindings.rs"))
        .expect("Couldn't write bindings");
}
