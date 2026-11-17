# How to: link libseams

`dseams-sys` links `libseams` at build time. The script in
`dseams-sys/build.rs` stops at the first match below. A
`seams_version.h` from another major, or from a minor older than 2.14,
stops the build when that header is on the include path.

## A seams-core build tree

CI builds seams-core at the commit in `seams-core.env` and points the
crates at that library:

```bash
export SEAMS_LIBDIR="$PWD/../seams-core/bbdir/src"
export SEAMS_INCLUDE="$PWD/../seams-core/include:$SEAMS_LIBDIR"
cargo test -- --test-threads=1
cargo test --examples -- --test-threads=1
```

`SEAMS_LIB_DIR` is the same variable as `SEAMS_LIBDIR`. The directory
must contain `libseams.so` (or `libseams.dylib`, `seams.dll`, or
`seams.lib`). For a meson build the shared library is `bbdir/src` when
the build directory is `bbdir`. An install prefix uses `$prefix/lib`,
and the headers default to `$prefix/include` when `seams.h` is there.

`SEAMS_INCLUDE` is a path list. The meson tree keeps `seams.h` in the
source `include` directory, not next to `bbdir/src`, so the variable
has to name both.

Tests and examples of this workspace get an rpath to `SEAMS_LIBDIR`.
Any other binary needs that directory on `LD_LIBRARY_PATH`.

## pkg-config

Unset `SEAMS_LIBDIR`. Put the directory that holds `seams.pc` on
`PKG_CONFIG_PATH`. For the same meson tree that file is
`bbdir/meson-uninstalled`.

```bash
unset SEAMS_LIBDIR
export PKG_CONFIG_PATH="$PWD/../seams-core/bbdir/meson-uninstalled"
cargo test -- --test-threads=1
```

The accepted versions are 2.14.0 up to, and not including, 3.0.0. The
installed library keeps every reader it was configured with, including
`.con` and chemfiles when those options were on.

## The bundled feature

```bash
python3 dseams-sys/vendor.py
cargo test --features bundled --test ice --examples -- --test-threads=1
```

`vendor.py` writes `dseams-sys/vendor/` from the commit in
`seams-core.env` and from the Eigen 3.4.0 tarball. `vendor/` is
gitignored. `python3 dseams-sys/vendor.py --source ../seams-core`
archives that commit out of a checkout that already has it.

Without `vendor/`, `SEAMS_SOURCE_DIR` may name a checkout at the same
commit. Eigen then comes from `EIGEN3_INCLUDE_DIR` or from pkg-config
module `eigen3` at 3.4.0 or newer.

The bundled build is x86_64 only, because `shell_classify.cpp` uses
AVX2. It needs a C++20 compiler and OpenMP (GCC links `gomp`, Clang
links `omp`). It reads LAMMPS dumps and XYZ. `.con` and chemfiles stay
on the pkg-config or `SEAMS_LIBDIR` library. `SEAMS_LIBDIR` still wins
when it is set, including over `--features bundled`.

The published crate ships a filled `vendor/`, so a downstream
`--features bundled` build does not run `vendor.py`.
