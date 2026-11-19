# Tutorial: nucleation

To follow a crystal nucleus you need a per-atom measure of crystallinity
and a threshold. d-SEAMS offers two. The Lechner-Dellago q6-bar averages
the Steinhardt q6 over each atom and its neighbours, and an atom counts as
ice when its q6-bar is above `ice_cut`. CHILL+ gives a label instead of a
number. This tutorial grows a crystalline slab one layer at a time and
watches both counts.

<iframe title="Nucleation q6-bar" src="https://odysee.com/$/embed/dseams-nucleation:965e5772f700e5b1d91f1b069557eb9e87f1c60b" width="960" height="540" allowfullscreen></iframe>

The recording follows a nucleation trajectory. This page uses frames built
in code, so the program needs no data files.

## A growing crystal

`slab(layers, solid)` stacks eight layers of the diamond cell. The first
`solid` layers are perfect crystal, and the others are displaced by up to
one angstrom per coordinate, a crude liquid. It is the slab from the
[interface tutorial](interface.md) with a variable crystal thickness. The
program measures it with `q6bar` at two cuts and with CHILL+.

```rust
use seams::{ChillOptions, Label, Q6BarOptions, System};

const LAYERS: usize = 8;

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
    println!("solid layers  q6bar>0.36  q6bar>0.50  CHILL+ ice");
    for solid in [0, 2, 4, 6, 8] {
        let (xyz, size) = slab(LAYERS, solid);
        let mut frame = System::new()?;
        frame.set_ortho(&xyz, size[0], size[1], size[2])?;

        let loose = frame.q6bar(&Q6BarOptions::default())?;
        let strict = frame.q6bar(&Q6BarOptions {
            ice_cut: 0.5,
            ..Q6BarOptions::default()
        })?;
        let counts = frame.chill_plus(&ChillOptions::default())?.counts;
        let crystal: i32 = [Label::Cubic, Label::Hexagonal, Label::Recubic, Label::Rehex]
            .iter()
            .map(|label| counts[*label as usize])
            .sum();
        println!(
            "{solid:>12} {:>11} {:>11} {crystal:>11}",
            loose.n_ice, strict.n_ice
        );
    }
    Ok(())
}
```

```text
solid layers  q6bar>0.36  q6bar>0.50  CHILL+ ice
           0          79          12           0
           2         188         120         111
           4         309         254         253
           6         445         407         400
           8         576         576         576
```

The slab has 576 atoms, 72 per layer. With no crystal, `q6bar` at the
default cut of 0.36 still marks 79 atoms as ice, because random
displacements sometimes leave a locally ordered patch. At a cut of 0.5 only
12 remain, and CHILL+ finds none. With every layer ordered, all 576 atoms
pass either cut. In between, the count rises steadily as layers are added.
Once a crystal is present, the 0.5 cut and CHILL+ agree to within about ten
atoms, while the looser cut counts disordered atoms next to the crystal as
well.

The cut is a threshold you choose, not a constant of nature. Look at the
distribution of `values` for your own system before you fix it.

## The Q6Bar result

`q6bar` returns a `Q6Bar` with four fields:

- `values` has one q6-bar per atom.
- `mean` and `median` summarise the finite values.
- `n_ice` is the number of atoms strictly above `ice_cut`.

`Q6BarOptions::default` uses a 3.5 angstrom cutoff, species `0` (every
atom) and an `ice_cut` of 0.36. Raising or lowering the cut changes
`n_ice` without changing `values`.

## The underlying order parameters

`steinhardt` returns the local q_l, and with `average: true` also the
neighbour mean that q6-bar is built from. `order` is 6 by default and may be
3, 4, 6, 8 or 12. `ql` takes the same parameters on a named neighbour graph
through `OrderOptions.graph`. `q4q6` is a shortcut for the two most common
orders.

```rust
use seams::{SteinhardtOptions, System};

fn main() -> Result<(), seams::Error> {
    let mut frame = System::new()?;
    frame.read("ice1h.lammpstrj", 1, -1)?;
    let result = frame.steinhardt(&SteinhardtOptions {
        average: true,
        ..Default::default()
    })?;
    let mean = |values: &[f64]| values.iter().sum::<f64>() / values.len() as f64;
    println!("local q6 {:.3}", mean(&result.local));
    println!(
        "averaged q6 {:.3}",
        mean(&result.average.expect("average was requested"))
    );
    Ok(())
}
```

```text
local q6 0.626
averaged q6 0.562
```

The averaged mean is the smaller one here. Averaging each atom's q6 over
its neighbour shell smooths out atom-to-atom noise, which is why Lechner
and Dellago introduced it: the averaged value separates ice from liquid
more cleanly than q6 alone. Cuts such as the default `ice_cut` of 0.36 are
set against the averaged values.

The 148-frame trajectory and the per-frame cluster sizes are in the engine
tutorial [Nucleation](https://docs.dseams.info/tutorials/nucleation.html).
