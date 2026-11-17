# Tutorial: rings

Count primitive rings on the ice Ih cell. The recording then shows the
same count on the mixed frame and on ice Ih.

<iframe title="Primitive rings on the mixed frame, then on ice Ih" src="https://odysee.com/$/embed/dseams-rings:cfb3b6687dd81847ecb005782df8cf5143617be5" width="960" height="540" allowfullscreen></iframe>

Primitive rings on the mixed frame, then on ice Ih.

`RingOptions::default` is a 3.5 angstrom cutoff, the cutoff graph, and
`max_size` 6 (the largest ring size the search keeps, from 3 through 12).
`Rings::histogram(6)` returns seven bins, index equal to ring size.
`Rings::fraction` is the fraction of atoms that sit on a ring of one size.
`six_ring_fraction` is that pair for size 6: the histogram entry, then
the fraction.

On `dseams/tests/data/ice1h.lammpstrj` the size-6 bin is 256, which is the
`rings 256` locked by `cargo run --example ice_ih` and the `rings` field
of the [shared census](ice-ih.md):

```text
pairs 512 rings 0 0 0 0 0 0 256 chill 0 128 0 0 0 0 0 0 0
```

```rust
fn main() -> Result<(), seams::Error> {
    let mut system = seams::System::new()?;
    system.read("dseams/tests/data/ice1h.lammpstrj", 1, 1)?;
    let rings = system.rings(&seams::RingOptions::default())?;
    let hist = rings.histogram(6)?;
    let fraction = rings.fraction(6)?;
    assert_eq!(hist[6], 256);
    assert!(fraction.is_finite());
    let first = rings.vertices(0)?;
    assert!(!first.is_empty());
    for ring in rings.iter().take(1) {
        let _vertices = ring?;
    }
    Ok(())
}
```

`vertices(index)` is the atom indices of one ring. `iter` yields each
ring's vertices as a `Result`. `size` is the number of rings.
`ring_symmetry_name` turns a `RingSymmetry` code into its short name
(`"pentagon"`, `"hexagon"`, and the cage-face names).

`Drop` frees the ring set.

The engine tutorial, including the mixed TIP4P frame this crate does not
ship, is [Primitive rings](https://docs.dseams.info/tutorials/rings.html).
