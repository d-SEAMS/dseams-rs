# How to: read a trajectory

A `System` owns one frame. Four calls fill it.

| Call | What it stores |
| --- | --- |
| `set_ortho(xyz, lx, ly, lz)` | Coordinates in an orthorhombic cell whose origin is zero. `xyz` is `x, y, z` triples, in angstroms. |
| `set_frame(xyz, box9)` | Coordinates and a nine-number cell: `ox, oy, oz, lx, ly, lz, xy, xz, yz`. |
| `set_atoms(xyz, box9, types, ids)` | The same cell, plus optional species and ids. Empty slices leave those columns unset. |
| `read(path, frame, type_filter)` | One frame from a path. `frame` is 1-based. A negative `type_filter` keeps every atom. |

`count` is the number of points. It is 0 until one of those calls
succeeds.

```rust
fn main() -> Result<(), seams::Error> {
    let (xyz, edge) = seams::diamond8();
    let mut ortho = seams::System::new()?;
    ortho.set_ortho(&xyz, edge, edge, edge)?;
    assert_eq!(ortho.count(), 8);

    let mut box9 = [0.0; 9];
    box9[3] = edge;
    box9[4] = edge;
    box9[5] = edge;
    box9[6] = 0.3;
    let mut tilted = seams::System::new()?;
    tilted.set_frame(&xyz, &box9)?;
    assert_eq!(tilted.count(), 8);
    Ok(())
}
```

`read` accepts XYZ, CON, a chemfiles format, or a LAMMPS dump when the
linked `libseams` was built with that reader. The bundled library reads
LAMMPS dumps and XYZ. The ice dumps in this crate are LAMMPS, every atom
type 1:

```rust
fn main() -> Result<(), seams::Error> {
    let mut system = seams::System::new()?;
    system.read("dseams/tests/data/ice1h.lammpstrj", 1, 1)?;
    assert_eq!(system.count(), 128);
    Ok(())
}
```

`nframes(path)` counts frames in a trajectory. A nul byte inside the
path is rejected before the call reaches the library; `code()` is 4
(`SEAMS_ERR_ARG`) and `message()` is `text contains a nul`.

`examples/ice_ih.rs` and `examples/lang_tasks.rs` call `read`.
`examples/minimal.rs` parses a LAMMPS dump in Rust and calls
`set_ortho`, which is the path its test locks.
