# How to: read a trajectory

A `System` holds one frame. It is empty until one of four calls fills it,
and `count` reports how many atoms it holds, which is 0 for an empty frame.

| Call | What it stores |
| --- | --- |
| `set_ortho(xyz, lx, ly, lz)` | Coordinates in a box with zero origin and no tilt. `xyz` is a flat list of `x, y, z` triples in angstroms. |
| `set_frame(xyz, box9)` | Coordinates and a nine-number cell: `ox, oy, oz, lx, ly, lz, xy, xz, yz`. |
| `set_atoms(xyz, box9, types, ids)` | The same cell, plus optional atom types and ids. Empty slices leave those columns unset. |
| `read(path, frame, type_filter)` | One frame from a file. |

## From arrays in memory

Use `set_ortho` for a rectangular box and `set_frame` for a tilted one.
The tilts are the LAMMPS `xy`, `xz` and `yz`, and a zero tilt means an
orthogonal axis.

```rust
fn main() -> Result<(), seams::Error> {
    let (xyz, edge) = seams::diamond8();

    let mut ortho = seams::System::new()?;
    ortho.set_ortho(&xyz, edge, edge, edge)?;

    let mut box9 = [0.0; 9];
    box9[3] = edge;
    box9[4] = edge;
    box9[5] = edge;
    box9[6] = 0.3;
    let mut tilted = seams::System::new()?;
    tilted.set_frame(&xyz, &box9)?;

    println!("{} atoms, {} atoms", ortho.count(), tilted.count());
    Ok(())
}
```

```text
8 atoms, 8 atoms
```

Use `set_atoms` when species matter, as in the [brine tutorial](brine.md).
Pass one type per atom, and an empty slice for the ids you do not have.

## From a file

`read` takes a path, a **1-based** frame number and a type filter. A
negative filter keeps every atom, and a positive one keeps only atoms of
that type. The format is picked from the file. Every build reads LAMMPS
dumps and XYZ files. The bundled build also enables readcon-core and
chemfiles when pkg-config finds them; an external `libseams` keeps the
readers with which it was built. `has_readcon()` reports `.con` support,
and `has_chemfiles()` reports formats such as PDB and GRO. See
[Link libseams](link.md).

`nframes` counts the frames in a file, which tells you how far a loop may
go:

```rust
use seams::{ChillOptions, Label, System};

fn main() -> Result<(), seams::Error> {
    let path = "ice1h.lammpstrj";
    let frames = seams::nframes(path)?;
    for index in 1..=frames as i32 {
        let mut frame = System::new()?;
        frame.read(path, index, -1)?;
        let ice = frame.chill_plus(&ChillOptions::default())?;
        println!(
            "frame {index}: {} atoms, {} hexagonal",
            frame.count(),
            ice.counts[Label::Hexagonal as usize]
        );
    }
    Ok(())
}
```

```text
frame 1: 128 atoms, 128 hexagonal
```

This runs on the file from the [ice Ih tutorial](ice-ih.md). A frame number
past the end of the file, or a type filter that matches no atom, is a
`Status::Range` error, so loop up to `nframes`.

A path with a nul byte is rejected before it reaches the library, with
code 4 and the message `text contains a nul`.
