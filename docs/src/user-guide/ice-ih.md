# Tutorial: ice Ih

Read the ice Ih dump shipped with the crate, then print the neighbour,
ring, and CHILL+ census. The same recording is the Rust front on that cell.

<iframe title="Rust on ice Ih" src="https://odysee.com/$/embed/dseams-rust:687055b1ac9dfe7596006cb4f2fa466de9492ca5" width="960" height="540" allowfullscreen></iframe>

Rust on ice Ih.

## The dump

`dseams/tests/data/ice1h.lammpstrj` is one frame of 128 atoms, LAMMPS type
1. `System::read` takes a 1-based frame index. The type filter `1` keeps
type 1. A negative filter keeps every atom; on this file both selections
are the 128 waters.

From a checkout, with [libseams linked](link.md):

```bash
cargo run --example ice_ih
cargo run --example lang_tasks
```

`ice_ih` prints a line the example test requires exactly:

```text
rust ice nop 128 q6 0.625855 hexagonal 128 rings 256
```

`nop` is `System::count`. `q6` is the mean of `q4q6(3.5).q6`, printed to
six digits. `hexagonal` is `counts[Label::Hexagonal as usize]` from
`chill_plus` with `ChillOptions::default` (cutoff 3.5 angstroms, cutoff
graph, published table). `rings` is the number of primitive six-rings,
the first element of `six_ring_fraction`.

## The shared census

`lang_tasks` prints the one line every d-SEAMS language front prints for
this file. The example test requires:

```text
pairs 512 rings 0 0 0 0 0 0 256 chill 0 128 0 0 0 0 0 0 0
```

`pairs` is `Neighbours::nnz` for `NeighbourOptions::default`, which is the
cutoff graph at 3.5 angstroms. Self pairs are omitted. 512 directed pairs
on 128 atoms is four neighbours each.

`rings` is `Rings::histogram(6)` for `RingOptions` with `max_size` 6. The
seven integers are sizes 0 through 6. Size 6 is 256. That is the same
six-ring count `ice_ih` prints. The default ring graph is the cutoff graph.

`chill` is the nine `Classification::counts` from `chill_plus`, in label
order: cubic, hexagonal, water, interfacial, clathrate, interfacial
clathrate, unclassified, reclassified cubic, reclassified hexagonal.
Hexagonal is 128. The other eight populations are 0.

The calls, with the paths the examples use, are:

```rust
use seams::{ChillOptions, Label, NeighbourOptions, RingOptions, System};

fn census(path: &str) -> Result<(), seams::Error> {
    let mut frame = System::new()?;
    frame.read(path, 1, -1)?;
    let pairs = frame.neighbours(&NeighbourOptions::default())?.nnz()?;
    let rings = frame
        .rings(&RingOptions {
            max_size: 6,
            ..RingOptions::default()
        })?
        .histogram(6)?;
    let chill = frame.chill_plus(&ChillOptions::default())?;
    assert_eq!(frame.count(), 128);
    assert_eq!(pairs, 512);
    assert_eq!(rings[6], 256);
    assert_eq!(chill.counts[Label::Hexagonal as usize], 128);
    Ok(())
}
```

`Drop` frees the system, the neighbour list, and the ring set when those
values go out of scope.

The mean local q6 on this frame is the 0.625855 above. `q4q6` returns one
q4 and one q6 per atom on the cutoff shell. `steinhardt` with
`average: true` also returns the Lechner-Dellago neighbour mean; the
nucleation tutorial uses the q6-bar summary of that average.

The engine tutorial for primitive rings on this cell and on the mixed
TIP4P frame is
[Primitive rings](https://docs.dseams.info/tutorials/rings.html).
