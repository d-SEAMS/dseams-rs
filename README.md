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
2. **Feature `bundled`** (enabled by default): compile the C API and
   Eigen 3.4.0 from the seams-core sources in `dseams-sys/vendor/` with
   the `cc` crate. x86_64 only, C++20 with OpenMP; reads LAMMPS dumps
   and XYZ but not `.con` or chemfiles.
3. **pkg-config** (with `default-features = false`): module `seams`, at
   least 2.14.0 and below 3.0.0.

The crate version tracks the seams-core release. `seams-core.env` names the
seams-core tag that CI builds and that `vendor.py` vendors: `v2.14.0` of
[d-SEAMS/seams-core](https://github.com/d-SEAMS/seams-core).

## Building and testing against a seams-core build

```bash
. dseams-rs/seams-core.env
git clone "$SEAMS_CORE_REPO" seams-core
cd seams-core
git checkout "$SEAMS_CORE_REF"
pixi run meson setup bbdir -Dwith_tests=true -Dwith_cli=false
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
python3 dseams-sys/vendor.py                       # download the pinned tag
python3 dseams-sys/vendor.py --source ../seams-core  # or git archive it from a checkout
cargo test --features bundled --test ice --examples
```

## Examples

`dseams/examples/` holds `ice` (a built diamond cell), `minimal` (the GenIce
sI cell), `ice_ih` (the ice Ih census) and `lang_tasks` (the census every
d-SEAMS language front prints, shown in the ice Ih tutorial). Each
reads its dump from `dseams/tests/data/` unless a path is given, and
`cargo test --examples` checks its output.

## Regenerating the declarations

```bash
python3 dseams-sys/gen_sys.py ../seams-core/include/seams.h dseams-sys/src/lib.rs
```

CI fails when the checked-in `dseams-sys/src/lib.rs` differs from this
output for the pinned header.

## Publishing

Both crates publish from the workspace, `dseams-sys` first. `vendor/` must
be filled so the `bundled` feature works from crates.io. Pushing the tag
`vX.Y.Z` runs [`.github/workflows/publish.yml`](.github/workflows/publish.yml),
which vendors the seams-core tag and publishes `dseams-sys`, then `dseams`.

```bash
python3 dseams-sys/vendor.py
cargo publish --workspace --dry-run --allow-dirty
```

`--allow-dirty` is there because `vendor/` is generated and gitignored.
`--workspace` checks `dseams` against the `dseams-sys` package just built.
A lone `cargo publish -p dseams` waits until that version is on crates.io,
which is how the tag workflow publishes them. The tag workflow
authenticates with crates.io trusted publishing via GitHub OIDC
(`publish.yml` in the `release` environment).

## Development

### Relation to seams-core

seams-core owns the engine, the C API and its header, the CLI, and the C++
oracle `binding_oracle` that `dseams/tests/cpp_match.rs` compares against.
This repository owns the Rust side only. A new analysis, a changed number or
a new C function lands in seams-core first; it is bound here once a
seams-core commit carries it, by moving `SEAMS_CORE_REF` in
`seams-core.env` and regenerating `dseams-sys/src/lib.rs`. CI always builds
seams-core at that ref.

### Against a local seams-core checkout

Keep seams-core next to this repository, as in
[Building and testing against a seams-core build](#building-and-testing-against-a-seams-core-build):
`meson setup` with `-Dwith_tests=true` also builds the oracle, and
`SEAMS_LIBDIR` points at its `bbdir/src`.

To try an unreleased engine change, check out that branch in
`../seams-core` instead of the pinned ref and rebuild `bbdir`. The tests
load `libseams.so` through the rpath at run time, so they pick up the
rebuilt library without a `cargo clean`. Unset `SEAMS_LIBDIR` and set
`PKG_CONFIG_PATH=$PWD/../seams-core/bbdir/meson-uninstalled` to exercise
the pkg-config path against the same tree. With `dseams-sys/vendor/`
absent, `SEAMS_SOURCE_DIR=$PWD/../seams-core` and `--features bundled`
compile the bundled copy from that checkout without running `vendor.py`;
Eigen 3.4 then comes from `EIGEN3_INCLUDE_DIR` (the pixi environment has it
at `../seams-core/.pixi/envs/default/include/eigen3`) or pkg-config.

### Release order

1. seams-core tags `vX.Y.Z` on d-SEAMS/seams-core.
2. Here, `seams-core.env` moves to `SEAMS_CORE_REPO=https://github.com/d-SEAMS/seams-core`
   and `SEAMS_CORE_REF=vX.Y.Z`, the workspace version and the `dseams-sys`
   requirement become `X.Y.Z`, `towncrier build --version X.Y.Z` writes the
   changelog, and CI passes on that commit.
3. Tag `vX.Y.Z` here. `.github/workflows/publish.yml` vendors the pinned
   seams-core tag and publishes `dseams-sys`, then `dseams`.

Commits follow Conventional Commits, and each user-visible change adds a
fragment under `changelog.d/`.

## Documentation

- Site: <https://rust.dseams.info/>, the book with the rustdoc
  pages under [`api/`](https://rust.dseams.info/api/seams/index.html).
- docs.rs: [`dseams`](https://docs.rs/dseams) and
  [`dseams-sys`](https://docs.rs/dseams-sys).
- Engine book: [the Rust page](https://docs.dseams.info/stable/rust.html)
  of [docs.dseams.info](https://docs.dseams.info).
- Video: [Rust on ice Ih](https://odysee.com/dseams-rust:687055b1ac9dfe7596006cb4f2fa466de9492ca5).

The book under `docs/` has four parts: getting started, the user guide,
the API reference, and development. `mdbook build docs` renders it, and
`cargo doc --no-deps` writes the API reference. A push to `main` deploys
both to the site.

## License

MIT. The bundled Eigen headers in `dseams-sys/vendor/eigen` are MPL-2.0,
with `AlignedBox.h` under BSD-3-Clause and `BFloat16.h` under Apache-2.0.
