# Tutorial: rings

A primitive ring is a closed loop of bonded atoms that cannot be split into
two smaller loops. Ring statistics are a direct fingerprint of a structure:
ice Ih and cubic ice have only six-membered rings, while a clathrate adds
five-membered rings. This tutorial counts them on ice Ih and on the sI
clathrate framework, then reads the atoms of individual rings.

<iframe title="Primitive rings on the mixed frame, then on ice Ih" src="https://odysee.com/$/embed/dseams-rings:cfb3b6687dd81847ecb005782df8cf5143617be5" width="960" height="540" allowfullscreen></iframe>

You need the two dumps from the [user guide](index.md) page.

## The histogram

`RingOptions::default` uses a 3.5 angstrom cutoff, the cutoff graph and a
`max_size` of 6, the largest ring the search keeps. `max_size` may be set
from 3 to 12. `Rings::histogram(n)` returns `n + 1` bins indexed by ring
size, so `histogram(6)` has seven entries and bin 6 counts six-rings.

```rust
use seams::{RingOptions, System};

fn main() -> Result<(), seams::Error> {
    for path in ["ice1h.lammpstrj", "genice_sI.lammpstrj"] {
        let mut frame = System::new()?;
        frame.read(path, 1, -1)?;
        let rings = frame.rings(&RingOptions::default())?;
        let histogram = rings.histogram(6)?;
        println!(
            "{path}: {} rings, five {} six {}",
            rings.size(),
            histogram[5],
            histogram[6]
        );
    }
    Ok(())
}
```

```text
ice1h.lammpstrj: 256 rings, five 0 six 256
genice_sI.lammpstrj: 102 rings, five 48 six 54
```

Ice Ih has 256 rings and all of them are hexagons. The clathrate framework
has 48 pentagons and 54 hexagons, which is its cage faces counted once
each.

`Rings::size` is the number of rings kept, and `Rings::fraction(n)` is the
fraction of atoms that sit on at least one ring of size `n`.
`System::six_ring_fraction` is a shortcut for the six-ring count and that
fraction in one call.

## The atoms of a ring

`Rings::vertices(i)` returns the atom indices of ring `i`. `Rings::iter`
walks every ring and yields each as a `Result<Vec<i32>, Error>`.

```rust
use seams::{RingOptions, System};

fn main() -> Result<(), seams::Error> {
    let mut frame = System::new()?;
    frame.read("ice1h.lammpstrj", 1, -1)?;
    let rings = frame.rings(&RingOptions::default())?;

    println!("ring 0 atoms {:?}", rings.vertices(0)?);
    println!("fraction of atoms on a six-ring {}", rings.fraction(6)?);

    let mut sizes = std::collections::BTreeMap::new();
    for ring in rings.iter() {
        *sizes.entry(ring?.len()).or_insert(0) += 1;
    }
    println!("{sizes:?}");
    Ok(())
}
```

```text
ring 0 atoms [0, 4, 7, 3, 5, 9]
fraction of atoms on a six-ring 1
{6: 256}
```

Every atom of the crystal sits on six-rings, so the fraction is 1.

## The six-ring shortcut

Counting hexagons is common enough to have its own call.
`System::six_ring_fraction` takes a cutoff and returns the number of
six-rings with the fraction of atoms on them, without building a `Rings`
handle:

```rust
use seams::System;

fn main() -> Result<(), seams::Error> {
    let mut frame = System::new()?;
    frame.read("genice_sI.lammpstrj", 1, -1)?;
    let (six_rings, fraction) = frame.six_ring_fraction(3.5)?;
    println!(
        "{six_rings} six-rings on {:.0}% of the atoms",
        100.0 * fraction
    );
    Ok(())
}
```

```text
54 six-rings on 100% of the atoms
```

In the clathrate framework every atom still sits on at least one
six-ring, even though 48 pentagons are present too.

For the same count on a mixed TIP4P frame, see the engine tutorial
[Primitive rings](https://docs.dseams.info/tutorials/rings.html).
