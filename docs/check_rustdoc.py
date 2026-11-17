#!/usr/bin/env python3
# Copyright (c) d-SEAMS developers
"""Fail when rustdoc omits a public item of dseams or dseams-sys.

Run after `cargo doc --no-deps --workspace`. The argument is the doc
directory (target/doc). Symbols come from the crate sources: public
types, functions, constants, fields, enum variants, the ffi re-export,
and the Default, Drop, and Iterator implementations.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDENT = r"[A-Za-z_][A-Za-z0-9_]*"


def strip_noise(text):
    """Blank comments and string literals, keeping newlines and braces outside them."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("//", i):
            j = text.find("\n", i)
            if j < 0:
                break
            out.append("\n")
            i = j + 1
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            if j < 0:
                j = n - 2
            chunk = text[i : j + 2]
            out.append("".join("\n" if ch == "\n" else " " for ch in chunk))
            i = j + 2
            continue
        if text[i] == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == '"':
                    j += 1
                    break
                j += 1
            chunk = text[i:j]
            out.append("".join("\n" if ch == "\n" else " " for ch in chunk))
            i = j
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def type_name(raw):
    raw = raw.strip().rstrip("{").strip()
    raw = re.sub(r"^<[^>]*>\s*", "", raw)
    raw = re.sub(r"<.*", "", raw)
    return raw.strip()


class Block:
    def __init__(self, kind, name, open_depth):
        self.kind = kind
        self.name = name
        self.open_depth = open_depth


def parse_safe(text):
    """Public surface of the safe crate."""
    items = []
    stack = []
    depth = 0
    code = strip_noise(text)
    for raw in code.splitlines():
        line = raw.strip()
        parent = stack[-1] if stack else None
        decl = None
        if parent is None or parent.kind == "root":
            found = re.match(rf"pub\s+(struct|enum)\s+({IDENT})\b", line)
            if found:
                decl = (found.group(1), found.group(2))
            elif re.match(rf"pub\s+fn\s+({IDENT})\b", line):
                decl = ("fn", re.match(rf"pub\s+fn\s+({IDENT})\b", line).group(1))
            elif re.match(rf"pub\s+use\s+{IDENT}\s+as\s+({IDENT})\s*;", line):
                decl = ("reexport", re.match(rf"pub\s+use\s+{IDENT}\s+as\s+({IDENT})\s*;", line).group(1))
        elif parent.kind == "struct" and re.match(rf"pub\s+({IDENT})\s*:", line):
            decl = ("field", (parent.name, re.match(rf"pub\s+({IDENT})\s*:", line).group(1)))
        elif parent.kind == "enum" and re.match(rf"({IDENT})\b", line):
            name = re.match(rf"({IDENT})\b", line).group(1)
            if name[:1].isupper():
                decl = ("variant", (parent.name, name))
        elif parent.kind == "variant" and re.match(rf"({IDENT})\s*:", line):
            decl = (
                "variant_field",
                (parent.name[0], parent.name[1], re.match(rf"({IDENT})\s*:", line).group(1)),
            )
        elif parent.kind == "inherent" and re.match(rf"pub\s+fn\s+({IDENT})\b", line):
            decl = ("method", (parent.name, re.match(rf"pub\s+fn\s+({IDENT})\b", line).group(1)))
        elif parent is None or parent.kind in {"root", "inherent"}:
            pass
        if line.startswith("impl"):
            body = line[len("impl") :].strip().rstrip("{").strip()
            if " for " in body:
                trait, ty = body.split(" for ", 1)
                trait = type_name(trait)
                ty = type_name(ty)
                if trait == "Default":
                    decl_trait = ("trait_method", (ty, "default"))
                elif trait == "Drop":
                    decl_trait = ("trait_method", (ty, "drop"))
                elif trait == "Iterator":
                    decl_trait = ("trait_method", (ty, "next"))
                else:
                    decl_trait = None
                if decl_trait:
                    items.append(decl_trait)
                decl = ("trait_impl", ty)
            else:
                decl = ("inherent", type_name(body))
        if decl and decl[0] not in {"trait_impl"}:
            if decl[0] != "inherent":
                items.append(decl)
        opens = raw.count("{")
        closes = raw.count("}")
        if decl and decl[0] in {"struct", "enum", "fn", "inherent", "trait_impl", "variant"} and opens:
            name = decl[1]
            stack.append(Block(decl[0], name, depth))
        depth += opens - closes
        if depth < 0:
            depth = 0
        while stack and depth <= stack[-1].open_depth:
            stack.pop()
    return items


