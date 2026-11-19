# User guide

The tutorials each take one analysis from a frame to a number you can
check. Every program on these pages is complete. Copy it into a project
that depends on `dseams`, as set up in [Getting started](../getting-started.md),
and it runs as shown.

Some tutorials read a LAMMPS dump from disk. Two small dumps ship in the
`dseams` source, and the pages that need them show one `curl` line to
fetch each into the directory where you run `cargo run`:

```bash
base=https://raw.githubusercontent.com/d-SEAMS/dseams-rs/v2.14.1/dseams/tests/data
curl -fsSLO "$base/ice1h.lammpstrj"
curl -fsSLO "$base/genice_sI.lammpstrj"
```

`ice1h.lammpstrj` is 128 oxygen atoms of proton-disordered ice Ih.
`genice_sI.lammpstrj` is the 46-oxygen framework of one sI clathrate cell.
The three slab tutorials build their frames in code and need no files.

## Tutorials

- [Ice Ih](ice-ih.md) reads the 128-molecule cell and reports pairs, rings and CHILL+ labels.
- [Bulk ice](bulk-ice.md) tells cubic ice, hexagonal ice and sI clathrate apart.
- [Cages](cages.md) scores hexagonal and double-diamond cage membership and counts cages by ring signature.
- [Rings](rings.md) counts primitive rings and reads their atoms.
- [An ice-water interface](interface.md) labels a slab layer by layer.
- [Brine](brine.md) locates the ice fronts of a slab and the ion content on each side.
- [Nucleation](nucleation.md) follows q6-bar and CHILL+ counts as a crystal grows.

## How-to

- [Link libseams](link.md) covers the bundled engine, a `libseams` you built, and pkg-config.
- [Read a trajectory](read.md) shows the four ways to fill a frame.
- [Handle errors](errors.md) explains `Error`, `Status` and handle ownership.

The engine book has the same science with the `seams` command and full
trajectories. Start at [docs.dseams.info](https://docs.dseams.info).
