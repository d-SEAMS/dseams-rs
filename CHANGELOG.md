# Changelog

All notable changes to `dseams-sys` and `dseams` are documented in this file.

The format is [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The crate version follows the seams-core release whose C API it binds.

Unreleased notes live in [`newsfragments/`](newsfragments/) and are assembled
by [towncrier](https://towncrier.readthedocs.io/).

<!-- towncrier release notes start -->

## [2.14.1] - 2026-11-18

### Changed

- `dseams` and `dseams-sys` now bind seams-core v2.14.1, including the sources generated for the optional bundled build.

## [2.14.0] - 2026-11-17

### Added

- The Rust crates live in their own repository, d-SEAMS/dseams-rs, and CI builds seams-core at the tag named in `seams-core.env` to test them.
- The `minimal`, `ice_ih` and `lang_tasks` examples read dumps shipped in `dseams/tests/data`, and `cargo test --examples` checks the lines they print.
- `dseams-sys` declares `seams_rings_chordless`, the chordless cycles of one size in a neighbour graph, and the `bundled` build compiles the seams-core sources it needs.

### Changed

- `dseams-sys` links an installed libseams by default: `SEAMS_LIBDIR` (with `SEAMS_INCLUDE`), then the `seams` pkg-config module within 2.14 <= v < 3. The opt-in `bundled` feature compiles one from the pinned seams-core sources and replaces both the old default bundled build and the `system` feature.

### Fixed

- The `bundled` build adds the C++ compiler's library directory to the link line, so rustc's linker finds `libstdc++` and `libgomp`.