def parse_sys(text):
    items = []
    code = strip_noise(text)
    for raw in code.splitlines():
        line = raw.strip()
        found = re.match(rf"pub\s+const\s+({IDENT})\b", line)
        if found:
            items.append(("const", found.group(1)))
            continue
        found = re.match(rf"pub\s+struct\s+({IDENT})\b", line)
        if found:
            items.append(("struct", found.group(1)))
            continue
        found = re.match(rf"pub\s+fn\s+({IDENT})\b", line)
        if found:
            items.append(("fn", found.group(1)))
    return items


def load(path):
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def check_safe(doc_dir, items):
    crate = doc_dir / "seams"
    index = load(crate / "index.html")
    pages = {}
    missing = []
    for kind, name in items:
        if kind == "struct":
            page = crate / f"struct.{name}.html"
            if not page.is_file():
                missing.append(f"struct {name}")
        elif kind == "enum":
            page = crate / f"enum.{name}.html"
            if not page.is_file():
                missing.append(f"enum {name}")
        elif kind == "fn":
            page = crate / f"fn.{name}.html"
            if not page.is_file():
                missing.append(f"fn {name}")
        elif kind == "reexport":
            if f'id="reexport.{name}"' not in index:
                missing.append(f"reexport {name}")
        elif kind == "field":
            ty, field = name
            page = pages.get(ty)
            if page is None:
                struct_page = crate / f"struct.{ty}.html"
                enum_page = crate / f"enum.{ty}.html"
                page = load(struct_page if struct_page.is_file() else enum_page)
                pages[ty] = page
            if f'id="structfield.{field}"' not in page:
                missing.append(f"field {ty}.{field}")
        elif kind == "method" or kind == "trait_method":
            ty, method = name
            page = pages.get(ty)
            if page is None:
                struct_page = crate / f"struct.{ty}.html"
                enum_page = crate / f"enum.{ty}.html"
                page = load(struct_page if struct_page.is_file() else enum_page)
                pages[ty] = page
            if f'id="method.{method}"' not in page:
                missing.append(f"method {ty}::{method}")
        elif kind == "variant":
            ty, variant = name
            page = pages.get(ty)
            if page is None:
                page = load(crate / f"enum.{ty}.html")
                pages[ty] = page
            if f'id="variant.{variant}"' not in page:
                missing.append(f"variant {ty}::{variant}")
        elif kind == "variant_field":
            ty, variant, field = name
            page = pages.get(ty)
            if page is None:
                page = load(crate / f"enum.{ty}.html")
                pages[ty] = page
            if f'id="variant.{variant}.field.{field}"' not in page:
                missing.append(f"variant field {ty}::{variant}.{field}")
        else:
            missing.append(f"unhandled {kind} {name}")
    return missing


def check_sys(doc_dir, items):
    crate = doc_dir / "seams_sys"
    missing = []
    for kind, name in items:
        if kind == "const":
            page = crate / f"constant.{name}.html"
        elif kind == "struct":
            page = crate / f"struct.{name}.html"
        elif kind == "fn":
            page = crate / f"fn.{name}.html"
        else:
            missing.append(f"unhandled {kind} {name}")
            continue
        if not page.is_file():
            missing.append(f"{kind} {name}")
    return missing


def main(argv):
    doc = Path(argv[1] if len(argv) > 1 else ROOT / "target" / "doc")
    if not (doc / "seams" / "index.html").is_file():
        print(f"missing rustdoc output: {doc}/seams/index.html", file=sys.stderr)
        return 1
    safe_items = parse_safe((ROOT / "dseams" / "src" / "lib.rs").read_text(encoding="utf-8"))
    sys_items = parse_sys((ROOT / "dseams-sys" / "src" / "lib.rs").read_text(encoding="utf-8"))
    safe_missing = check_safe(doc, safe_items)
    sys_missing = check_sys(doc, sys_items)
    safe_ok = len(safe_items) - len(safe_missing)
    sys_ok = len(sys_items) - len(sys_missing)
    print(f"seams {safe_ok}/{len(safe_items)}")
    print(f"seams_sys {sys_ok}/{len(sys_items)}")
    if safe_missing or sys_missing:
        for item in safe_missing + sys_missing:
            print(f"missing {item}", file=sys.stderr)
        return 1
    print("rustdoc coverage ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
