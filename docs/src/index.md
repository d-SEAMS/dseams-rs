# dseams

`dseams` is the safe Rust crate for [d-SEAMS](https://dseams.info), the ice,
clathrate and ring engine for molecular simulation frames. The engine, the
C API (`libseams`, header `seams.h`) and the command-line tool live in
[seams-core](https://github.com/d-SEAMS/seams-core). This book documents the
two crates in this repository:

| Crate | Library | Role |
| --- | --- | --- |
| `dseams-sys` | `seams_sys` | Raw declarations generated from `seams.h` |
| `dseams` | `seams` | Owned handles, options structs, iterators, `Result` errors |

The crates.io name `seams` belongs to an unrelated project, so the packages
are `dseams-sys` and `dseams`. Code still says `use seams::System`.

```rust
fn main() -> Result<(), seams::Error> {
    let (xyz, edge) = seams::diamond8();
    seams::set_num_threads(1)?;
    let mut system = seams::System::new()?;
    system.set_ortho(&xyz, edge, edge, edge)?;
    let ice = system.chill_plus(&seams::ChillOptions::default())?;
    assert_eq!(ice.counts[seams::Label::Cubic as usize], 8);
    Ok(())
}
```

Coordinates and cutoffs are angstroms. A cell is nine LAMMPS numbers:
origin, edge lengths, then the tilts `xy`, `xz`, `yz`.

## In this book

The layout follows the same four-part shape as the NumPy documentation.

- [Getting started](getting-started.md) installs the crate, links `libseams`, and classifies the eight-atom cubic cell.
- The [user guide](user-guide/index.md) is the tutorials and the how-to pages.
- The [API reference](api.md) is the rustdoc generated from the crates.
- [Development](development.md) is how to build, test, and regenerate the declarations.

The engine book, including the C API and the science tutorials, is
[docs.dseams.info](https://docs.dseams.info). The C header reference is
[the stable C API](https://docs.dseams.info/stable/c.html).

Cite the 2020 paper, [DOI 10.1021/acs.jcim.0c00031](https://doi.org/10.1021/acs.jcim.0c00031),
as recorded in `CITATION.cff`.
