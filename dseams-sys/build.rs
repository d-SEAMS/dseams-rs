// Copyright (c) d-SEAMS developers
//! Find libseams for the raw bindings.
//!
//! The declarations in src/lib.rs are generated ahead of time from
//! include/seams.h, so this script only has to link the library:
//!
//! 1. `SEAMS_LIBDIR` (or `SEAMS_LIB_DIR`): link the shared libseams in that
//!    directory. `SEAMS_INCLUDE` optionally names the header directories.
//! 2. Feature `bundled`: compile the C API from the pinned seams-core sources
//!    in `vendor/` (or a checkout named by `SEAMS_SOURCE_DIR`).
//! 3. Otherwise: pkg-config module `seams`, 2.14.0 or newer within major 2.
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

fn main() {
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=sources.txt");
    for var in [
        "SEAMS_LIBDIR",
        "SEAMS_LIB_DIR",
        "SEAMS_INCLUDE",
        "SEAMS_SOURCE_DIR",
        "EIGEN3_INCLUDE_DIR",
    ] {
        println!("cargo:rerun-if-env-changed={var}");
    }

    // rustdoc does not link, and docs.rs has no libseams.
    if env::var_os("DOCS_RS").is_some() {
        return;
    }

    if let Some(dir) = env::var_os("SEAMS_LIBDIR").or_else(|| env::var_os("SEAMS_LIB_DIR")) {
        link_prebuilt(&PathBuf::from(dir));
        return;
    }

    #[cfg(feature = "bundled")]
    build_bundled();
    #[cfg(not(feature = "bundled"))]
    probe_pkg_config();
}

fn crate_version() -> (u32, u32) {
    let major = env::var("CARGO_PKG_VERSION_MAJOR")
        .unwrap()
        .parse()
        .unwrap();
    let minor = env::var("CARGO_PKG_VERSION_MINOR")
        .unwrap()
        .parse()
        .unwrap();
    (major, minor)
}

/// The bindings cover the 2.14 C API. A later minor release only adds
/// functions, so any 2.x at or above 2.14 links; a different major does not.
fn check_header_version(include: &[PathBuf]) {
    let Some(header) = include
        .iter()
        .map(|dir| dir.join("seams_version.h"))
        .find(|path| path.is_file())
    else {
        return;
    };
    let text = fs::read_to_string(&header).unwrap();
    let field = |name: &str| -> Option<u32> {
        text.lines().find_map(|line| {
            let rest = line.trim().strip_prefix("#define ")?.strip_prefix(name)?;
            rest.trim().parse().ok()
        })
    };
    let (Some(major), Some(minor)) = (field("SEAMS_VERSION_MAJOR"), field("SEAMS_VERSION_MINOR"))
    else {
        return;
    };
    let (want_major, want_minor) = crate_version();
    if major != want_major || minor < want_minor {
        panic!(
            "{} is libseams {major}.{minor}; dseams-sys {} needs {want_major}.x at or above {want_major}.{want_minor}",
            header.display(),
            env::var("CARGO_PKG_VERSION").unwrap()
        );
    }
}

fn export_include(include: &[PathBuf]) {
    if include.is_empty() {
        return;
    }
    let joined = env::join_paths(include).unwrap();
    println!("cargo:include={}", joined.to_string_lossy());
}

/// Dependents read this as `DEP_SEAMS_RPATH`; the dseams crate turns it into
/// an rpath for its own tests and examples.
fn export_rpath(dirs: &[PathBuf]) {
    if dirs.is_empty() {
        return;
    }
    let joined = env::join_paths(dirs).unwrap();
    println!("cargo:rpath={}", joined.to_string_lossy());
}

