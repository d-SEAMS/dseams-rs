# Getting started

This page installs `dseams` 2.14.0, points the build at `libseams`, and
classifies one cubic cell. The recording is the Rust front on ice Ih.

<iframe title="Rust on ice Ih" src="https://odysee.com/$/embed/dseams-rust:687055b1ac9dfe7596006cb4f2fa466de9492ca5" width="960" height="540" allowfullscreen></iframe>

Rust on ice Ih.

## Add the crate

Rust 1.85 or newer builds the crates.

```toml
[dependencies]
dseams = "2.14.0"
```

`cargo add dseams` writes the same line. The library name is `seams`.

## Link libseams

`dseams-sys` does not run bindgen. The declarations are already in the
crate. The build script takes the first match:

1. `SEAMS_LIBDIR` (or `SEAMS_LIB_DIR`): the directory that holds the shared
   `libseams`. A meson build uses `bbdir/src`. An install prefix uses
   `lib`. Set `SEAMS_INCLUDE` to the header directories when
   `seams.h` is not in the sibling `include` directory. For the meson tree
   that this repository's CI builds, that is the seams-core `include`
   directory plus `bbdir/src`.
2. Feature `bundled`: compile the C API and Eigen 3.4.0 with the `cc`
   crate. This needs x86_64 and a C++20 compiler with OpenMP. The shell
   classifier uses AVX2. The bundled copy reads LAMMPS dumps and XYZ.
   `.con` files and the chemfiles formats need a `libseams` that was
   built with those readers. Fill `dseams-sys/vendor/` with
   `python3 dseams-sys/vendor.py`, or set `SEAMS_SOURCE_DIR` to a
   seams-core checkout at the commit in `seams-core.env`.
   `SEAMS_LIBDIR` still wins when it is set.
3. pkg-config module `seams`, at least 2.14.0 and below 3.0.0. A
   `seams_version.h` from another major release, or from an older minor
   release, stops the build.

The [link how-to](user-guide/link.md) has the commands for each path.

Tests and examples in this workspace receive an rpath to `SEAMS_LIBDIR`.
A binary in another crate needs that directory on `LD_LIBRARY_PATH` at
run time. The bundled build links a static library, so it has no rpath.

## Classify the eight-atom cell

`diamond8` returns the eight-atom cubic diamond and its lattice constant,
`2.75 * 4 / sqrt(3)` angstroms. The nearest-neighbour distance is 2.75
angstroms. `ChillOptions::default` uses a 3.5 angstrom cutoff, the cutoff
graph, and the published CHILL+ table. Every atom is cubic:

```rust
fn main() -> Result<(), seams::Error> {
    let (xyz, edge) = seams::diamond8();
    seams::set_num_threads(1)?;
    let mut system = seams::System::new()?;
    system.set_ortho(&xyz, edge, edge, edge)?;
    let ice = system.chill_plus(&seams::ChillOptions::default())?;
    assert_eq!(ice.labels.len(), 8);
    assert_eq!(ice.counts[seams::Label::Cubic as usize], 8);
    Ok(())
}
```

`set_num_threads` is process-global. `1` makes the following call
single-threaded. `ice.counts[label as usize]` is the population of that
label. The nine labels, in count order, are `Cubic`, `Hexagonal`,
`Water`, `Interfacial`, `Clathrate`, `Interclathrate`, `Unclassified`,
`Recubic`, and `Rehex`.

From a checkout of this repository, with `SEAMS_LIBDIR` set:

```bash
cargo run --example ice_ih
cargo test --doc -- --test-threads=1
```

`ice_ih` reads the ice Ih dump shipped in the crate and prints

```text
rust ice nop 128 q6 0.625855 hexagonal 128 rings 256
```

That line is locked by the example's test. The [ice Ih tutorial](user-guide/ice-ih.md) walks through it.
The engine book is [docs.dseams.info](https://docs.dseams.info).
