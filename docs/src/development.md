# Development

The engine, the C API, and the C++ oracle live in
[seams-core](https://github.com/d-SEAMS/seams-core). This repository is
the Rust side: the safe crate, the generated declarations, the build
script, this book, and the examples. A new analysis or a new C function
lands in seams-core first. It is wrapped here after `SEAMS_CORE_REF` in
`seams-core.env` moves to a commit that contains it.

Contributor conventions for this repository are in `AGENTS.md` at the
repository root. The engine book is
[docs.dseams.info](https://docs.dseams.info).

## Build and test

Build seams-core at the pinned commit with tests enabled, then run the
checks from the repository root. The workflow file
`.github/workflows/ci.yml` is the same sequence.

```bash
. ./seams-core.env
git clone "$SEAMS_CORE_REPO" ../seams-core
git -C ../seams-core checkout "$SEAMS_CORE_REF"
(cd ../seams-core && pixi run meson setup bbdir -Dwith_tests=true -Dwith_cli=false \
 && pixi run ninja -C bbdir src/libseams.so bindings/binding_oracle)

export SEAMS_LIBDIR=$PWD/../seams-core/bbdir/src
export SEAMS_INCLUDE=$PWD/../seams-core/include:$SEAMS_LIBDIR
export SEAMS_CPP_ORACLE=$PWD/../seams-core/bbdir/bindings/binding_oracle
export SEAMS_SOURCE_ROOT=$PWD/../seams-core
export OMP_NUM_THREADS=1

cargo fmt --all -- --check
cargo clippy --all-targets -- -D warnings
cargo test -- --test-threads=1
cargo test --examples -- --test-threads=1
RUSTDOCFLAGS="-D warnings" cargo doc --no-deps
```

`dseams/tests/ice.rs` calls every safe wrapper on the cubic cell.
`dseams/tests/cpp_match.rs` compares those analyses with the C++ oracle
on ice Ih, sI, an XYZ file, a CON file, and the triclinic sH dump. It
skips, and says so, when `SEAMS_CPP_ORACLE` or `SEAMS_SOURCE_ROOT` is
unset. `dseams/examples/` holds `ice`, `minimal`, `ice_ih`, `lang_tasks`,
and `binding_overhead`. `cargo test --examples` checks their output.

Unset `SEAMS_LIBDIR` and set
`PKG_CONFIG_PATH=$PWD/../seams-core/bbdir/meson-uninstalled` with
`--no-default-features` to test the pkg-config path against the same tree.

The bundled feature, from a filled `dseams-sys/vendor/`:

```bash
python3 dseams-sys/vendor.py --source ../seams-core
cargo clippy --features bundled --all-targets -- -D warnings
cargo test --features bundled --test ice --examples -- --test-threads=1
cargo +1.85.0 build --features bundled --all-targets
```

`1.85.0` is the minimum supported compiler (`rust-version` in the
workspace manifest).

## Declarations

`dseams-sys/src/lib.rs` is generated. Regenerate it when `seams.h` changes,
and do not edit it by hand:

```bash
python3 dseams-sys/gen_sys.py ../seams-core/include/seams.h dseams-sys/src/lib.rs
```

CI diffs that file against the generator output for the pinned header.
`dseams-sys/sources.txt` lists the translation units the bundled feature
compiles, relative to seams-core. Update it when the link closure of
`src/seams_api.cpp` changes.

## Documentation

This book is the user-facing documentation:

```bash
mdbook build docs
```

mdBook 0.5.4 is the version CI installs. The API reference is rustdoc,
as the [API page](api.md) describes. After `cargo doc --no-deps --workspace`,
the coverage check fails if a public symbol is missing from the HTML:

```bash
DOCS_RS=1 cargo doc --no-deps --workspace
python3 docs/check_rustdoc.py target/doc
python3 docs/check_book.py docs/book
```

`check_rustdoc.py` parses `dseams/src/lib.rs` and `dseams-sys/src/lib.rs`.
Hiding a public item from rustdoc fails that check. `check_book.py`
checks the built HTML: internal links, the tutorial recordings, and the
engine-book links.

## Changelog

User-visible changes add a fragment under `changelog.d/`. The names and
the types are in `changelog.d/README.md`. Commits use Conventional
Commits.

The release order, from the seams-core tag through `cargo publish` and
the tag on this repository, is in `AGENTS.md`.
