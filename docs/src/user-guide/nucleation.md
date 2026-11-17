# Tutorial: nucleation

Summarise the Lechner-Dellago q6-bar and count atoms above an ice cut.
The recording follows a nucleation trajectory. The three-frame mW dump
and its cluster table are in the engine tutorial.

<iframe title="Nucleation q6-bar" src="https://odysee.com/$/embed/dseams-nucleation:965e5772f700e5b1d91f1b069557eb9e87f1c60b" width="960" height="540" allowfullscreen></iframe>

Nucleation q6-bar.

`Q6BarOptions::default` uses a 3.5 angstrom cutoff, species filter 0, and
`ice_cut` 0.36. `q6bar` returns one value per atom, the mean and median
of the finite values, and `n_ice`, the count strictly above the cut.

```rust
fn main() -> Result<(), seams::Error> {
    let (xyz, edge) = seams::diamond8();
    let mut system = seams::System::new()?;
    system.set_ortho(&xyz, edge, edge, edge)?;
    let summary = system.q6bar(&seams::Q6BarOptions::default())?;
    assert_eq!(summary.values.len(), 8);
    assert!(summary.mean.is_finite());
    Ok(())
}
```

On the eight-atom diamond the value vector has one entry per atom and
the mean is finite. `n_ice` depends on the cut. The same options struct
is the nucleation census: raise or lower `ice_cut` to change `n_ice`
without changing `values`.

`steinhardt` with `SteinhardtOptions { average: true, ..Default::default() }`
returns the local q6 and the neighbour mean that q6-bar is built from.
`order` is 6 by default, and may be 3, 4, 6, 8, or 12. `ql` is the same
parameter on a named graph (`OrderOptions.graph`).

CHILL+ on a growing cluster is a different count from `n_ice`. Crystal
atoms for that cluster are `Label::Cubic`, `Label::Hexagonal`,
`Label::Recubic`, and `Label::Rehex`. The [ice Ih](ice-ih.md) tutorial
shows the nine-bin `counts` array those labels index.

The 148-frame trajectory and the per-frame cluster sizes are in
[Nucleation](https://docs.dseams.info/tutorials/nucleation.html).
