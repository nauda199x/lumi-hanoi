#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "lumi-signature/index.html"
IMAGE = "https://lumi-hanoi.com/assets/media/signature/penthouse/s1-floor-35.webp"
ALT = "Lumi Signature Lumi Hanoi — mặt bằng tòa S1 đại diện cho 5 tòa Signature"


def attr(tag: str, name: str) -> str | None:
    m = re.search(rf'\b{re.escape(name)}\s*=\s*(["\'])(.*?)\1', tag, re.I | re.S)
    return html.unescape(m.group(2)) if m else None


def set_meta(doc: str, selector: str, key: str, value: str) -> str:
    escaped = html.escape(value, quote=True)
    for match in re.finditer(r'<meta\b[^>]*>', doc, re.I):
        tag = match.group(0)
        if attr(tag, selector) != key:
            continue
        if re.search(r'\bcontent\s*=', tag, re.I):
            new_tag = re.sub(
                r'\bcontent\s*=\s*(["\']).*?\1',
                f'content="{escaped}"',
                tag,
                count=1,
                flags=re.I | re.S,
            )
        else:
            new_tag = tag[:-1] + f' content="{escaped}">'
        return doc[:match.start()] + new_tag + doc[match.end():]
    return doc.replace('</head>', f'<meta {selector}="{key}" content="{escaped}"></head>', 1)


def main() -> None:
    doc = PATH.read_text(encoding="utf-8")
    old = doc
    doc = set_meta(doc, "property", "og:image", IMAGE)
    doc = set_meta(doc, "property", "og:image:type", "image/webp")
    doc = set_meta(doc, "property", "og:image:width", "1980")
    doc = set_meta(doc, "property", "og:image:height", "1457")
    doc = set_meta(doc, "property", "og:image:alt", ALT)
    doc = set_meta(doc, "name", "twitter:card", "summary_large_image")
    doc = set_meta(doc, "name", "twitter:image", IMAGE)
    doc = set_meta(doc, "name", "twitter:image:alt", ALT)
    # Keep Article schema aligned with the same representative plan.
    if '"@type":"Article"' in doc and '"image":' not in doc.split('</head>', 1)[0]:
        doc = doc.replace('"inLanguage":"vi-VN",', f'"inLanguage":"vi-VN","image":"{IMAGE}",', 1)
    if doc != old:
        PATH.write_text(doc, encoding="utf-8")
        print("fixed lumi-signature/index.html")
    else:
        print("lumi-signature/index.html already aligned")


if __name__ == "__main__":
    main()
