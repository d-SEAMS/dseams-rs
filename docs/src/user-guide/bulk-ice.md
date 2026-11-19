# Tutorial: bulk ice

CHILL+ looks at the four neighbours of each molecule and asks whether the
bonds to the next shell are staggered or eclipsed. Four staggered bonds
make cubic ice, one eclipsed bond among four makes hexagonal ice, and four
eclipsed bonds make a clathrate. This tutorial runs CHILL+ on three
crystals that differ only in that pattern: cubic ice, hexagonal ice and the
sI clathrate framework.

You need the two dumps from the [user guide](index.md) page for the last
two sections. The cubic crystal is built in code.

## Cubic ice

`diamond8` is one conventional diamond cell of eight oxygen atoms with an
edge of about 6.35 angstroms. That is smaller than twice the cutoff, so
this program tiles it two times along each axis to get a 64-atom crystal in
a cell of about 12.7 angstroms. It then compares CHILL, the original
classifier, with CHILL+.

```rust
use seams::{ChillOptions, Label, System};

fn main() -> Result<(), seams::Error> {
    let (cell, edge) = seams::diamond8();
    let mut xyz = Vec::new();
    for iz in 0..2 {
        for iy in 0..2 {
            for ix in 0..2 {
                for site in cell.chunks(3) {
                    xyz.extend([
                        site[0] + ix as f64 * edge,
                        site[1] + iy as f64 * edge,
                        site[2] + iz as f64 * edge,
                    ]);
                }
            }
        }
    }
    let side = 2.0 * edge;

    let mut crystal = System::new()?;
    crystal.set_ortho(&xyz, side, side, side)?;
    let options = ChillOptions::default();
    let chill = crystal.chill(&options)?;
    let plus = crystal.chill_plus(&options)?;
    let cubic = Label::Cubic as usize;
    println!("atoms {}", crystal.count());
    println!("CHILL  cubic {}", chill.counts[cubic]);
    println!("CHILL+ cubic {}", plus.counts[cubic]);
    Ok(())
}
```

```text
atoms 64
CHILL  cubic 64
CHILL+ cubic 64
```

`chill` and `chill_plus` return the same `Classification`: `labels`, one
code per atom, and `counts`, nine populations indexed by `Label`. The two
classifiers agree on a perfect crystal. They differ on molecules that sit
between phases, and CHILL+ adds the clathrate classes.

## Hexagonal ice

The ice Ih dump is hexagonal ice. Each molecule has three staggered bonds
and one eclipsed bond, which is the hexagonal signature.

```rust
use seams::{ChillOptions, Label, System};

fn main() -> Result<(), seams::Error> {
    let mut crystal = System::new()?;
    crystal.read("ice1h.lammpstrj", 1, -1)?;
    let plus = crystal.chill_plus(&ChillOptions::default())?;
    println!("atoms {}", crystal.count());
    println!("hexagonal {}", plus.counts[Label::Hexagonal as usize]);
    Ok(())
}
```

```text
atoms 128
hexagonal 128
```

## sI clathrate

The sI file holds the 46 oxygen atoms that form the hydrogen-bonded
framework of one clathrate cell, with no guest molecules. CHILL+ with the
published table calls every one of them a clathrate atom. Original CHILL
has no clathrate class, so it sees something else:

```rust
use seams::{ChillOptions, Label, System};

fn main() -> Result<(), seams::Error> {
    let mut framework = System::new()?;
    framework.read("genice_sI.lammpstrj", 1, -1)?;
    let options = ChillOptions::default();
    let chill = framework.chill(&options)?;
    let plus = framework.chill_plus(&options)?;
    println!("atoms {}", framework.count());
    println!(
        "CHILL  {} {}",
        seams::label_name(Label::Water),
        chill.counts[Label::Water as usize]
    );
    println!(
        "CHILL+ {} {}",
        seams::label_name(Label::Clathrate),
        plus.counts[Label::Clathrate as usize]
    );

    let order = framework.q4q6(3.5)?;
    let mean_q6 = order.q6.iter().sum::<f64>() / order.q6.len() as f64;
    println!("mean q6 {mean_q6:.3}");
    Ok(())
}
```

```text
atoms 46
CHILL  water 46
CHILL+ clathrate 46
mean q6 0.595
```

Original CHILL labels the whole framework as liquid water, because none of
its crystal patterns match. This is why CHILL+ is the right default for
anything that may contain hydrates. The mean q6 of 0.595 is high, like
ice, so q6 alone cannot separate the two crystals. The CHILL+ label can.

## Ih or Ic, atom by atom

CHILL+ calls both crystals ice, with different labels. `System::symmetry`
goes further and compares each molecule's whole neighbour shell with the
ideal hexagonal and cubic shells. It returns one code per atom: 0 for ice
Ih, 1 for ice Ic, 2 for stacking disorder and -1 when the shell matches
none of them. A non-positive RMSD limit selects the library's own ceiling.

```rust
use seams::System;

fn tally(codes: &[i32]) -> Vec<(i32, usize)> {
    let mut counts = std::collections::BTreeMap::new();
    for code in codes {
        *counts.entry(*code).or_insert(0) += 1;
    }
    counts.into_iter().collect()
}

fn main() -> Result<(), seams::Error> {
    let mut hexagonal = System::new()?;
    hexagonal.read("ice1h.lammpstrj", 1, -1)?;
    println!("ice1h:      {:?}", tally(&hexagonal.symmetry(0.0)?));

    let mut clathrate = System::new()?;
    clathrate.read("genice_sI.lammpstrj", 1, -1)?;
    println!("genice_sI:  {:?}", tally(&clathrate.symmetry(0.0)?));
    Ok(())
}
```

```text
ice1h:      [(0, 128)]
genice_sI:  [(-1, 46)]
```

All 128 atoms of the Ih dump are ice Ih, and none of the clathrate atoms
match either ice.

## Choosing the options

`ChillOptions` has four fields:

| Field | Default | Meaning |
| --- | --- | --- |
| `cutoff` | `3.5` | Neighbour distance in angstroms |
| `species` | `0` | Atom type to analyse, or `0` for every atom |
| `graph` | `Graph::Cutoff` | How neighbours are chosen: `Cutoff`, `Mutual` or `Seeded` |
| `rule` | `ChillRule::Published` | The threshold table: `Published` or `Ovito` |

Set `species` when a file mixes oxygen with ions or guests. The
[brine tutorial](brine.md) does that.

The next tutorial, [cages](cages.md), asks a different question of the
same two crystals: whether each atom sits in a finished cage.
