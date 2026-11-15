# Rust tutorial

`dseams-sys` is the FFI crate. `dseams` is the safe wrapper. Point `SEAMS_LIBDIR` at the directory holding `libseams.so` before building.

`dseams/tests/ice.rs` is the test `cargo test` runs:

```{literalinclude} ../../dseams/tests/ice.rs
:language: rust
:lines: 29-63
```

The ice example builds a 64-atom cell:

```bash
export SEAMS_LIBDIR=/path/to/seams-core/build/src
cargo run --example ice
cargo test -- --test-threads=1
```

The integration test checks both CHILL+ rules, q6 above 0.3, four neighbours, and a six-ring fraction above one half.

## The rest of the call set

`dseams/tests/cpp_match.rs` runs when `SEAMS_CPP_ORACLE` names seams-core's `binding_oracle` and `SEAMS_SOURCE_ROOT` names the seams-core checkout.
It calls `chill`, `steinhardt` with the Lechner-Dellago average, `rings` and `vertices`, `cages`, `knn`, `rdf`, `running_cn`, `coordination`, `hbonds`, `density_axis`, `fingerprint`, `site_table`, `contact_pairs`, `domains`, `prisms`, `monolayer`, and `signature_cages`, then checks each value against seams-core's `tests/binding_oracle.cpp`.
On ice Ih and the sI guest frame the test prints:

```
rustcall hexagonal 128
rustcall q6bar 0.562448843702
rustcall vert 6 0
rustcall cages 128 0 0 0
rustcall knn 512
rustcall sheet 256
rustcall sig 2 40
```
