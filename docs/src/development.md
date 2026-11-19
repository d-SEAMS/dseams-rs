# Building from source

Use this page when you want the crates from a checkout, to read the tests,
run the examples or build the documentation yourself. Programs that only
depend on `dseams` need none of it, because `cargo add dseams` fetches
everything.

The repository holds the two crates, `dseams-sys` and `dseams`, plus this
book and the examples. The engine, the C API and the command-line tool live
in [seams-core](https://github.com/d-SEAMS/seams-core). A new analysis
starts there and is wrapped here afterwards.

## Build and test with the bundled engine

You need Rust 1.85 or newer, Python 3, and a C++20 compiler with OpenMP,
as described in [Link libseams](user-guide/link.md).

```bash
git clone https://github.com/d-SEAMS/dseams-rs
cd dseams-rs
python3 dseams-sys/vendor.py
cargo test --features bundled -- --test-threads=1
```

`vendor.py` downloads the seams-core sources and Eigen 3.4.0 that the
bundled build compiles into `dseams-sys/vendor/`. A checkout does not ship
those files, but the package on crates.io does. `--test-threads=1` keeps
the OpenMP width stable between tests.

The tests are:

- `dseams/tests/ice.rs` calls every safe wrapper on the cubic cell.
- `dseams/tests/cpp_match.rs` compares the analyses with the C++ engine's
  own results on ice Ih, sI, an XYZ file, a CON file and a triclinic sH
  dump. It needs a seams-core build and prints that it skipped when
  `SEAMS_CPP_ORACLE` and `SEAMS_SOURCE_ROOT` are not set.
- The documentation examples in `dseams/src/lib.rs` run as doctests.

## Run the examples

`dseams/examples/` holds five programs. Each runs on the dumps in
`dseams/tests/data/`:

| Example | What it does |
| --- | --- |
| `ice` | Classifies a 64-atom cubic ice crystal built in code. |
| `minimal` | Parses the sI framework dump in Rust, stores it with `set_ortho` and checks its CHILL+ labels. |
| `ice_ih` | Prints the ice Ih census of the [ice Ih tutorial](user-guide/ice-ih.md). |
| `lang_tasks` | Prints the census line that every d-SEAMS language binding prints. |
| `binding_overhead` | A timing driver. It reads commands on standard input and times the wrapped calls. |

```bash
cargo run --features bundled --example ice_ih
cargo test --features bundled --examples -- --test-threads=1
```

The first command prints `rust ice nop 128 q6 0.625855 hexagonal 128 rings 256`.

## Use another libseams

To test against a `libseams` you built, set `SEAMS_LIBDIR` to its directory
and leave out `--features bundled`. The test binaries get an rpath to that
directory, so they run without `LD_LIBRARY_PATH`. Setting `PKG_CONFIG_PATH`
instead tests the pkg-config route. Both are described in
[Link libseams](user-guide/link.md).

## Build the documentation

The book is built with mdBook 0.5.4 and the API reference with rustdoc:

```bash
DOCS_RS=1 cargo doc --no-deps --workspace
python3 docs/check_rustdoc.py target/doc
mdbook build docs
cp -r target/doc docs/book/api
cp docs/rustdoc-index.html docs/book/api/index.html
python3 docs/check_book.py docs/book
```

`DOCS_RS=1` makes the build script skip linking, as it does on docs.rs,
because rustdoc does not need the library. `check_rustdoc.py` fails when a
public symbol is missing from the generated HTML, and `check_book.py` checks
the built pages, their links and the recordings.

Every Rust program in the book and the READMEs is compiled and run by one
script:

```bash
python3 docs/check_examples.py --features bundled
```

A `text` block that directly follows a `rust` block is the program's
expected output, and the script compares the two.

## The declarations

`dseams-sys/src/lib.rs` is generated from the C header `seams.h` and is not
edited by hand:

```bash
python3 dseams-sys/gen_sys.py path/to/seams-core/include/seams.h dseams-sys/src/lib.rs
```

## Contributing

The conventions for changes, commits and the changelog are in
[AGENTS.md](https://github.com/d-SEAMS/dseams-rs/blob/main/AGENTS.md).