fn link_prebuilt(dir: &Path) {
    let found = fs::read_dir(dir)
        .unwrap_or_else(|e| panic!("SEAMS_LIBDIR={}: {e}", dir.display()))
        .filter_map(Result::ok)
        .any(|entry| {
            let name = entry.file_name();
            let name = name.to_string_lossy();
            name.starts_with("libseams.") || name == "seams.lib" || name == "seams.dll"
        });
    if !found {
        panic!("SEAMS_LIBDIR={} holds no libseams", dir.display());
    }
    println!("cargo:rustc-link-search=native={}", dir.display());
    println!("cargo:rustc-link-lib=dylib=seams");

    let mut include: Vec<PathBuf> = match env::var_os("SEAMS_INCLUDE") {
        Some(dirs) => env::split_paths(&dirs).collect(),
        None => Vec::new(),
    };
    if include.is_empty() {
        // An install prefix keeps the headers next to lib/.
        if let Some(prefix) = dir.parent() {
            if prefix.join("include/seams.h").is_file() {
                include.push(prefix.join("include"));
            }
        }
    }
    if let Some(missing) = include.iter().find(|d| !d.is_dir()) {
        panic!(
            "SEAMS_INCLUDE names {}, which is not a directory",
            missing.display()
        );
    }
    if !include.is_empty() && !include.iter().any(|d| d.join("seams.h").is_file()) {
        panic!(
            "no seams.h under SEAMS_INCLUDE={}",
            env::join_paths(&include).unwrap().to_string_lossy()
        );
    }
    check_header_version(&include);
    export_include(&include);
    export_rpath(&[dir.to_path_buf()]);
}

#[cfg(not(feature = "bundled"))]
fn probe_pkg_config() {
    let (major, minor) = crate_version();
    let lib = pkg_config::Config::new()
        .range_version(format!("{major}.{minor}.0").as_str()..format!("{}.0.0", major + 1).as_str())
        .probe("seams")
        .unwrap_or_else(|e| {
            panic!(
                "libseams not found. Set SEAMS_LIBDIR to the directory holding libseams, \
                 add the directory holding seams.pc to PKG_CONFIG_PATH, \
                 or enable the `bundled` feature.\n{e}"
            )
        });
    check_header_version(&lib.include_paths);
    export_include(&lib.include_paths);
    export_rpath(&lib.link_paths);
}

#[cfg(feature = "bundled")]
fn source_root(manifest: &Path) -> PathBuf {
    let vendored = manifest.join("vendor");
    if vendored.join("src/seams_api.cpp").is_file() {
        return vendored;
    }
    if let Some(dir) = env::var_os("SEAMS_SOURCE_DIR") {
        let checkout = PathBuf::from(dir);
        if checkout.join("src/seams_api.cpp").is_file() {
            return checkout;
        }
        panic!(
            "SEAMS_SOURCE_DIR={} is not a seams-core checkout",
            checkout.display()
        );
    }
    panic!(
        "feature `bundled` needs the seams-core sources: run `python3 dseams-sys/vendor.py` \
         in the dseams-rs repository, or set SEAMS_SOURCE_DIR to a seams-core checkout \
         at the tag in seams-core.env"
    );
}

#[cfg(feature = "bundled")]
fn eigen_include(root: &Path) -> Vec<PathBuf> {
    let vendored = root.join("eigen");
    if vendored.join("Eigen/Core").is_file() {
        return vec![vendored];
    }
    if let Ok(dir) = env::var("EIGEN3_INCLUDE_DIR") {
        return vec![PathBuf::from(dir)];
    }
    match pkg_config::Config::new()
        .atleast_version("3.4.0")
        .cargo_metadata(false)
        .probe("eigen3")
    {
        Ok(lib) => lib.include_paths,
        Err(e) => {
            panic!("Eigen >= 3.4.0 not found (vendor/eigen, EIGEN3_INCLUDE_DIR, pkg-config): {e}")
        }
    }
}

