# dseams-rs

Rust interface to [d-SEAMS](https://dseams.info). It exposes CHILL and
CHILL+ labels, Steinhardt order, neighbour lists, rings, cages, RDF and
coordination, hydrogen bonds, density, fingerprints, contacts, domains,
prisms, monolayer statistics, symmetry and planar brine-front analysis.
It reads LAMMPS and XYZ, plus CON and chemfiles formats when available.

The C++ engine and its C API (`libseams`, header `seams.h`) live in
[seams-core](https://github.com/d-SEAMS/seams-core). This repository holds
the two crates on top of it:

| Crate | Library name | What it is |
|---|---|---|
| [`dseams`](dseams) | `seams` | Safe handles, options structs, iterators and `Result` errors |
| [`dseams-sys`](dseams-sys) | `seams_sys` | Raw FFI declarations, generated from `seams.h` |

The crates.io name `seams` belongs to an unrelated project, hence the `d`.
Code says `use seams::System`.

## Install

```bash
cargo add dseams --features bundled
```

The `bundled` feature compiles the engine from source, so nothing else needs
installing. It needs Rust 1.85 or newer and a C++20 compiler with OpenMP on
x86_64. It reads LAMMPS dumps and XYZ files, and uses installed chemfiles
and readcon-core libraries when pkg-config finds them.

## A first result

```rust
use seams::{ChillOptions, Label, System};

fn main() -> Result<(), seams::Error> {
    let (xyz, edge) = seams::diamond8();
    let mut frame = System::new()?;
    frame.set_ortho(&xyz, edge, edge, edge)?;
    let ice = frame.chill_plus(&ChillOptions::default())?;
    println!("cubic atoms: {}", ice.counts[Label::Cubic as usize]);
    Ok(())
}
```

```text
cubic atoms: 8
```

Coordinates and cutoffs are in angstroms. A cell is nine numbers in the
LAMMPS order: origin, edge lengths, then the tilts `xy`, `xz` and `yz`.

## Linking libseams

`dseams-sys` does not run bindgen, because the declarations are checked in.
Its build script uses the first of these that applies:

1. **`SEAMS_LIBDIR`**: the directory that holds the shared `libseams`: the
   `src` directory of a meson build tree, or the library directory of an
   install prefix. `SEAMS_INCLUDE`, a path list, optionally names the
   header directories.
2. **Feature `bundled`**: compile the C API and Eigen 3.4.0 from the
   engine sources that ship in the package, with the `cc` crate. It needs
   x86_64 and C++20 with OpenMP. Chemfiles 0.10 and readcon-core 0.16 are
   enabled when pkg-config finds them.
3. **pkg-config**: module `seams`, at least 2.14.0 and below 3.0.0.

Programs linked to a shared library need its directory on
`LD_LIBRARY_PATH` at run time. The [link how-to](https://rust.dseams.info/user-guide/link.html)
has the commands for each route, including building `libseams` from
seams-core.

## Documentation

- [The book](https://rust.dseams.info/): getting started, seven tutorials
  on real frames, how-to pages, and the API reference.
- [docs.rs/dseams](https://docs.rs/dseams) and
  [docs.rs/dseams-sys](https://docs.rs/dseams-sys): the API reference for
  each release.
- [The engine book](https://docs.dseams.info), with its
  [Rust page](https://docs.dseams.info/stable/rust.html).
- [Rust on ice Ih](https://odysee.com/dseams-rust:687055b1ac9dfe7596006cb4f2fa466de9492ca5),
  a video of the ice Ih census.

The [examples](dseams/examples) are runnable programs: `ice` (a cubic ice
crystal), `minimal` (the sI clathrate framework), `ice_ih` (the ice Ih
census) and `lang_tasks` (the census that every d-SEAMS language binding
prints).

## Building from source and contributing

[Building from source](https://rust.dseams.info/development.html) covers
cloning this repository, running the tests and examples, and building the
documentation. Conventions for changes are in [AGENTS.md](AGENTS.md).

## Citing

If you use d-SEAMS in published work, cite R. Goswami, A. Goswami and
J. K. Singh, "d-SEAMS: Deferred Structural Elucidation Analysis for
Molecular Simulations", *Journal of Chemical Information and Modeling* 60
(4), 2169-2177, [doi:10.1021/acs.jcim.0c00031](https://doi.org/10.1021/acs.jcim.0c00031).

## Other language bindings

- [PydSEAMSlib](https://github.com/d-SEAMS/PydSEAMSlib): Python.
- [Dseams.jl](https://github.com/d-SEAMS/Dseams.jl): Julia.
- [dseams-r](https://github.com/d-SEAMS/dseams-r): R.
- [dseams-fortran](https://github.com/d-SEAMS/dseams-fortran): Fortran.
- [yodaStruct](https://github.com/d-SEAMS/yodaStruct): Lua.

## License

MIT. The bundled Eigen headers in `dseams-sys/vendor/eigen` are MPL-2.0,
with `AlignedBox.h` under BSD-3-Clause and `BFloat16.h` under Apache-2.0.
