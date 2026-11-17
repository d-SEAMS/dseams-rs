# Tutorial: an ice-water interface

CHILL+ on a slab separates hexagonal ice, cubic ice, interfacial ice, and
water. The basal-interface trajectory and its layer profile are in the
engine tutorial. This page is the same call from Rust, on a cell the
crate ships, and the recording of that basal frame.

<iframe title="CHILL+ on the basal interface" src="https://odysee.com/$/embed/dseams-interface:74af20635ceeef7945f8e22cb5b02522a865baa6" width="960" height="540" allowfullscreen></iframe>

CHILL+ on the basal interface.

`ChillOptions` holds the cutoff (default 3.5 angstroms), a species
filter (`0` keeps every atom), the neighbour `Graph` (`Cutoff`,
`Mutual`, or `Seeded`), and the `ChillRule` (`Published` or `Ovito`).
Published edges are inclusive. OVITO edges are open.

```rust
fn main() -> Result<(), seams::Error> {
    let mut system = seams::System::new()?;
    system.read("dseams/tests/data/ice1h.lammpstrj", 1, 1)?;
    let ice = system.chill_plus(&seams::ChillOptions::default())?;
    assert_eq!(ice.counts[seams::Label::Hexagonal as usize], 128);
    assert_eq!(ice.counts[seams::Label::Interfacial as usize], 0);
    let _name = seams::label_name(seams::Label::Interfacial);
    Ok(())
}
```

`chill` is the original CHILL classifier and returns the same
`Classification` shape: `labels`, one code per atom, and `counts`, nine
populations in `Label` order. `label_name` is the short name of a code.
On this ice Ih frame the interfacial count is 0 because every atom is
hexagonal. A mixed slab is where `Label::Interfacial` and `Label::Water`
become nonzero.

`set_frame` stores a tilted cell. The nine numbers are origin (`ox`,
`oy`, `oz`), edge lengths (`lx`, `ly`, `lz`), then tilts `xy`, `xz`,
`yz`. `Axis::Z` is the default axis for the density and brine profiles
when you bin that slab.

The basal frame, the layer command, and the recorded stack are in
[Ice-water interface](https://docs.dseams.info/tutorials/interface.html).
