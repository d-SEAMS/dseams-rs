// Copyright (c) d-SEAMS developers
//! Put the directory of a shared libseams on the rpath of this crate's tests
//! and examples, so they run without LD_LIBRARY_PATH. dseams-sys reports the
//! directory as `DEP_SEAMS_RPATH`; a bundled (static) build reports none.
use std::env;

fn main() {
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-env-changed=DEP_SEAMS_RPATH");
    if env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("windows") {
        return;
    }
    if let Some(dirs) = env::var_os("DEP_SEAMS_RPATH") {
        for dir in env::split_paths(&dirs) {
            println!("cargo:rustc-link-arg=-Wl,-rpath,{}", dir.display());
        }
    }
}