#[cfg(feature = "bundled")]
fn build_bundled() {
    let target_arch = env::var("CARGO_CFG_TARGET_ARCH").unwrap();
    if target_arch != "x86_64" {
        panic!(
            "the bundled libseams needs x86_64 (shell_classify.cpp uses AVX2 intrinsics); \
             on {target_arch} build without it and link an installed libseams"
        );
    }
    let manifest = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap());
    let root = source_root(&manifest);
    let out = PathBuf::from(env::var("OUT_DIR").unwrap());

    let template = fs::read_to_string(root.join("include/seams_version.h.in")).unwrap();
    let header = template
        .replace("@MAJOR@", &env::var("CARGO_PKG_VERSION_MAJOR").unwrap())
        .replace("@MINOR@", &env::var("CARGO_PKG_VERSION_MINOR").unwrap())
        .replace("@PATCH@", &env::var("CARGO_PKG_VERSION_PATCH").unwrap())
        .replace(
            "@STRING@",
            &format!(
                "{}.{}.{}",
                env::var("CARGO_PKG_VERSION_MAJOR").unwrap(),
                env::var("CARGO_PKG_VERSION_MINOR").unwrap(),
                env::var("CARGO_PKG_VERSION_PATCH").unwrap()
            ),
        );
    let generated = out.join("include");
    fs::create_dir_all(&generated).unwrap();
    fs::write(generated.join("seams_version.h"), header).unwrap();

    let mut core = Vec::new();
    let mut avx2 = Vec::new();
    let mut avx512 = Vec::new();
    for line in fs::read_to_string(manifest.join("sources.txt"))
        .unwrap()
        .lines()
    {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let (bucket, rel) = match line.split_once(':') {
            Some(("avx2", rel)) => (&mut avx2, rel.trim()),
            Some(("avx512", rel)) => (&mut avx512, rel.trim()),
            Some((tag, _)) => panic!("sources.txt: unknown tag {tag}"),
            None => (&mut core, line),
        };
        let path = root.join(rel);
        println!("cargo:rerun-if-changed={}", path.display());
        bucket.push(path);
    }

    let eigen = eigen_include(&root);
    let base = || {
        let mut build = cc::Build::new();
        build
            .cpp(true)
            .std("c++20")
            .opt_level(2)
            .warnings(false)
            .flag("-w")
            .flag("-fopenmp")
            .define("SEAMS_HAS_OPENMP", "1")
            .define("EIGEN_MPL2_ONLY", None)
            .include(root.join("src/include/internal"))
            .include(root.join("include"))
            .include(&generated)
            .includes(&eigen);
        if env::var_os("CARGO_CFG_DEBUG_ASSERTIONS").is_none() {
            build.define("NDEBUG", None);
        }
        build
    };

    let mut objects = Vec::new();
    let mut simd = base();
    simd.flag("-mavx2").flag("-mfma").files(&avx2);
    objects.extend(simd.compile_intermediates());
    let mut wide = base();
    wide.flag("-mavx512f")
        .flag("-mavx512dq")
        .flag("-mfma")
        .files(&avx512);
    objects.extend(wide.compile_intermediates());

    let mut lib = base();
    lib.define("SEAMS_YLM_AVX512", "1")
        .files(&core)
        .objects(&objects);
    let compiler = lib.get_compiler();
    lib.compile("seams_bundled");

    if compiler.is_like_clang() {
        println!("cargo:rustc-link-lib=omp");
    } else {
        println!("cargo:rustc-link-lib=gomp");
    }
    // rustc drives the link with lld (or cc, not g++). Neither searches
    // GCC's private directory, which is where the unversioned libstdc++
    // and libgomp live.
    add_cxx_lib_search(&compiler);
    export_include(&[root.join("include"), generated]);
}

#[cfg(feature = "bundled")]
fn add_cxx_lib_search(compiler: &cc::Tool) {
    for name in ["libstdc++.so", "libc++.so", "libgomp.so", "libomp.so"] {
        let Ok(output) = std::process::Command::new(compiler.path())
            .arg(format!("-print-file-name={name}"))
            .output()
        else {
            continue;
        };
        if !output.status.success() {
            continue;
        }
        let text = String::from_utf8_lossy(&output.stdout);
        let path = Path::new(text.trim());
        if let Some(dir) = path.parent() {
            if path.is_file() {
                println!("cargo:rustc-link-search=native={}", dir.display());
            }
        }
    }
}
