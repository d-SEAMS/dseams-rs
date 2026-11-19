# Tutorial: brine

When salt water freezes, the growing ice rejects the ions. The brine
analysis measures that on a planar front. Given which atoms are ice, it
finds where the ice starts and stops along one axis, the ion content of the
ice and the liquid, and the pockets of liquid trapped inside the crystal.

<iframe title="The brine front" src="https://odysee.com/$/embed/dseams-brine:124a3a7fa52cdf7aff34ac00cfba6068e240a947" width="960" height="540" allowfullscreen></iframe>

The recording shows the NaCl front from a simulation. This page builds a
slab with the same layout, so the program needs no data files.

## The input

`System::brine` takes one integer per atom, nonzero when that atom is ice,
and a `BrineOptions`:

| Field | Meaning |
| --- | --- |
| `water_type` | The atom type of water, or `0` for any |
| `ion_type` | The atom type of the ions, or `0` for none |
| `bins` | Bins along the axis, with `0` meaning 20 |
| `axis` | The front axis, `Axis::Z` by default |

The slice must have one entry for every atom in the frame, ions included.
The usual source of the ice flags is CHILL+: an atom is ice when its label
is cubic, hexagonal, reclassified cubic or reclassified hexagonal.

## A slab with ions in the liquid

The program below builds the slab from the [interface tutorial](interface.md):
four ordered layers and four displaced layers. In the displaced half, every
twelfth atom becomes an ion of type 2, and all other atoms are water of
type 1. CHILL+ runs on the water only, through `species: 1`, and the result
becomes the ice flags.

```rust
use seams::{Axis, BrineOptions, ChillOptions, Label, System};

const LAYERS: usize = 8;
const SOLID: usize = 4;
const PER_LAYER: usize = 8 * 3 * 3;

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

fn main() -> Result<(), seams::Error> {
    let (xyz, size) = slab(LAYERS, SOLID);
    let atoms = xyz.len() / 3;
    let types: Vec<i32> = (0..atoms)
        .map(|i| {
            if i >= SOLID * PER_LAYER && i % 12 == 0 {
                2
            } else {
                1
            }
        })
        .collect();
    let cell = [0.0, 0.0, 0.0, size[0], size[1], size[2], 0.0, 0.0, 0.0];

    let mut frame = System::new()?;
    frame.set_atoms(&xyz, &cell, &types, &[])?;
    let water_only = ChillOptions {
        species: 1,
        ..ChillOptions::default()
    };
    let labels = frame.chill_plus(&water_only)?.labels;
    let ice: Vec<i32> = labels
        .iter()
        .map(|&code| {
            let crystal = [Label::Cubic, Label::Hexagonal, Label::Recubic, Label::Rehex];
            crystal.iter().any(|label| *label as i32 == code) as i32
        })
        .collect();

    let options = BrineOptions {
        water_type: 1,
        ion_type: 2,
        bins: 16,
        axis: Axis::Z,
    };
    let front = frame.brine(&ice, &options)?;

    let fronts = front.fronts()?;
    println!(
        "ice from {:.1} to {:.1} angstroms, {:.1} thick",
        fronts.enter, fronts.exit, fronts.thickness
    );

    let rejection = front.rejection()?;
    println!(
        "molality in ice {:.2}, in liquid {:.2} mol/kg",
        rejection.ice, rejection.liquid
    );
    println!("rejection coefficient {:.2}", rejection.k);

    let pockets = front.pockets()?;
    println!(
        "pockets {}, reservoir waters {}",
        pockets.pockets, pockets.reservoir_waters
    );

    let profile = front.profile()?;
    println!("z (angstroms)  molality  ice fraction");
    for ((z, molality), fraction) in profile
        .coordinate
        .iter()
        .zip(&profile.molality)
        .zip(&profile.ice_fraction)
    {
        println!("{z:>13.1} {molality:>9.2} {fraction:>13.2}");
    }
    Ok(())
}
```

```text
ice from 1.6 to 23.2 angstroms, 21.7 thick
molality in ice 0.00, in liquid 2.46 mol/kg
rejection coefficient 0.00
pockets 4, reservoir waters 291
z (angstroms)  molality  ice fraction
          1.6      0.00          0.50
          4.8      0.00          1.00
          7.9      0.00          1.00
         11.1      0.00          1.00
         14.3      0.00          1.00
         17.5      0.00          1.00
         20.6      0.00          1.00
         23.8      0.68          0.39
         27.0      3.85          0.00
         30.2      2.60          0.00
         33.3      0.82          0.00
         36.5      3.47          0.00
         39.7      2.25          0.00
         42.9      0.96          0.00
         46.0      4.34          0.00
         49.2      1.03          0.00
```

## Reading the four reports

`Brine` owns the analysis and frees it when dropped. It has four queries.

| Method | Returns |
| --- | --- |
| `fronts` | `BrineFronts`: `enter` and `exit` positions and the `thickness` between them, in angstroms, and `found`, which is true when both crossings exist |
| `rejection` | `Rejection`: the molality of the bulk ice and of the bulk liquid in mol/kg, their ratio `k`, and `defined`, which is false when the ratio cannot be formed |
| `profile` | `BrineProfile`: bin centres in angstroms, molality in mol/kg and a dimensionless ice fraction, one entry per bin |
| `pockets` | `Pockets`: the number of liquid pockets inside the ice, not counting the liquid reservoir, and the number of waters in that reservoir |

In the output above the ice fraction is 1 through the ordered half and
falls to 0 at the upper front. The box is periodic along z, so the ice also
has a lower face near the bottom of the box, which is why the first bin is
only half ice. The two crossings are reported at 1.6 and 23.2 angstroms.
The molality is zero in the ice and between 0.7 and 4.3 mol/kg in the
liquid bins. The rejection coefficient `k` is 0 because no ion sits in the
ice. A real freezing front has a `k` above zero and below one.

The ions here are a pattern, not a salt concentration. The molality that
`brine` reports is the amount of ion against the mass of water in each
region.

The NaCl frame, the slab table and the water census of that frame are in
the engine tutorial [Brine and NaCl](https://docs.dseams.info/tutorials/brine.html).
