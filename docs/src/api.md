# API reference

The reference is rustdoc, generated from the crate source. Every public
type, function, field, and enum variant in `dseams` and `dseams-sys` is
in that output. This site carries the pages for
[`seams`](api/seams/index.html) and
[`seams_sys`](api/seams_sys/index.html). `dseams` denies missing documentation, and each public
item carries a doctest.

Build it from this repository:

```bash
# The docs.rs build: rustdoc does not link libseams.
DOCS_RS=1 cargo doc --no-deps --open

# The same pages, linked against a library you built.
export SEAMS_LIBDIR=/path/to/seams-core/bbdir/src
export SEAMS_INCLUDE=/path/to/seams-core/include:$SEAMS_LIBDIR
cargo doc --no-deps --open
```

`cargo doc` writes `target/doc/seams/index.html` for the safe crate and
`target/doc/seams_sys/index.html` for the raw declarations. The package
field `documentation` names the docs.rs pages of the published `dseams`
and `dseams-sys` crates.

`seams::ffi` is the re-export of `seams_sys`. Most programs use the safe
crate. The raw names (`seams_chill_plus`, `SEAMS_OK`, and the opaque
handles) are the C API, documented in the engine book at
[the stable C API](https://docs.dseams.info/stable/c.html).

`docs/check_rustdoc.py` reads those HTML pages after `cargo doc` and
fails if a public symbol is absent. The development page runs it.

## Safe crate

One frame and the calls that fill it.

| Item | Role |
| --- | --- |
| `System` | One frame. `new`, `set_ortho`, `set_frame`, `set_atoms`, `read`, `count`, and every analysis. |
| `diamond8` | Eight-atom cubic diamond and its lattice constant. |
| `nframes` | Frame count of a trajectory path. |
| `version`, `abi` | Library version text, and the ABI number (1). |
| `set_num_threads`, `num_threads` | Process-global OpenMP width. |

Ice labels.

| Item | Role |
| --- | --- |
| `System::chill`, `System::chill_plus` | Original CHILL and CHILL+. Both return `Classification`. |
| `ChillOptions` | Cutoff, species filter, `Graph`, and `ChillRule`. |
| `Label`, `label_name` | Nine label codes and their short names. `counts[label as usize]` is the population. |
| `ChillRule` | `Published` or `Ovito`. |

Order parameters.

| Item | Role |
| --- | --- |
| `System::q4q6` | Local q4 and q6 on the cutoff shell. Returns `Q4Q6`. |
| `System::steinhardt` | Local q_l, and the Lechner-Dellago mean when `average` is set. Returns `Steinhardt`. |
| `System::ql` | q_l on a named graph. `OrderOptions`. |
| `System::q6bar` | q6-bar, its mean and median, and the count above `ice_cut`. `Q6BarOptions`, `Q6Bar`. |

Neighbours, rings, and cages.

| Item | Role |
| --- | --- |
| `System::neighbours`, `System::knn`, `System::neighbour_degree` | Cutoff or mutual list, k-nearest list, or the degree of each atom. |
| `Neighbours` | `nnz`, `degrees`, and `pairs`, which yields `NeighbourPair`. |
| `Graph` | `Cutoff`, `Mutual`, or `Seeded`. |
| `System::rings`, `System::six_ring_fraction` | Primitive rings. `Rings` has `size`, `vertices`, `histogram`, `fraction`, and `iter`. |
| `RingSymmetry`, `ring_symmetry_name` | Symmetry class of a primitive ring. |
| `System::cages`, `System::signature_cages` | Hexagonal and double-diamond membership, or closed cages of one signature. |
| `Cages`, `CageCounts`, `CageLabel` | Owned membership, the four disjoint counts, and the per-atom code. |
| `SignatureOptions`, `SignatureMatch` | Signature text such as `512`, and the cage and atom totals. |

Distributions, bonds, and topology.

| Item | Role |
| --- | --- |
| `System::rdf`, `System::running_cn`, `System::coordination` | Partial RDF (`Distribution`), running coordination, and the integral to `rmax`. |
| `System::density` | Number density along one `Axis`. `DensityOptions`, `DensityProfile`. |
| `System::hbonds` | Hydrogen-bond count. `BondOptions`. |
| `System::site_table`, `System::contact_pairs`, `System::domains` | Site kinds, unlike contacts, and the largest polar or apolar domain. |
| `SiteKind`, `DomainSubset`, `DomainOptions`, `DomainReport`, `Contacts` | The codes and the reports those calls return. |
| `System::fingerprint` | Topological fingerprint. `Fingerprint` exposes `key`, `atom`, and `rings`. |
| `System::prisms`, `System::monolayer`, `System::symmetry` | Prism stacks, a monolayer ring histogram, and per-atom ice-shell labels. |

Brine and errors.

| Item | Role |
| --- | --- |
| `System::brine` | Planar ice front from an ice assignment. `BrineOptions` selects species, bins, and `Axis`. |
| `Brine` | `fronts`, `rejection`, `profile`, `pockets`. |
| `BrineFronts`, `Rejection`, `BrineProfile`, `Pockets` | The four reports. Lengths are angstroms. Molality is mol/kg. |
| `Error`, `Status` | A failed call. `status`, `code`, and `message`. |

Handles (`System`, `Neighbours`, `Rings`, `Cages`, `Fingerprint`,
`Brine`) are `Send` and not `Sync`. `Drop` frees the C object.
