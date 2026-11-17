#!/usr/bin/env python3
# Copyright (c) d-SEAMS developers
"""Check the built book: recordings, internal links, engine links."""

import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "src"

# Page, relative to the book output, and the player that belongs on it.
PLAYERS = {
    "getting-started.html": "https://odysee.com/$/embed/dseams-rust:687055b1ac9dfe7596006cb4f2fa466de9492ca5",
    "user-guide/ice-ih.html": "https://odysee.com/$/embed/dseams-rust:687055b1ac9dfe7596006cb4f2fa466de9492ca5",
    "user-guide/cages.html": "https://odysee.com/$/embed/dseams-cages:1c258cea9384acd2e21eeec509c5eedc050d08db",
    "user-guide/rings.html": "https://odysee.com/$/embed/dseams-rings:cfb3b6687dd81847ecb005782df8cf5143617be5",
    "user-guide/interface.html": "https://odysee.com/$/embed/dseams-interface:74af20635ceeef7945f8e22cb5b02522a865baa6",
    "user-guide/brine.html": "https://odysee.com/$/embed/dseams-brine:124a3a7fa52cdf7aff34ac00cfba6068e240a947",
    "user-guide/nucleation.html": "https://odysee.com/$/embed/dseams-nucleation:965e5772f700e5b1d91f1b069557eb9e87f1c60b",
}
ALLOWED = set(PLAYERS.values())
HREF = re.compile(r"""(?:href|src)=["']([^"']+)["']""", re.I)
FORBIDDEN = (
    "embed.txt",
    "TODO",
    "FIXME",
    "placeholder",
    "coming soon",
    "rgpot",
    "sphinxcontrib",
    "density_axis",
    "API_SYMBOLS",
)


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)


def chapter_html(md_rel):
    """mdBook's HTML name for a SUMMARY path."""
    path = Path(md_rel)
    if path.name == "index.md":
        return path.with_name("index.html") if path.parent.as_posix() not in {".", ""} else Path("index.html")
    if path.name == "README.md":
        return path.with_suffix(".html")
    return path.with_suffix(".html")


def summary_pages():
    pages = []
    for line in (SRC / "SUMMARY.md").read_text(encoding="utf-8").splitlines():
        found = re.search(r"\(([^)]+\.md)\)", line)
        if not found:
            continue
        rel = found.group(1)
        if not (SRC / rel).is_file():
            fail(f"SUMMARY links missing source {rel}")
        pages.append(chapter_html(rel).as_posix())
    return pages


def check_sources():
    for path in SRC.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for word in FORBIDDEN:
            if word in text:
                fail(f"{path} contains {word}")
        if "odysee.com/" in text.replace("odysee.com/$/embed/", ""):
            fail(f"{path} has an Odysee URL that is not an embed")


def check_html(book):
    pages = summary_pages()
    if "index.html" not in pages:
        fail("book has no index")
    for page in pages:
        html_path = book / page
        if not html_path.is_file():
            fail(f"missing built page {page}")
        text = html_path.read_text(encoding="utf-8", errors="replace")
        main = text
        start = text.find("<main")
        end = text.rfind("</main>")
        if start >= 0 and end > start:
            main = text[start:end]
        for src in HREF.findall(main):
            if "odysee.com" in src and src not in ALLOWED and "odysee.com/$/embed/" in src:
                fail(f"{page} embeds an unexpected player {src}")
            if "odysee.com" in src and "/$ /embed/".replace(" ", "") not in src and "odysee.com/$/embed/" not in src:
                fail(f"{page} uses a non-embed Odysee URL {src}")
        expected = PLAYERS.get(page)
        if expected and expected not in text:
            fail(f"{page} is missing its recording")
        if page == "user-guide/bulk-ice.html" and "<iframe" in main:
            fail("bulk-ice has no matching recording")
        for word in FORBIDDEN:
            if word in main:
                fail(f"{page} contains {word}")
        check_links(book, html_path, main)
    print(f"book ok ({len(pages)} pages, {len(PLAYERS)} recordings)")


def check_links(book, html_path, text):
    external = []
    for href in HREF.findall(text):
        if href.startswith(("#", "mailto:", "javascript:")):
            continue
        if href.startswith(("http://", "https://")):
            external.append(href.split("#", 1)[0])
            continue
        target = (html_path.parent / href.split("#", 1)[0]).resolve()
        try:
            target.relative_to(book.resolve())
        except ValueError:
            fail(f"{html_path.name} links outside the book: {href}")
        if href.split("#", 1)[0] and not target.is_file():
            fail(f"{html_path.relative_to(book)} broken link {href}")
    return external


def check_external(book):
    seen = []
    for page in summary_pages():
        text = (book / page).read_text(encoding="utf-8", errors="replace")
        start = text.find("<main")
        end = text.rfind("</main>")
        if start >= 0 and end > start:
            text = text[start:end]
        for href in check_links(book, book / page, text):
            if href not in seen:
                seen.append(href)
    for href in seen:
        if href.startswith("https://docs.rs/"):
            fail(f"unpublished docs.rs link in the book: {href}")
        request = urllib.request.Request(href, headers={"User-Agent": "dseams-docs"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                code = response.status
        except Exception as exc:
            status = getattr(getattr(exc, "code", None), "real", None)
            code = getattr(exc, "code", None)
            if code is None:
                fail(f"{href} failed: {exc}")
            if "doi.org" in href and code in {403, 401}:
                continue
            fail(f"{href} returned {code}")
        if code not in {200, 301, 302}:
            fail(f"{href} returned {code}")
    print(f"links ok ({len(seen)} external)")


def main(argv):
    book = Path(argv[1] if len(argv) > 1 else ROOT / "docs" / "book")
    if not book.is_dir():
        fail(f"missing book output {book}")
    check_sources()
    check_html(book)
    check_external(book)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
