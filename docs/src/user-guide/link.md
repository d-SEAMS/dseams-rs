# How to: link libseams

`dseams` calls the d-SEAMS engine through `libseams`. The `dseams-sys`
build script finds that library in one of three ways and uses the first
that applies:

1. the directory named by `SEAMS_LIBDIR`,
2. a copy compiled from source, when the `bundled` feature is on,
3. the `seams` module known to pkg-config.

If none applies, the build stops with the message "libseams not found" and
a hint. A `seams_version.h` from another major release, or from a minor
release older than 2.14, also stops the build. Any later 2.x release links.

## Compile a copy: the bundled feature

```bash
cargo add dseams --features bundled
```

The crate package carries the engine sources and Eigen 3.4.0, and compiles
them with the `cc` crate. You need:

- a C++20 compiler with OpenMP (GCC 11 or newer, or a recent Clang),
- an x86_64 machine, because the shell classifier uses AVX2.

Set `CC` and `CXX` to choose the compiler, for example
`CC=gcc CXX=g++ cargo build`. The bundled engine reads LAMMPS dumps and XYZ
files. It does not read `.con` files or the chemfiles formats. Use one of
the next two routes when you need those readers.

Programs built this way link the engine statically. They run anywhere,
with no library path to set.

## Use a libseams you built

Build and install the engine from its repository. This uses the tag
`v2.14.1`, the release that `dseams` 2.14.1 is built against:

```bash
git clone --branch v2.14.1 https://github.com/d-SEAMS/seams-core
cd seams-core
meson setup build --prefix="$HOME/.local/libseams" -Dwith_tests=false -Dwith_cli=false
meson compile -C build
meson install -C build
```

Meson needs Eigen 3.4 and fetches it when it is not installed. Then point
the crate at the directory that holds `libseams.so`:

```bash
export SEAMS_LIBDIR="$(dirname "$(find "$HOME/.local/libseams" -name libseams.so | head -n 1)")"
export LD_LIBRARY_PATH="$SEAMS_LIBDIR"
cargo run
```

`SEAMS_LIB_DIR` is accepted as a synonym. The directory must contain
`libseams.so`, or `libseams.dylib` on macOS. Debian and Ubuntu install to
`lib/x86_64-linux-gnu` under the prefix, and other systems use `lib` or
`lib64`, which is why the command above asks `find`.

`SEAMS_INCLUDE` is optional. It is a path list of header directories, and
when it is set the build checks the version in `seams_version.h` against
the crate.

The shared library is found at run time through the loader, so keep the
directory on `LD_LIBRARY_PATH` (or `DYLD_LIBRARY_PATH` on macOS), or add
an rpath to your own build. The crate adds one only to its own tests and
examples.

## Use pkg-config

When an installed `libseams` has a `seams.pc` file, leave `SEAMS_LIBDIR`
unset and put the directory with that file on `PKG_CONFIG_PATH`:

```bash
export PKG_CONFIG_PATH="$HOME/.local/libseams/lib/x86_64-linux-gnu/pkgconfig"
export LD_LIBRARY_PATH="$HOME/.local/libseams/lib/x86_64-linux-gnu"
cargo run
```

Versions from 2.14.0 up to, but not including, 3.0.0 are accepted. The
installed library keeps every reader it was built with, including `.con`
and chemfiles when those were enabled.

## Check what you linked

`seams::version()` returns the library's version text, and `seams::abi()`
returns its ABI number:

```rust
fn main() {
    println!("libseams {} (ABI {})", seams::version(), seams::abi());
}
```

```text
libseams 2.14.1 (ABI 1)
```

## When it fails

| Message | Cause and fix |
| --- | --- |
| libseams not found | No library was found. Turn on `bundled`, set `SEAMS_LIBDIR`, or set `PKG_CONFIG_PATH`. |
| SEAMS_LIBDIR=... holds no libseams | The directory has no `libseams` file. Point at the one that does. |
| error while loading shared libraries: libseams.so | The program linked, but the loader cannot see the directory. Set `LD_LIBRARY_PATH`. |
| A message naming `seams_version.h` | The library is from another major release or older than 2.14. Build a newer tag. |
