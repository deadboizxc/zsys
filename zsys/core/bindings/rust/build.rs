use std::env;
use std::path::PathBuf;

fn main() {
    // Link against libzsys_core.so
    println!("cargo:rustc-link-lib=zsys_core");
    println!("cargo:rerun-if-changed=../../c/include/zsys_user.h");
    println!("cargo:rerun-if-changed=../../c/include/zsys_chat.h");
    println!("cargo:rerun-if-changed=../../c/include/zsys_client.h");

    let include_dir = PathBuf::from("../../c/include");

    let bindings = bindgen::Builder::default()
        // Feed all three headers through a single wrapper
        .header_contents(
            "wrapper.h",
            r#"
#include "zsys_user.h"
#include "zsys_chat.h"
#include "zsys_client.h"
"#,
        )
        .clang_arg(format!("-I{}", include_dir.display()))
        // Allowlists — keep only zsys symbols
        .allowlist_function("zsys_user_.*")
        .allowlist_type("ZsysUser")
        .allowlist_function("zsys_chat_.*")
        .allowlist_type("ZsysChat")
        .allowlist_type("ZsysChatType")
        .allowlist_function("zsys_client_.*")
        .allowlist_type("ZsysClientConfig")
        .allowlist_type("ZsysClientMode")
        .allowlist_function("zsys_free")
        // Derive common traits
        .derive_debug(true)
        .derive_copy(false)
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        .generate()
        .expect("bindgen failed to generate bindings");

    let out = PathBuf::from(env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out.join("bindings.rs"))
        .expect("failed to write bindings.rs");
}
