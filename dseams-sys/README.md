# dseams-sys

Raw FFI declarations for the [d-SEAMS](https://dseams.info) C API
(`include/seams.h` in seams-core). Most code wants the safe
[`dseams`](https://crates.io/crates/dseams) crate instead.

The crates.io name `seams` belongs to an unrelated project, so the
packages are `dseams-sys` and `dseams`. The library names are unchanged:

```toml
[dependencies]
dseams-sys = "2.14.0"
```

```rust
use seams_sys::{seams_version_string, SEAMS_OK};
```

## How libseams is found

The declarations in `src/lib.rs` are generated from `seams.h` ahead of
time (`gen_sys.py`), so building needs the library, not the header or
libclang. `build.rs` takes the first of:

1. `SEAMS_LIBDIR` set (`SEAMS_LIB_DIR` also works): link the shared
   `libseams` in that directory, a meson build tree (`build/src`) or an
   install prefix (`$prefix/lib`). `SEAMS_INCLUDE`, a path list, names
   the header directories; for a prefix it defaults to `$prefix/include`.
2. Feature `bundled`: compile the C API, the analyses behind it, and
   Eigen 3.4.0 with the `cc` crate, from `vendor/`. The published crate
   ships `vendor/`; in a git checkout, run `python3 dseams-sys/vendor.py`
   first or set `SEAMS_SOURCE_DIR` to a seams-core checkout at the commit
   in `seams-core.env`. This needs a C++20 compiler with OpenMP (GCC 11
   or newer) on x86_64; the shell classifier uses AVX2. The bundled build
   reads LAMMPS dumps and XYZ, not `.con` or the chemfiles formats.
3. Otherwise pkg-config module `seams`, at least 2.14.0 and below 3.0.0
   (`PKG_CONFIG_PATH=$prefix/lib/pkgconfig`, or `build/meson-uninstalled`
   for a meson build tree). The installed library keeps every reader it
   was configured with, including `.con` and chemfiles.

A `seams_version.h` from another major release or an older minor one
stops the build. For a shared library, `DEP_SEAMS_RPATH` carries its
directory to dependent build scripts; the run-time loader still needs it
on `LD_LIBRARY_PATH` or an rpath for binaries outside this workspace.

## License

The crate and d-SEAMS are MIT. The bundled Eigen is MPL-2.0, with
`AlignedBox.h` under BSD-3-Clause and `BFloat16.h` under Apache-2.0; the
texts are in `vendor/eigen/`.
