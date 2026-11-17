#!/usr/bin/env python3
"""Add and validate search metadata on every generated documentation page."""

import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree

DESCRIPTION = (
    "Rust documentation for d-SEAMS molecular trajectory analysis, including "
    "ice classification, clathrate cages, and primitive rings."
)
DOI = "https://doi.org/10.1021/acs.jcim.0c00031"
REPOSITORY = "https://github.com/d-SEAMS/dseams-rs"
SITE_NAME = "dseams Rust documentation"
START = "<!-- dseams-seo:start -->"
END = "<!-- dseams-seo:end -->"


def canonical_url(base_url, relative):
    path = relative.as_posix()
    if path == "index.html":
        path = ""
    elif path.endswith("/index.html"):
        path = path[: -len("index.html")]
    return base_url.rstrip("/") + "/" + quote(path, safe="/.-~")


def page_title(text, relative):
    match = re.search(r"<title\b[^>]*>(.*?)</title\s*>", text, re.I | re.S)
    if match:
        title = html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()
        if title:
            return re.sub(r"\s+", " ", title)
    label = relative.stem.replace("-", " ").replace("_", " ").strip().title()
    return f"{label or 'Documentation'} - {SITE_NAME}"


def remove_generated_metadata(text):
    text = re.sub(
        re.escape(START) + r".*?" + re.escape(END) + r"\s*",
        "",
        text,
        flags=re.S,
    )
    text = re.sub(
        r"<meta\b(?=[^>]*\bname\s*=\s*['\"]description['\"])[^>]*>\s*",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"<link\b(?=[^>]*\brel\s*=\s*['\"]canonical['\"])[^>]*>\s*",
        "",
        text,
        flags=re.I,
    )
    return text


def metadata(title, description, canonical, sitemap):
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "SoftwareApplication",
                "name": "dseams",
                "applicationCategory": "ScientificApplication",
                "operatingSystem": "Linux, macOS, Windows",
                "url": canonical,
                "citation": DOI,
            },
            {
                "@type": "SoftwareSourceCode",
                "name": "dseams-rs",
                "codeRepository": REPOSITORY,
                "programmingLanguage": "Rust",
                "url": REPOSITORY,
                "citation": DOI,
            },
        ],
    }
    escaped_title = html.escape(title, quote=True)
    escaped_description = html.escape(description, quote=True)
    escaped_url = html.escape(canonical, quote=True)
    sitemap_url = html.escape(sitemap, quote=True)
    return "\n".join(
        [
            START,
            f'<meta name="description" content="{escaped_description}">',
            f'<link rel="canonical" href="{escaped_url}">',
            f'<link rel="sitemap" type="application/xml" href="{sitemap_url}">',
            '<meta property="og:type" content="website">',
            f'<meta property="og:site_name" content="{html.escape(SITE_NAME, quote=True)}">',
            f'<meta property="og:title" content="{escaped_title}">',
            f'<meta property="og:description" content="{escaped_description}">',
            f'<meta property="og:url" content="{escaped_url}">',
            '<meta name="twitter:card" content="summary">',
            f'<meta name="twitter:title" content="{escaped_title}">',
            f'<meta name="twitter:description" content="{escaped_description}">',
            '<script type="application/ld+json">'
            + json.dumps(graph, ensure_ascii=False, separators=(",", ":"))
            + "</script>",
            END,
        ]
    )


