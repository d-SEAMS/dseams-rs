# dseams-sys

Raw FFI declarations for the [d-SEAMS](https://dseams.info) C API
(`include/seams.h` in seams-core). Most code wants the safe
[`dseams`](https://crates.io/crates/dseams) crate instead.

The crates.io name `seams` belongs to an unrelated project, so the
packages are `dseams-sys` and `dseams`. The library names are unchanged:
this crate is `seams_sys`.

```bash
cargo add dseams-sys --features bundled
```

```rust
use std::ffi::CStr;

fn main() {
    let text = unsafe { CStr::from_ptr(seams_sys::seams_version_string()) };
    println!("libseams {}", text.to_str().unwrap());
    assert_eq!(seams_sys::SEAMS_OK, 0);
}
```

```text
libseams 2.14.1
```

## How libseams is found

The declarations are generated from `seams.h` ahead of time, so building
needs the library, not the header or libclang. The build script uses the
first of these that applies:

1. `SEAMS_LIBDIR` is set (`SEAMS_LIB_DIR` also works): link the shared
   `libseams` in that directory, which is the `src` directory of a meson
   build tree or the library directory of an install prefix.
   `SEAMS_INCLUDE`, a path list, optionally names the header directories,
   and the build then checks the version in `seams_version.h`.
2. Feature `bundled`: compile the C API, the analyses behind it, and
   Eigen 3.4.0 with the `cc` crate, from sources in the package. This needs
   a C++20 compiler with OpenMP (GCC 11 or newer) on x86_64, because the
   shell classifier uses AVX2. The bundled build reads LAMMPS dumps and XYZ,
   not `.con` files or the chemfiles formats.
3. Otherwise the pkg-config module `seams`, at least 2.14.0 and below 3.0.0
   (set `PKG_CONFIG_PATH` to the directory that holds `seams.pc`). The
   installed library keeps every reader it was built with, including `.con`
   and chemfiles.

A `seams_version.h` from another major release or from a minor release older
than 2.14 stops the build. A shared library must also be visible to the
loader when a program runs, through `LD_LIBRARY_PATH` or an rpath. The
bundled build links statically and needs neither.

The [link how-to](https://rust.dseams.info/user-guide/link.html) has the
commands, including how to build `libseams` from seams-core.

## License

The crate and d-SEAMS are MIT. The bundled Eigen is MPL-2.0, with
`AlignedBox.h` under BSD-3-Clause and `BFloat16.h` under Apache-2.0. The
texts are in `vendor/eigen/`.
