# Getting started

This page takes you from an empty directory to a classified ice cell.

## What you need

- Rust 1.85 or newer.
- A C++20 compiler with OpenMP, such as GCC 11 or newer, on x86_64. The
  `bundled` feature compiles the engine from source, so no separate
  `libseams` install is needed.

The `bundled` copy reads LAMMPS dumps and XYZ files. If you already have a
`libseams` built with more readers (`.con` files or the chemfiles formats),
link it instead. The [link how-to](user-guide/link.md) shows both routes.

## Create a project

```bash
cargo new first-frame
cd first-frame
cargo add dseams --features bundled
```

The first build is the slow one, because `cargo` compiles `libseams` and
its Eigen headers. Later builds reuse that work. The library is named `seams`, so the
code below says `seams::System` even though the package is `dseams`.

## Classify a cell

Replace `src/main.rs` with this program. `diamond8` returns the eight atoms
of one cubic diamond cell and its edge length, which is the oxygen lattice
of cubic ice. `System` holds one frame,
`set_ortho` stores the atoms in a box with zero origin and no tilt, and
`chill_plus` labels each atom:

```rust
use seams::{ChillOptions, Label, System};

fn main() -> Result<(), seams::Error> {
    let (xyz, edge) = seams::diamond8();
    let mut frame = System::new()?;
    frame.set_ortho(&xyz, edge, edge, edge)?;
    let ice = frame.chill_plus(&ChillOptions::default())?;
    for label in [Label::Cubic, Label::Hexagonal, Label::Water] {
        println!(
            "{:<10} {}",
            seams::label_name(label),
            ice.counts[label as usize]
        );
    }
    Ok(())
}
```

Run it with `cargo run`:

```text
cubic      8
hexagonal  0
water      0
```

Every atom is cubic. `ChillOptions::default` uses a 3.5 angstrom cutoff, the
cutoff neighbour graph and the published CHILL+ thresholds.

## How the results are shaped

- `ice.labels` holds one label code per atom, and `ice.counts` holds the
  population of each label. `counts[label as usize]` is the number of atoms
  with that label.
- The nine labels, in count order, are `Cubic`, `Hexagonal`, `Water`,
  `Interfacial`, `Clathrate`, `Interclathrate`, `Unclassified`, `Recubic`
  and `Rehex`.
- Analyses that take several settings take an options struct. Start from
  `Default::default()` and change only the fields you need.
- Every fallible call returns `Result<_, seams::Error>`. The
  [error how-to](user-guide/errors.md) lists what can go wrong.

## Watch it on ice Ih

The recording runs the same calls on a real ice Ih frame and prints the
census that the [ice Ih tutorial](user-guide/ice-ih.md) builds step by step.

<iframe title="Rust on ice Ih" src="https://odysee.com/$/embed/dseams-rust:687055b1ac9dfe7596006cb4f2fa466de9492ca5" width="960" height="540" allowfullscreen></iframe>

## Next

Continue with the [ice Ih tutorial](user-guide/ice-ih.md). It reads a
128-molecule trajectory frame from disk and reports neighbours, rings and
CHILL+ labels.