def apply(root, base_url):
    pages = sorted(root.rglob("*.html"))
    if not pages:
        raise ValueError(f"no HTML pages found in {root}")

    titles = {}
    prepared = []
    for path in pages:
        text = remove_generated_metadata(path.read_text(encoding="utf-8", errors="replace"))
        relative = path.relative_to(root)
        title = page_title(text, relative)
        titles[title] = titles.get(title, 0) + 1
        prepared.append((path, relative, text, title))

    urls = []
    for path, relative, text, title in prepared:
        if titles[title] > 1:
            title = f"{title} ({relative.as_posix()})"
        description = f"{title}. {DESCRIPTION}"
        canonical = canonical_url(base_url, relative)
        title_tag = f"<title>{html.escape(title)}</title>"
        if re.search(r"<title\b[^>]*>.*?</title\s*>", text, re.I | re.S):
            text = re.sub(
                r"<title\b[^>]*>.*?</title\s*>",
                title_tag,
                text,
                count=1,
                flags=re.I | re.S,
            )
        else:
            text = re.sub(r"<head\b[^>]*>", lambda match: match.group(0) + "\n" + title_tag, text, count=1, flags=re.I)
        block = metadata(
            title,
            description,
            canonical,
            canonical_url(base_url, Path("sitemap.xml")),
        )
        if not re.search(r"</head\s*>", text, re.I):
            raise ValueError(f"{relative} has no closing head element")
        text = re.sub(r"</head\s*>", block + "\n</head>", text, count=1, flags=re.I)
        path.write_text(text, encoding="utf-8")
        if relative.name != "404.html" and not re.search(
            r'<meta\b[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*noindex',
            text,
            re.I,
        ):
            urls.append(canonical)

    sitemap = ElementTree.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for url in urls:
        node = ElementTree.SubElement(sitemap, "url")
        ElementTree.SubElement(node, "loc").text = url
    ElementTree.ElementTree(sitemap).write(
        root / "sitemap.xml", encoding="utf-8", xml_declaration=True
    )


def attribute(text, element, key, value):
    pattern = (
        rf"<{element}\b(?=[^>]*\b{key}\s*=\s*['\"]{re.escape(value)}['\"])[^>]*>"
    )
    return re.search(pattern, text, re.I)


def check(root):
    pages = sorted(root.rglob("*.html"))
    if not pages:
        raise ValueError(f"no HTML pages found in {root}")
    seen_titles = {}
    seen_descriptions = {}
    errors = []
    for path in pages:
        relative = path.relative_to(root)
        text = path.read_text(encoding="utf-8", errors="replace")
        title_match = re.search(r"<title\b[^>]*>\s*(.*?)\s*</title\s*>", text, re.I | re.S)
        description_match = attribute(text, "meta", "name", "description")
        canonical_match = attribute(text, "link", "rel", "canonical")
        required_og = [
            attribute(text, "meta", "property", name)
            for name in ("og:title", "og:description", "og:url")
        ]
        required_twitter = [
            attribute(text, "meta", "name", name)
            for name in ("twitter:card", "twitter:title", "twitter:description")
        ]
        missing = []
        if not title_match or not re.sub(r"<[^>]+>", "", title_match.group(1)).strip():
            missing.append("title")
        if not description_match:
            missing.append("description")
        if not canonical_match:
            missing.append("canonical")
        if not all(required_og):
            missing.append("Open Graph tags")
        if not all(required_twitter):
            missing.append("Twitter tags")
        if DOI not in text or '"SoftwareApplication"' not in text or '"SoftwareSourceCode"' not in text:
            missing.append("structured data")
        if missing:
            errors.append(f"{relative}: missing {', '.join(missing)}")
            continue
        title = html.unescape(re.sub(r"<[^>]+>", "", title_match.group(1))).strip()
        description = re.search(r'\bcontent\s*=\s*["\']([^"\']+)', description_match.group(0), re.I)
        description = html.unescape(description.group(1)).strip() if description else ""
        seen_titles.setdefault(title, []).append(relative)
        seen_descriptions.setdefault(description, []).append(relative)

    for label, values in (("title", seen_titles), ("description", seen_descriptions)):
        for value, paths in values.items():
            if not value:
                errors.append(f"{paths[0]}: empty {label}")
            elif len(paths) > 1:
                errors.append(
                    f"duplicate {label} on " + ", ".join(str(path) for path in paths)
                )
    if not (root / "sitemap.xml").is_file():
        errors.append("missing sitemap.xml")
    if errors:
        raise ValueError("\n".join(errors))
    print(f"SEO metadata ok ({len(pages)} HTML pages)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("apply", "check"))
    parser.add_argument("root", type=Path)
    parser.add_argument("--base-url", default="https://rust.dseams.info/")
    args = parser.parse_args()
    try:
        if args.command == "apply":
            apply(args.root, args.base_url)
        else:
            check(args.root)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
