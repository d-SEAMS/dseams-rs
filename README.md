# dseams-rs

Rust bindings to [d-SEAMS](https://dseams.info), the ice, clathrate and ring
analysis engine for molecular simulation frames. The C++ engine and its C
API (`libseams`, header `seams.h`) live in
[seams-core](https://github.com/d-SEAMS/seams-core); this repository holds
the two crates on top of it:

| Crate | Library name | What it is |
|---|---|---|
| [`dseams-sys`](dseams-sys) | `seams_sys` | Raw FFI declarations, generated from `seams.h` |
| [`dseams`](dseams) | `seams` | Safe handles, options structs, iterators, `Result` errors |

The crates.io name `seams` belongs to an unrelated project, hence the `d`.

```toml
[dependencies]
dseams = "2.14.0"
```

## Linking libseams

`dseams-sys` does not run bindgen; the declarations are checked in. Its
build script takes the first of:

1. **`SEAMS_LIBDIR`**: the directory holding the shared `libseams`, a meson
   build tree's `build/src` or an install prefix's `lib`. `SEAMS_INCLUDE`
   (a path list) names the header directories when they are not
   `$SEAMS_LIBDIR/../include`.
2. **Feature `bundled`**: compile the C API and Eigen 3.4.0 from the seams-core
   sources in `dseams-sys/vendor/` with the `cc` crate. x86_64 only, C++20
   with OpenMP; reads LAMMPS dumps and XYZ but not `.con` or chemfiles.
3. **pkg-config**: module `seams`, at least 2.14.0 and below 3.0.0.

The crate version tracks the seams-core release. `seams-core.env` names the
seams-core commit that CI builds and that `vendor.py` vendors; it moves to the
`v2.14.0` tag of d-SEAMS/seams-core once that tag exists.

## Building and testing against a seams-core build

```bash
git clone https://github.com/d-SEAMS/seams-core
cd seams-core
git checkout "$(. ../dseams-rs/seams-core.env && echo "$SEAMS_CORE_REF")"
pixi run meson setup bbdir -Dwith_python=false -Dwith_tests=true -Dwith_cli=false
pixi run ninja -C bbdir src/libseams.so bindings/binding_oracle
cd ../dseams-rs

export SEAMS_LIBDIR=$PWD/../seams-core/bbdir/src
export SEAMS_INCLUDE=$PWD/../seams-core/include:$SEAMS_LIBDIR
# Optional: compare every analysis with the C++ path (dseams/tests/cpp_match.rs).
export SEAMS_CPP_ORACLE=$PWD/../seams-core/bbdir/bindings/binding_oracle
export SEAMS_SOURCE_ROOT=$PWD/../seams-core
export OMP_NUM_THREADS=1

cargo fmt --all -- --check
cargo clippy --all-targets -- -D warnings
cargo test -- --test-threads=1
cargo test --examples -- --test-threads=1
```

The tests and examples get an rpath to `SEAMS_LIBDIR`; other programs need
it on `LD_LIBRARY_PATH`.

## The bundled build

```bash
python3 dseams-sys/vendor.py                       # download the pinned commit
python3 dseams-sys/vendor.py --source ../seams-core  # or git archive it from a checkout
cargo test --features bundled --test ice --examples
```

## Regenerating the declarations

```bash
python3 dseams-sys/gen_sys.py ../seams-core/include/seams.h dseams-sys/src/lib.rs
```

CI fails when the checked-in `dseams-sys/src/lib.rs` differs from this
output for the pinned header.

## Publishing

Both crates publish from the workspace, `dseams-sys` first; `vendor/` must
be filled so the `bundled` feature works from crates.io:

```bash
python3 dseams-sys/vendor.py
cargo publish --workspace --dry-run --allow-dirty
```

`--allow-dirty` is there because `vendor/` is generated and gitignored.

## Documentation

`docs/api/rust.md` is the API page and `docs/tutorials/rust.md` the
tutorial; `cargo doc --no-deps` builds the rustdoc.

## License

MIT. The bundled Eigen headers in `dseams-sys/vendor/eigen` are MPL-2.0,
with `AlignedBox.h` under BSD-3-Clause and `BFloat16.h` under Apache-2.0.
