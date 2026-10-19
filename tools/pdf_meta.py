#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Stamp title, author, subject and keywords into a PDF with an incremental update. No dependencies."""
import re
import sys

META = {
    "Title": "From Monovalent Dev to Bivalent DevOps to Trivalent DevIntOps: "
             "Intelligence as the Third Continuous Loop in Software Engineering",
    "Author": "Pavel Chertorogov",
    "Subject": "DevIntOps, version 1.0. Canonical version: https://devintops.org/v1/",
    "Keywords": "DevIntOps; DevOps; software engineering; AI agents; continuous learning; engineering systems; self-improving systems",
}
# No /Creator on purpose: macOS Spotlight shows /Creator as the author when one is present.


def text_string(value):
    """Literal string for ASCII (read by every viewer), UTF-16BE hex with a byte order mark otherwise."""
    if value.isascii():
        return "(" + value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ")"
    return "<FEFF" + value.encode("utf-16-be").hex().upper() + ">"


def stamp(path):
    data = open(path, "rb").read()
    prev = int(re.findall(rb"startxref\s+(\d+)\s+%%EOF", data)[-1])
    trailer = re.findall(rb"trailer\s*<<(.*?)>>", data, re.S)[-1]
    size = int(re.search(rb"/Size\s+(\d+)", trailer).group(1))
    root = re.search(rb"/Root\s+(\d+\s+\d+\s+R)", trailer).group(1).decode()

    kept = {}
    old = re.search(rb"/Info\s+(\d+)\s+(\d+)\s+R", trailer)
    if old:
        body = re.search(rb"(?<!\d)" + old.group(1) + rb"\s+" + old.group(2) + rb"\s+obj\s*<<(.*?)>>\s*endobj", data, re.S)
        if body:
            for key in ("CreationDate", "Producer"):
                m = re.search(rb"/" + key.encode() + rb"\s*(\([^)]*\))", body.group(1))
                if m:
                    kept[key] = m.group(1).decode("latin-1")

    fields = "".join(f"/{k} {text_string(v)}\n" for k, v in META.items())
    fields += "".join(f"/{k} {v}\n" for k, v in kept.items())
    base = data if data.endswith(b"\n") else data + b"\n"
    obj = f"{size} 0 obj\n<<\n{fields}>>\nendobj\n".encode("latin-1")
    xref_at = len(base) + len(obj)
    xref = f"xref\n0 1\n0000000000 65535 f \n{size} 1\n{len(base):010d} 00000 n \n".encode()
    tail = (f"trailer\n<</Size {size + 1}\n/Root {root}\n/Info {size} 0 R\n/Prev {prev}>>\n"
            f"startxref\n{xref_at}\n%%EOF\n").encode()
    with open(path, "wb") as fh:
        fh.write(base + obj + xref + tail)
    print(f"stamped metadata into {path.split('/site/')[-1] if '/site/' in path else path}")


if __name__ == "__main__":
    stamp(sys.argv[1])
