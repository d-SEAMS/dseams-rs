# Tutorial: cages

CHILL+ labels an atom by its local bonds. The cage analysis asks about
larger structure: is the atom part of a finished hexagonal cage (the unit of
ice Ih), a finished double-diamond cage (the unit of cubic ice), both, or
neither? A second call, the signature search, counts closed polyhedra by
the sizes of their faces, which is how clathrate cages such as the
pentagonal dodecahedron are found.

<iframe title="Ice Ih hexagonal cages, cubic double-diamond cages, then the clathrate cells" src="https://odysee.com/$/embed/dseams-cages:1c258cea9384acd2e21eeec509c5eedc050d08db" width="960" height="540" allowfullscreen></iframe>

You need the two dumps from the [user guide](index.md) page.

## Cage membership

`System::cages` assigns every atom to one of four disjoint classes.
`CageOptions::default` uses a 3.5 angstrom cutoff, the seeded neighbour
graph (mutual four-nearest-neighbour seeds plus union completions) and
`k` of 4. `Cages::counts` returns the population of each class and
`Cages::labels` returns one `CageLabel` code per atom.

```rust
use seams::{CageOptions, System};

fn main() -> Result<(), seams::Error> {
    for path in ["ice1h.lammpstrj", "genice_sI.lammpstrj"] {
        let mut frame = System::new()?;
        frame.read(path, 1, -1)?;
        let cages = frame.cages(&CageOptions::default())?;
        let counts = cages.counts()?;
        println!(
            "{path}: hexagonal {} cubic {} water {} both {}",
            counts.hexagonal, counts.cubic, counts.water, counts.both
        );
    }
    Ok(())
}
```

```text
ice1h.lammpstrj: hexagonal 128 cubic 0 water 0 both 0
genice_sI.lammpstrj: hexagonal 0 cubic 0 water 46 both 0
```

All 128 atoms of ice Ih belong to hexagonal cages. The clathrate framework
has no hexagonal or double-diamond cage, so its atoms fall in the
remaining class, `water`. That class means "in no ice cage", not liquid
water. `CageLabel` spells the four codes: `Water` (0), `Hex` (1), `Cubic`
(2) and `Both` (3).

Cubic ice shows up as `cubic` membership. It needs a cell wide enough
that no pair of atoms can meet through two periodic images, which means an
edge of at least twice the cutoff. The 8-atom `diamond8` cell is too small,
so this program tiles it twice along each axis to get 64 atoms:

```rust
use seams::{CageOptions, System};

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

    let mut frame = System::new()?;
    frame.set_ortho(&xyz, side, side, side)?;
    let counts = frame.cages(&CageOptions::default())?.counts()?;
    println!("hexagonal {} cubic {}", counts.hexagonal, counts.cubic);
    Ok(())
}
```

```text
hexagonal 0 cubic 64
```

## Counting cages by signature

`System::signature_cages` counts closed cages whose faces match a
signature. The text `512` means twelve pentagons, `5^12`, and `51262` means
twelve pentagons and two hexagons, `5^12 6^2`. These are the two cage
types of sI. The result is a `SignatureMatch` with the number of cages and
the number of atoms they cover.

```rust
use seams::{SignatureOptions, System};

fn main() -> Result<(), seams::Error> {
    let mut frame = System::new()?;
    frame.read("genice_sI.lammpstrj", 1, -1)?;
    for spec in ["512", "51262"] {
        let found = frame.signature_cages(&SignatureOptions {
            spec: spec.to_string(),
            ..SignatureOptions::default()
        })?;
        println!("{spec}: {} cages, {} atoms", found.cages, found.atoms);
    }
    Ok(())
}
```

```text
512: 2 cages, 40 atoms
51262: 6 cages, 46 atoms
```

One sI cell holds two small cages and six large ones. The six large cages
cover all 46 framework atoms, and the two small cages cover 40 of them.
`SignatureOptions.graph` selects the neighbour graph. It defaults to
`Graph::Cutoff`.

The signature search is stricter about the cell than the membership call.
On a cell thinner than twice the cutoff it returns `Status::Argument`
instead of a count, and a signature that is not a valid ring census gets
the same status with a message that names the text.

For the same search with the `seams` command, see the engine how-to
[Cage search](https://docs.dseams.info/howto/cages-trace.html).
