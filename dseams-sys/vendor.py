#!/usr/bin/env python3
# Copyright (c) d-SEAMS developers
# SPDX-License-Identifier: MIT
"""Fill dseams-sys/vendor/ with the pinned seams-core sources and Eigen.

The `bundled` feature compiles libseams from vendor/, and cargo package
ships it. The seams-core tag is the one in seams-core.env at the
repository root. Run this before cargo package or cargo publish:

    python3 dseams-sys/vendor.py                      # download the pinned tag
    python3 dseams-sys/vendor.py --source ../seams-core  # git archive from a checkout

Eigen comes from the 3.4.0 release tarball, checked against its sha256.
Pass --eigen-tarball to use a tarball that is already on disk.
"""

import argparse
import hashlib
import io
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
PIN_FILE = HERE.parent / "seams-core.env"
EIGEN_VERSION = "3.4.0"
EIGEN_URL = f"https://gitlab.com/libeigen/eigen/-/archive/{EIGEN_VERSION}/eigen-{EIGEN_VERSION}.tar.gz"
EIGEN_SHA256 = "8586084f71f9bde545ee7fa6d00288b264a2b7ac3607b974e54d13e7162c1c72"
# MPL2 for the library, BSD for AlignedBox.h, Apache for BFloat16.h.
EIGEN_NOTICES = ("COPYING.MPL2", "COPYING.BSD", "COPYING.APACHE", "COPYING.README")


def sources():
    listed = []
    for line in (HERE / "sources.txt").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        listed.append(line.split(":", 1)[1].strip() if ":" in line else line)
    return listed


def pin():
    values = {}
    for line in PIN_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values["SEAMS_CORE_REPO"], values["SEAMS_CORE_REF"]


def fetch(url, path):
    with urllib.request.urlopen(url) as response, open(path, "wb") as out:
        shutil.copyfileobj(response, out)


def wanted(rel):
    """True for the files the bundled build reads, relative to seams-core."""
    if rel in WANTED:
        return True
    parent, _, name = rel.rpartition("/")
    return parent == "src/include/internal" and name.endswith((".hpp", ".h"))


def extract_seams(archive, dest, strip):
    count = 0
    for member in archive.getmembers():
        if not member.isfile():
            continue
        parts = member.name.split("/", strip)
        if len(parts) <= strip:
            continue
        rel = parts[strip]
        if not wanted(rel):
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.extractfile(member) as src, open(target, "wb") as out:
            shutil.copyfileobj(src, out)
        count += 1
    missing = [rel for rel in WANTED if not (dest / rel).is_file()]
    if missing:
        raise SystemExit(f"seams-core archive lacks {', '.join(missing)}")
    return count


def seams_from_checkout(checkout, ref, dest):
    probe = subprocess.run(
        ["git", "-C", str(checkout), "cat-file", "-e", f"{ref}^{{commit}}"],
        capture_output=True,
    )
    if probe.returncode != 0:
        raise SystemExit(f"{checkout} has no commit {ref}; fetch it first")
    tar = subprocess.run(
        ["git", "-C", str(checkout), "archive", "--format=tar", ref],
        check=True,
        capture_output=True,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(tar)) as archive:
        return extract_seams(archive, dest, 0)


def seams_from_github(repo, ref, dest, tmp):
    tarball = pathlib.Path(tmp) / "seams-core.tar.gz"
    fetch(f"{repo}/archive/{ref}.tar.gz", tarball)
    with tarfile.open(tarball) as archive:
        return extract_seams(archive, dest, 1)


def unpack_eigen(tarball, dest):
    digest = hashlib.sha256(pathlib.Path(tarball).read_bytes()).hexdigest()
    if digest != EIGEN_SHA256:
        raise SystemExit(f"{tarball}: sha256 {digest}, expected {EIGEN_SHA256}")
    prefix = f"eigen-{EIGEN_VERSION}/"
    keep = [prefix + "Eigen/"] + [prefix + name for name in EIGEN_NOTICES]
    with tarfile.open(tarball) as archive:
        for member in archive.getmembers():
            if not member.isfile() or not any(member.name.startswith(k) for k in keep):
                continue
            target = dest / member.name[len(prefix):]
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", help="seams-core git checkout holding the pinned tag")
    parser.add_argument("--eigen-tarball", help=f"eigen-{EIGEN_VERSION}.tar.gz on disk")
    args = parser.parse_args(argv)

    repo, ref = pin()
    vendor = HERE / "vendor"
    if vendor.exists():
        shutil.rmtree(vendor)
    vendor.mkdir()

    with tempfile.TemporaryDirectory() as tmp:
        if args.source:
            count = seams_from_checkout(pathlib.Path(args.source), ref, vendor)
        else:
            count = seams_from_github(repo, ref, vendor, tmp)
        print(f"seams-core {ref}: {count} files")
        tarball = args.eigen_tarball
        if tarball is None:
            tarball = pathlib.Path(tmp) / f"eigen-{EIGEN_VERSION}.tar.gz"
            fetch(EIGEN_URL, tarball)
        unpack_eigen(tarball, vendor / "eigen")
    total = sum(1 for p in vendor.rglob("*") if p.is_file())
    print(f"vendored {total} files into {vendor}")
    return 0


WANTED = sources() + ["include/seams.h", "include/seams_version.h.in", "LICENSE"]

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
