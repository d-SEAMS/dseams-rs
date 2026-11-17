# Changelog

All notable changes to `dseams-sys` and `dseams` are documented in this file.

The format is [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The crate version follows the seams-core release whose C API it binds.

Unreleased notes live in [`changelog.d/`](changelog.d/) and are assembled
by [towncrier](https://towncrier.readthedocs.io/).

<!-- towncrier release notes start -->

## [2.14.1] - 2026-11-17

### Added

- The book and the rustdoc pages are published at https://rust.dseams.info/ from every push to `main`. The README links the site, docs.rs, the engine book's Rust page and the Rust recording.

### Changed

- The documentation is a book with a getting started, a user guide, a rustdoc API reference, and a development page. The ice Ih, cage, ring, interface, brine, and nucleation pages include the matching d-SEAMS recordings.
- The documentation site moves to https://rust.dseams.info/.
- The tag publish workflow now authenticates exclusively through crates.io trusted publishing via GitHub OIDC and accepts patch releases of the Rust crates for the same `seams-core` minor release.
- `dseams` and `dseams-sys` now enable the `bundled` feature by default so `cargo add dseams` builds without a preinstalled `libseams`; `SEAMS_LIBDIR` still takes precedence, and `default-features = false` probes `pkg-config`.

### Fixed

- The bundled build script probes the default C++ compiler for C++20 and OpenMP and falls back to `g++` when `CXX` is unset and the default `c++` fails that probe.


## [2.14.0] - 2026-11-17

### Added

- The Rust crates live in their own repository, d-SEAMS/dseams-rs, and CI builds seams-core at the tag named in `seams-core.env` to test them.
- The `minimal`, `ice_ih` and `lang_tasks` examples read dumps shipped in `dseams/tests/data`, and `cargo test --examples` checks the lines they print.
- `dseams-sys` declares `seams_rings_chordless`, the chordless cycles of one size in a neighbour graph, and the `bundled` build compiles the seams-core sources it needs.

### Changed

- `dseams-sys` links an installed libseams by default: `SEAMS_LIBDIR` (with `SEAMS_INCLUDE`), then the `seams` pkg-config module within 2.14 <= v < 3. The opt-in `bundled` feature compiles one from the pinned seams-core sources and replaces both the old default bundled build and the `system` feature.

### Fixed

- The `bundled` build adds the C++ compiler's library directory to the link line, so rustc's linker finds `libstdc++` and `libgomp`.
