# Tutorial: ice Ih

This tutorial reads one frame of ice Ih from a LAMMPS dump and measures it
four ways: neighbour pairs, primitive rings, CHILL+ labels and the local
q6 order parameter. All four agree that the frame is a perfect hexagonal
crystal.

<iframe title="Rust on ice Ih" src="https://odysee.com/$/embed/dseams-rust:687055b1ac9dfe7596006cb4f2fa466de9492ca5" width="960" height="540" allowfullscreen></iframe>

## The dump

Fetch the file into the directory where you run `cargo run`, as described
on the [user guide](index.md) page:

```bash
curl -fsSLO https://raw.githubusercontent.com/d-SEAMS/dseams-rs/v2.14.1/dseams/tests/data/ice1h.lammpstrj
```

It holds one frame of 128 oxygen atoms in a periodic box of about
15.6 by 14.7 by 18.1 angstroms. Every atom has LAMMPS type 1.

## One program, four measurements

`System::read` takes the path, a 1-based frame number and a type filter.
A positive filter keeps only atoms of that type, and a negative one keeps
every atom. Here both choices give the same 128 atoms.

```rust
use seams::{ChillOptions, Label, NeighbourOptions, RingOptions, System};

fn main() -> Result<(), seams::Error> {
    let mut frame = System::new()?;
    frame.read("ice1h.lammpstrj", 1, -1)?;
    println!("atoms {}", frame.count());

    let pairs = frame.neighbours(&NeighbourOptions::default())?;
    println!("neighbour pairs {}", pairs.nnz()?);

    let rings = frame.rings(&RingOptions::default())?;
    println!("six-rings {}", rings.histogram(6)?[6]);

    let ice = frame.chill_plus(&ChillOptions::default())?;
    println!("hexagonal {}", ice.counts[Label::Hexagonal as usize]);

    let order = frame.q4q6(3.5)?;
    let mean_q6 = order.q6.iter().sum::<f64>() / order.q6.len() as f64;
    println!("mean q6 {mean_q6:.6}");
    Ok(())
}
```

```text
atoms 128
neighbour pairs 512
six-rings 256
hexagonal 128
mean q6 0.625855
```

What each line means:

- `neighbour pairs` is the number of directed pairs closer than the 3.5
  angstrom cutoff. Each atom has four neighbours, so 128 atoms give 512
  pairs. Self pairs are not counted.
- `six-rings` is the number of primitive six-membered rings. `histogram(6)`
  returns seven bins, indexed by ring size from 0 to 6, and bin 6 is the
  six-rings. The crystal has two per atom.
- `hexagonal` is the CHILL+ population of `Label::Hexagonal`. All 128 atoms
  carry that label.
- `mean q6` averages the per-atom Steinhardt q6 on the cutoff shell. About
  0.63 is the signature of an ordered tetrahedral crystal, well above the
  value for a liquid.

## Reading the neighbour list

`neighbours` returns a `Neighbours` handle. `degrees` gives the neighbour
count of every atom, and `pairs` iterates the directed pairs as
`NeighbourPair { atom, neighbour }`.

```rust
use seams::{NeighbourOptions, System};

fn main() -> Result<(), seams::Error> {
    let mut frame = System::new()?;
    frame.read("ice1h.lammpstrj", 1, -1)?;
    let list = frame.neighbours(&NeighbourOptions::default())?;

    let degrees = list.degrees()?;
    println!(
        "degrees {}..{}",
        degrees.iter().min().unwrap(),
        degrees.iter().max().unwrap()
    );
    for pair in list.pairs().take(3) {
        println!("atom {} has neighbour {}", pair.atom, pair.neighbour);
    }
    Ok(())
}
```

```text
degrees 4..4
atom 0 has neighbour 4
atom 0 has neighbour 9
atom 0 has neighbour 11
```

Atom indices start at 0 and follow the order of the file.

## The census every language prints

Every d-SEAMS language binding prints one summary line for this file:
the pair count, the ring histogram for sizes 0 to 6, and the nine CHILL+
populations. In Rust it is:

```rust
use seams::{ChillOptions, NeighbourOptions, RingOptions, System};

fn main() -> Result<(), seams::Error> {
    let mut frame = System::new()?;
    frame.read("ice1h.lammpstrj", 1, -1)?;
    let pairs = frame.neighbours(&NeighbourOptions::default())?.nnz()?;
    let rings = frame
        .rings(&RingOptions {
            max_size: 6,
            ..RingOptions::default()
        })?
        .histogram(6)?;
    let chill = frame.chill_plus(&ChillOptions::default())?;

    let join = |values: &[i32]| {
        values
            .iter()
            .map(i32::to_string)
            .collect::<Vec<_>>()
            .join(" ")
    };
    println!(
        "pairs {pairs} rings {} chill {}",
        join(&rings),
        join(&chill.counts)
    );
    Ok(())
}
```

```text
pairs 512 rings 0 0 0 0 0 0 256 chill 0 128 0 0 0 0 0 0 0
```

If a port of your own code prints a different line for this file, one of
the two has a bug. The nine CHILL+ populations are in label order: cubic,
hexagonal, water, interfacial, clathrate, interfacial clathrate,
unclassified, reclassified cubic and reclassified hexagonal.

## Where next

- [Bulk ice](bulk-ice.md) runs the same CHILL+ call on cubic ice and on a clathrate.
- [Rings](rings.md) goes further into the ring set and its atoms.
- The engine tutorial on [primitive rings](https://docs.dseams.info/tutorials/rings.html) covers this cell and a mixed TIP4P frame.
