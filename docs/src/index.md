# dseams

`dseams` is the Rust interface to [d-SEAMS](https://dseams.info), a toolkit
that classifies the molecules of a simulation frame. It labels ice and
clathrate with CHILL and CHILL+, computes Steinhardt order parameters,
finds primitive rings and cages, and measures planar ice fronts in brine.
The engine itself is written in C++ and lives in
[seams-core](https://github.com/d-SEAMS/seams-core). It is reached through
its C API, `libseams`.

Two crates make up the Rust side:

| Crate | Library name | Use it for |
| --- | --- | --- |
| `dseams` | `seams` | Analysing frames. Owned handles, options structs, iterators and `Result` errors. |
| `dseams-sys` | `seams_sys` | The raw C declarations. Most programs never name it. |

The crates.io name `seams` belongs to an unrelated project, so the packages
are `dseams` and `dseams-sys`. Code still says `use seams::System`.

## A first result

Add the crate with a bundled copy of the engine, then classify a cubic
ice cell:

```bash
cargo add dseams --features bundled
```

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
LAMMPS order: the origin, the three edge lengths, then the tilts `xy`,
`xz` and `yz`.

## Where to go next

| If you want to | Read |
| --- | --- |
| Install the crate and run your own first program | [Getting started](getting-started.md) |
| Learn the calls by working through real frames | [The tutorials](user-guide/index.md), starting with [ice Ih](user-guide/ice-ih.md) |
| Link an existing `libseams` instead of the bundled copy | [Link libseams](user-guide/link.md) |
| Load a trajectory from disk | [Read a trajectory](user-guide/read.md) |
| Look up a type or a method | [API reference](api.md) |
| Build the crates from a checkout and run their tests | [Building from source](development.md) |

The engine book, [docs.dseams.info](https://docs.dseams.info), covers the
command-line tool, the C API and the science behind each analysis. Its
[Rust page](https://docs.dseams.info/stable/rust.html) points back here.

## Citing d-SEAMS

If you use d-SEAMS in published work, cite the 2020 article: R. Goswami,
A. Goswami and J. K. Singh, "d-SEAMS: Deferred Structural Elucidation
Analysis for Molecular Simulations", *Journal of Chemical Information and
Modeling* 60 (4), 2169-2177,
[doi:10.1021/acs.jcim.0c00031](https://doi.org/10.1021/acs.jcim.0c00031).
