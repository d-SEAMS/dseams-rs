#!/usr/bin/env python3
# Copyright (c) d-SEAMS developers
"""Compile and run every Rust example in the book and the READMEs.

Each fenced `rust` block is a complete program with a `main`. It becomes a
binary of a scratch crate that depends on `dseams` and `dseams-sys`, runs in
a directory that holds the two shipped dumps, and must exit with status 0.
A `text` block that directly follows a `rust` block is that program's
standard output, and the two must match.

    check_examples.py                       dependencies are this workspace
    check_examples.py --features bundled    compile libseams from vendor/
    check_examples.py --registry 2.14.1     dependencies are the crates.io release

The library comes from the same places the crates look: `SEAMS_LIBDIR`, the
`bundled` feature, or pkg-config.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ROOT / "README.md",
    ROOT / "dseams" / "README.md",
    ROOT / "dseams-sys" / "README.md",
    *sorted((ROOT / "docs" / "src").rglob("*.md")),
]
DATA = ROOT / "dseams" / "tests" / "data"
FENCE = re.compile(r"^```([^\n]*)\n(.*?)^```[ \t]*$", re.S | re.M)


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)


def blocks(path):
    """Yield (line, program, expected stdout or None) for each rust block."""
    text = path.read_text(encoding="utf-8")
    found = list(FENCE.finditer(text))
    for index, match in enumerate(found):
        if match.group(1).strip() != "rust":
            continue
        expected = None
        if index + 1 < len(found):
            following = found[index + 1]
            between = text[match.end() : following.start()]
            if following.group(1).strip() == "text" and not between.strip():
                expected = following.group(2)
        line = text.count("\n", 0, match.start()) + 2
        yield line, match.group(2), expected


def collect():
    programs = []
    for path in SOURCES:
        for line, code, expected in blocks(path):
            if "fn main" not in code:
                fail(f"{path.relative_to(ROOT)}:{line}: a rust block needs its own main")
            name = f"ex{len(programs):03d}"
            programs.append((name, path.relative_to(ROOT), line, code, expected))
    return programs


def manifest(args):
    if args.registry:
        where = f'version = "={args.registry}"'
    else:
        where = None
    deps = []
    for crate in ("dseams", "dseams-sys"):
        fields = [where or f'path = "{ROOT / crate}"']
        if args.features:
            listed = ", ".join(f'"{name}"' for name in args.features.split(","))
            fields.append(f"features = [{listed}]")
        deps.append(f"{crate} = {{ {', '.join(fields)} }}")
    return (
        '[package]\nname = "book-examples"\nversion = "0.0.0"\nedition = "2021"\n\n'
        "[dependencies]\n" + "\n".join(deps) + "\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--features", help="comma separated dseams features")
    parser.add_argument("--registry", help="use this crates.io version of the crates")
    args = parser.parse_args()

    programs = collect()
    if not programs:
        fail("no rust examples found")
    work = Path(tempfile.mkdtemp(prefix="book-examples-"))
    try:
        (work / "src" / "bin").mkdir(parents=True)
        (work / "Cargo.toml").write_text(manifest(args), encoding="utf-8")
        (work / "src" / "main.rs").write_text("fn main() {}\n", encoding="utf-8")
        for name, _, _, code, _ in programs:
            (work / "src" / "bin" / f"{name}.rs").write_text(code, encoding="utf-8")
        run_dir = work / "run"
        run_dir.mkdir()
        for dump in DATA.glob("*.lammpstrj"):
            shutil.copy(dump, run_dir / dump.name)

        env = dict(os.environ, CARGO_TARGET_DIR=str(work / "target"), OMP_NUM_THREADS="1")
        env.pop("RUSTDOCFLAGS", None)
        build = subprocess.run(["cargo", "build", "--bins"], cwd=work, env=env)
        if build.returncode != 0:
            fail("the book examples do not compile")
        libdir = os.environ.get("SEAMS_LIBDIR") or os.environ.get("SEAMS_LIB_DIR")
        if libdir:
            env["LD_LIBRARY_PATH"] = libdir + os.pathsep + env.get("LD_LIBRARY_PATH", "")

        failures = []
        for name, path, line, _, expected in programs:
            binary = work / "target" / "debug" / name
            result = subprocess.run(
                [str(binary)], cwd=run_dir, env=env, capture_output=True, text=True
            )
            where = f"{path}:{line}"
            if result.returncode != 0:
                failures.append(f"{where}: exited with {result.returncode}\n{result.stdout}{result.stderr}")
            elif expected is not None and result.stdout != expected:
                failures.append(
                    f"{where}: output differs\n--- expected\n{expected}"
                    f"--- actual\n{result.stdout}"
                )
            else:
                print(f"ok {where}")
        if failures:
            fail("\n".join(failures))
        print(f"examples ok ({len(programs)} programs)")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
