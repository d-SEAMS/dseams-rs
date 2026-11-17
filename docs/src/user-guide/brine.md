# Tutorial: brine

Measure a planar ice front from an ice assignment. The recording is the
NaCl front. The ion trajectory itself is in the engine tutorial.

<iframe title="The brine front" src="https://odysee.com/$/embed/dseams-brine:124a3a7fa52cdf7aff34ac00cfba6068e240a947" width="960" height="540" allowfullscreen></iframe>

The brine front.

`System::brine` takes one integer per atom, nonzero when that atom is
ice, and a `BrineOptions`. The slice length must equal `count`. The
default options keep every species (`water_type` 0, `ion_type` 0),
choose 20 bins when `bins` is 0, and use `Axis::Z`.

```rust
fn main() -> Result<(), seams::Error> {
    let (xyz, edge) = seams::diamond8();
    let mut system = seams::System::new()?;
    system.set_ortho(&xyz, edge, edge, edge)?;
    let front = system.brine(&[1; 8], &seams::BrineOptions::default())?;
    let _profile = front.profile()?;
    Ok(())
}
```

Marking every atom ice, as this call does, builds a front on the cubic
cell. A trajectory with liquid and ions passes the CHILL+ crystal codes
as the ice flags and sets `ion_type` to the ion species.

`Brine` owns the C object and frees it on drop. The queries are:

| Method | Returns |
| --- | --- |
| `fronts` | `BrineFronts`: `enter`, `exit`, and `thickness` in angstroms, and `found` when both crossings exist |
| `rejection` | `Rejection`: bulk-ice and bulk-liquid molality in mol/kg, their ratio `k`, and `defined` |
| `profile` | `BrineProfile`: bin centres in angstroms, molality in mol/kg, and a dimensionless ice fraction |
| `pockets` | `Pockets`: pocket count, excluding the liquid reservoir, and `reservoir_waters` |

The NaCl frame, the slab table, and the water census of that frame are in
[Brine and NaCl](https://docs.dseams.info/tutorials/brine.html).
