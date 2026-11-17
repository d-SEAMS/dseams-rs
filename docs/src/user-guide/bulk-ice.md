# Tutorial: bulk ice

Classify two bulk crystals that ship with the crate. CHILL+ labels the
cubic diamond cubic, and the sI cell clathrate. The mixed TIP4P dump used
by the engine tutorial is not in this repository.

The recordings of the cage search and of primitive rings are on the
[cages](cages.md) and [rings](rings.md) tutorials. The mixed TIP4P
walkthrough is
[Classify ice on the mixed TIP4P example](https://docs.dseams.info/tutorials/bulk-ice.html).

## Cubic diamond

`diamond8` is one conventional cell, eight atoms, edge equal to the
lattice constant. `chill_plus` with the default options labels every atom
`Label::Cubic` (count index 0):

```rust
fn main() -> Result<(), seams::Error> {
    let (xyz, edge) = seams::diamond8();
    let mut system = seams::System::new()?;
    system.set_ortho(&xyz, edge, edge, edge)?;
    let ice = system.chill_plus(&seams::ChillOptions::default())?;
    assert_eq!(ice.counts[seams::Label::Cubic as usize], 8);
    Ok(())
}
```

`dseams/examples/ice.rs` repeats that cell on a 2 by 2 by 2 grid, 64
atoms, and stores them with `set_ortho`. The integration test
`dseams/tests/ice.rs` requires every CHILL+ label to be cubic, both for
the published table on the cutoff graph and for the OVITO table on the
mutual four-neighbour graph. It also requires a mean q6 above 0.3, four
neighbours inside 3.5 angstroms for every atom, and a primitive six-ring
fraction above one half.

```bash
cargo run --example ice
```

Against libseams 2.14.0 the example prints:

```text
dseams 2.14.0 cubic 64 of 64
```

## sI clathrate

`dseams/tests/data/genice_sI.lammpstrj` is the oxygen lattice of one GenIce
sI cell, 46 atoms. `cargo run --example minimal` reads it (or the dump
path given on the command line), calls `set_ortho`, and checks:

- `count` is 46
- `chill_plus` with the default options puts all 46 atoms in
  `Label::Clathrate` (count index 4)
- `six_ring_fraction(3.5)` reports 54 primitive six-rings
- the mean of `q4q6(3.5).q6` is above 0.5

Against libseams 2.14.0 the example prints:

```text
rust example ok 2.14.0 q6 0.595
```

The example parses the dump and calls `set_ortho`. `System::read` of the
same path, frame 1, type 1, is the LAMMPS reader; every atom in the file
is type 1.

## What the two labels mean

CHILL+ looks at the four neighbours of each atom and marks each bond
staggered or eclipsed. Four staggered bonds are cubic. Four eclipsed
bonds are clathrate. The sI oxygens are clathrate on that score. Cage
membership, in the next tutorial, asks a different question: whether the
atom sits in a finished hexagonal cage or a finished double-diamond cage.
