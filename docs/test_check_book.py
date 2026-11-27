#!/usr/bin/env python3
# Copyright (c) d-SEAMS developers
"""Self-test for repository links in check_book.py. No network."""

import contextlib
import importlib.util
import io
import ntpath
import socket
import sys
from pathlib import Path, PureWindowsPath


def load():
    path = Path(__file__).resolve().parent / "check_book.py"
    spec = importlib.util.spec_from_file_location("check_book_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def assert_missing(book, href, rel):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stderr(buf):
            book.check_repository_link(href)
    except SystemExit as exc:
        code = exc.code
    else:
        book.fail(f"{href} did not fail")
    message = buf.getvalue().strip()
    if code != 1 or href not in message or f"missing path {rel}" not in message:
        book.fail(f"unclear missing-path error for {href}: {message!r}")


def assert_posix_validator(book):
    """Reject URL paths with POSIX rules, including shapes ntpath misses.

    PureWindowsPath and ntpath are the Windows flavour on every host, so
    this does not read os.name and does not patch anything.
    """
    anchor = "C:\\checkout"
    rel = "D:AGENTS.md"
    windows = PureWindowsPath(rel)
    if windows.is_absolute() or ".." in windows.parts:
        book.fail(f"Windows flavour already rejects {rel!r}: {windows.parts}")
    joined = ntpath.join(anchor, rel)
    if ntpath.splitdrive(joined)[0].upper() == "C:":
        book.fail(f"ntpath kept the drive-relative path on the anchor: {joined}")
    if book.repository_parts(rel) is not None:
        book.fail(f"validator accepted {rel!r}")
    backslash = "docs\\..\\..\\etc"
    escaped = ntpath.normpath(ntpath.join(anchor, backslash))
    under_anchor = ntpath.normcase(ntpath.normpath(anchor) + "\\")
    if ntpath.normcase(escaped).startswith(under_anchor):
        book.fail(f"backslash path did not leave the anchor: {escaped}")
    if book.repository_parts(backslash) is not None:
        book.fail("validator accepted a backslash path")
    for collapsed in ("./AGENTS.md", ".//AGENTS.md", "docs//file.md"):
        folded = PureWindowsPath(collapsed)
        if folded.is_absolute() or ".." in folded.parts:
            book.fail(f"Windows flavour already rejects {collapsed!r}")
        if book.repository_parts(collapsed) is not None:
            book.fail(f"validator accepted {collapsed!r}")
    for sample in (
        "C:/AGENTS.md",
        "\\..\\AGENTS.md",
        "a\x00b",
        "/AGENTS.md",
        "foo/../AGENTS.md",
    ):
        if book.repository_parts(sample) is not None:
            book.fail(f"validator accepted {sample!r}")
    good = book.repository_parts("docs/src/SUMMARY.md")
    if good != ("docs", "src", "SUMMARY.md"):
        book.fail(f"normal path parsed as {good!r}")
    joined_good = ntpath.normpath(ntpath.join(anchor, *good))
    expect = ntpath.normpath(anchor + "\\docs\\src\\SUMMARY.md")
    if joined_good != expect:
        book.fail(f"validated parts did not stay under the anchor: {joined_good}")


def main():
    book = load()
    blob = "https://github.com/d-SEAMS/dseams-rs/blob/main/AGENTS.md"
    missing = "https://github.com/d-SEAMS/dseams-rs/blob/main/no-such-book-file.md"
    tree = "https://github.com/d-SEAMS/dseams-rs/tree/main/docs"
    external = "https://example.com/dseams-book-link-check"
    other_repo = "https://github.com/d-SEAMS/seams-core"
    repo_home = "https://github.com/d-SEAMS/dseams-rs"

    if book.check_repository_link(blob) is not True:
        book.fail(f"existing blob was rejected: {blob}")
    if book.check_repository_link(blob + "#contributing") is not True:
        book.fail("fragment on an existing markdown file was rejected")
    if book.check_repository_link(tree) is not True:
        book.fail(f"existing tree was rejected: {tree}")
    assert_missing(book, missing, "no-such-book-file.md")
    assert_missing(book, "https://github.com/d-SEAMS/dseams-rs/blob/main/docs", "docs")
    assert_missing(book, "https://github.com/d-SEAMS/dseams-rs/tree/main/AGENTS.md", "AGENTS.md")

    # URL paths are POSIX. These are the shapes Path() collapses or, on
    # Windows, fails to treat as escape. Each must fail as a missing path.
    prefix = "https://github.com/d-SEAMS/dseams-rs/blob/main/"
    bad_links = [
        ("./AGENTS.md", "./AGENTS.md"),
        (".//AGENTS.md", ".//AGENTS.md"),
        ("D%3AAGENTS.md", "D:AGENTS.md"),
        ("C%3A/AGENTS.md", "C:/AGENTS.md"),
        ("%5C..%5CAGENTS.md", "\\..\\AGENTS.md"),
        ("docs%5C..%5C..%5Cetc", "docs\\..\\..\\etc"),
        ("a%00b", "a\x00b"),
    ]
    for suffix, rel in bad_links:
        assert_missing(book, prefix + suffix, rel)
    assert_posix_validator(book)

    calls = []

    def urlopen(request, timeout=30):
        calls.append((request.full_url, timeout, request.get_header("User-agent")))
        return Response()

    original = book.urllib.request.urlopen
    book.urllib.request.urlopen = urlopen
    try:
        book.check_one_external(external)
        book.check_one_external(other_repo)
        book.check_one_external(repo_home)
        book.check_one_external(blob)
        book.check_one_external(tree)
    finally:
        book.urllib.request.urlopen = original
    expected = [
        (external, 30, "dseams-docs"),
        (other_repo, 30, "dseams-docs"),
        (repo_home, 30, "dseams-docs"),
    ]
    if calls != expected:
        book.fail(f"external link did not use the network path: {calls}")

    def blocked(*args, **kwargs):
        raise OSError("network blocked")

    original_connection = socket.create_connection
    socket.create_connection = blocked
    try:
        book.check_one_external(blob)
        book.check_one_external(tree)
        book.check_one_external(blob + "#contributing")
    finally:
        socket.create_connection = original_connection
    print("repository links ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
