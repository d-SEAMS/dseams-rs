# dseams

Safe Rust calls into [d-SEAMS](https://dseams.info): CHILL and CHILL+
ice labels, Steinhardt order parameters, primitive rings, cages, radial
distribution functions, hydrogen bonds, topological fingerprints and
planar brine fronts for molecular simulation frames.

The crates.io name `seams` belongs to an unrelated project, so the
package is `dseams`. The library is still called `seams`.

## Install

```bash
cargo add dseams --features bundled
```

The `bundled` feature compiles the d-SEAMS engine from source, so no
separate install is needed. It needs Rust 1.85 or newer and a C++20
compiler with OpenMP on x86_64, and it reads LAMMPS dumps and XYZ files.
To link a `libseams` you built instead, leave the feature off and set
`SEAMS_LIBDIR`, or put a `seams.pc` file on `PKG_CONFIG_PATH`. The
[link how-to](https://rust.dseams.info/user-guide/link.html) has the
commands.

## Example

Coordinates and cutoffs are in angstroms. This program classifies the
eight-atom cubic ice cell that `diamond8` returns:

```rust
fn main() -> Result<(), seams::Error> {
    let (xyz, edge) = seams::diamond8();
    let mut frame = seams::System::new()?;
    frame.set_ortho(&xyz, edge, edge, edge)?;
    let ice = frame.chill_plus(&seams::ChillOptions::default())?;
    println!("cubic atoms: {}", ice.counts[seams::Label::Cubic as usize]);
    Ok(())
}
```

```text
cubic atoms: 8
```

A `System` holds one frame, filled by `set_ortho`, `set_frame`,
`set_atoms` or `read`. Analyses are methods on it. Those with several
settings take an options struct with a `Default`. Calls that can fail
return `Result<_, seams::Error>`, and handles free their native object when
dropped.

## Documentation

- [The book](https://rust.dseams.info/) has a getting-started page, seven
  tutorials on real frames and how-to pages.
- [The API reference](https://docs.rs/dseams) describes every type and
  function.
- [The engine book](https://docs.dseams.info) covers the science behind each
  analysis.

Licensed under MIT.
