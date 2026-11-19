# Tutorial: an ice-water interface

At an ice-water interface, CHILL+ should find crystal on one side, liquid on
the other and a thin band of `Interfacial` ice between them. This tutorial
builds a small slab in code, labels it, and counts the labels layer by
layer along z. The same loop works on a frame you read from a simulation.

<iframe title="CHILL+ on the basal interface" src="https://odysee.com/$/embed/dseams-interface:74af20635ceeef7945f8e22cb5b02522a865baa6" width="960" height="540" allowfullscreen></iframe>

The recording shows CHILL+ on a basal-plane interface from a simulation.
The frame here is a stand-in, so that the program needs no data files.

## The slab

`slab` stacks eight layers of the diamond cell, each layer being one cell
high with 3 by 3 cells across. The lower four layers stay on their lattice
sites. In the upper four every coordinate is moved by up to one angstrom
in either direction, using a small fixed-seed generator so the result is
the same on every run. The displaced atoms have no tetrahedral order left,
which makes them a crude liquid. This is a test pattern for the analysis,
not a simulation of melting.

```rust
use seams::{ChillOptions, Label, System};

const LAYERS: usize = 8;
const SOLID: usize = 4;

fn slab(layers: usize, solid: usize) -> (Vec<f64>, [f64; 3]) {
    let (cell, edge) = seams::diamond8();
    let size = [3.0 * edge, 3.0 * edge, layers as f64 * edge];
    let mut state = 12345u64;
    let mut xyz = Vec::new();
    for iz in 0..layers {
        for iy in 0..3 {
            for ix in 0..3 {
                for site in cell.chunks(3) {
                    let shift = [ix as f64 * edge, iy as f64 * edge, iz as f64 * edge];
                    for axis in 0..3 {
                        let mut x = site[axis] + shift[axis];
                        if iz >= solid {
                            state = state
                                .wrapping_mul(6364136223846793005)
                                .wrapping_add(1442695040888963407);
                            x += ((state >> 11) as f64 / (1u64 << 53) as f64 - 0.5) * 2.0;
                        }
                        xyz.push(x.rem_euclid(size[axis]));
                    }
                }
            }
        }
    }
    (xyz, size)
}

fn is_ice(code: i32) -> bool {
    [Label::Cubic, Label::Hexagonal, Label::Recubic, Label::Rehex]
        .iter()
        .any(|label| *label as i32 == code)
}

fn main() -> Result<(), seams::Error> {
    let (xyz, size) = slab(LAYERS, SOLID);
    let mut frame = System::new()?;
    frame.set_ortho(&xyz, size[0], size[1], size[2])?;
    let labels = frame.chill_plus(&ChillOptions::default())?.labels;

    let height = size[2] / LAYERS as f64;
    let mut table = [[0usize; 3]; LAYERS];
    for (atom, &code) in labels.iter().enumerate() {
        let layer = ((xyz[3 * atom + 2] / height) as usize).min(LAYERS - 1);
        let column = if is_ice(code) {
            0
        } else if code == Label::Interfacial as i32 {
            1
        } else {
            2
        };
        table[layer][column] += 1;
    }

    println!("layer   ice  interfacial  other");
    for (layer, row) in table.iter().enumerate() {
        println!("{layer:>5} {:>5} {:>12} {:>6}", row[0], row[1], row[2]);
    }
    Ok(())
}
```

```text
layer   ice  interfacial  other
    0    54            5     13
    1    72            0      0
    2    72            0      0
    3    55            9     14
    4     0            1     75
    5     0            0     71
    6     0            2     68
    7     0            2     63
```

Layers 0 to 3 hold the crystal and layers 4 to 7 hold no ice at all. The
two middle crystal layers, 1 and 2, are all ice. The two layers that touch
the liquid are not. Layer 3 faces the displaced layers above it, and layer
0 faces layer 7 across the periodic boundary of the box, so the slab has
two interfaces. Both layers lose about a quarter of their atoms to
`interfacial` or to other labels, because atoms at the edge of a crystal
keep only some of their tetrahedral neighbours.

## What the call returns

`chill_plus` returns a `Classification`:

- `labels` has one `Label` code per atom, in the order the atoms were
  stored.
- `counts` has the nine populations, indexed by `Label`.

`label_name` gives the short text for a code, such as `"interfacial"`.
`ChillOptions` holds the cutoff (3.5 angstroms by default), a `species`
filter where `0` keeps every atom, the neighbour `Graph` and the
`ChillRule`. Published edges are inclusive and OVITO edges are open.
`chill` is the original CHILL classifier, with the same result shape and no
clathrate classes.

## Tilted cells

`set_ortho` stores a box with no tilt. For a triclinic cell use
`set_frame` or `set_atoms` with a nine-number box: the origin `ox, oy, oz`,
the edge lengths `lx, ly, lz`, then the tilts `xy, xz, yz`. The
[read how-to](read.md) shows the calls.

The basal frame from the recording, the layer command and the recorded
stack are in the engine tutorial
[Ice-water interface](https://docs.dseams.info/tutorials/interface.html).
