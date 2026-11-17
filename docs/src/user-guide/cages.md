# Tutorial: cages

Score hexagonal-cage and double-diamond-cage membership, then ask for
closed cages of one ring signature.

<iframe title="Ice Ih hexagonal cages, cubic double-diamond cages, then the clathrate cells" src="https://odysee.com/$/embed/dseams-cages:1c258cea9384acd2e21eeec509c5eedc050d08db" width="960" height="540" allowfullscreen></iframe>

Ice Ih hexagonal cages, cubic double-diamond cages, then the clathrate cells.

`CageOptions::default` uses a 3.5 angstrom cutoff, the seeded graph
(mutual four-neighbour seeds plus union completions), `k` of 4, and
`complete: false`. `Cages::counts` returns four disjoint populations:
`hexagonal`, `cubic`, `water`, and `both`. On the eight-atom diamond
those four numbers add up to the atom count:

```rust
fn main() -> Result<(), seams::Error> {
    let (xyz, edge) = seams::diamond8();
    let mut system = seams::System::new()?;
    system.set_ortho(&xyz, edge, edge, edge)?;
    let cages = system.cages(&seams::CageOptions::default())?;
    let counts = cages.counts()?;
    assert_eq!(
        counts.hexagonal + counts.cubic + counts.water + counts.both,
        8
    );
    let labels = cages.labels(8)?;
    assert_eq!(labels.len(), 8);
    Ok(())
}
```

`labels` is one `CageLabel` code per atom: `Water` (0), `Hex` (1),
`Cubic` (2), or `Both` (3). `Drop` frees the cage set.

## A signature census

`signature_cages` counts closed cages whose ring census matches `spec`.
The default spec is `"512"`. On the eight-atom diamond that spec is
rejected with `Status::Argument`:

```rust
fn main() -> Result<(), seams::Error> {
    let (xyz, edge) = seams::diamond8();
    let mut system = seams::System::new()?;
    system.set_ortho(&xyz, edge, edge, edge)?;
    let err = system
        .signature_cages(&seams::SignatureOptions::default())
        .unwrap_err();
    assert_eq!(err.status(), Some(seams::Status::Argument));
    Ok(())
}
```

`SignatureMatch` holds `cages` and `atoms`. `SignatureOptions.graph`
selects the neighbour graph. The default is `Graph::Cutoff`.

The sI guest frame in seams-core is what `dseams/tests/cpp_match.rs`
compares with the C++ oracle when `SEAMS_CPP_ORACLE` and
`SEAMS_SOURCE_ROOT` are set. The oxygen-only sI dump in this crate is
the [bulk ice](bulk-ice.md) example: 46 atoms, all CHILL+ clathrate, 54
primitive six-rings.

The engine how-to for the same cage search is
[Cage search](https://docs.dseams.info/howto/cages-trace.html).
