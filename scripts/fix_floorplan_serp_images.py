#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://lumi-hanoi.com"
TOWER_PAGES = [
    "mat-bang-lumi-hanoi/lumi-signature/s1/index.html",
    "mat-bang-lumi-hanoi/lumi-signature/s2/index.html",
    "mat-bang-lumi-hanoi/lumi-signature/s3/index.html",
    "mat-bang-lumi-hanoi/lumi-signature/s5/index.html",
    "mat-bang-lumi-hanoi/lumi-signature/s6/index.html",
    "mat-bang-lumi-hanoi/lumi-prestige/p1/index.html",
    "mat-bang-lumi-hanoi/lumi-prestige/p2/index.html",
    "mat-bang-lumi-hanoi/lumi-elite/e1/index.html",
    "mat-bang-lumi-hanoi/lumi-elite/e2/index.html",
]


def get_attr(tag: str, name: str) -> str | None:
    m = re.search(rf'\b{re.escape(name)}="([^"]*)"', tag, re.I)
    return html.unescape(m.group(1)) if m else None


def get_meta(doc: str, selector: str, key: str) -> str | None:
    pattern = re.compile(rf'<meta\b(?=[^>]*\b{selector}="{re.escape(key)}")[^>]*>', re.I)
    m = pattern.search(doc)
    return get_attr(m.group(0), "content") if m else None


def set_meta(doc: str, selector: str, key: str, value: str) -> str:
    pattern = re.compile(rf'<meta\b(?=[^>]*\b{selector}="{re.escape(key)}")[^>]*>', re.I)
    m = pattern.search(doc)
    escaped = html.escape(value, quote=True)
    if m:
        tag = m.group(0)
        if re.search(r'\bcontent="[^"]*"', tag, re.I):
            new_tag = re.sub(r'\bcontent="[^"]*"', f'content="{escaped}"', tag, count=1, flags=re.I)
        else:
            new_tag = tag[:-1] + f' content="{escaped}">'
        return doc[:m.start()] + new_tag + doc[m.end():]
    return doc.replace('</head>', f'<meta {selector}="{key}" content="{escaped}"></head>', 1)


def local_src(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc not in {"lumi-hanoi.com", "www.lumi-hanoi.com"}:
        return None
    return parsed.path if parsed.path.startswith('/') else '/' + parsed.path


def image_from_tag(tag: str) -> tuple[str, str, str, str] | None:
    src = get_attr(tag, "src")
    alt = get_attr(tag, "alt")
    width = get_attr(tag, "width")
    height = get_attr(tag, "height")
    if all((src, alt, width, height)):
        return src, alt, width, height
    return None


def primary_image(doc: str) -> tuple[str, str, str, str]:
    # Signature/Prestige pages explicitly mark the preferred floor-plan section.
    section = re.search(r'<section\b[^>]*data-primary-floor-plan[^>]*>.*?</section>', doc, re.I | re.S)
    if section:
        image = re.search(r'<img\b[^>]*class="[^"]*floor-plan-image[^"]*"[^>]*>', section.group(0), re.I)
        if image:
            result = image_from_tag(image.group(0))
            if result:
                return result

    # Elite already has a verified local floor-plan as og:image/schema image, but
    # its older HTML does not carry data-primary-floor-plan. Reuse that exact asset.
    og = get_meta(doc, "property", "og:image")
    og_alt = get_meta(doc, "property", "og:image:alt")
    width = get_meta(doc, "property", "og:image:width")
    height = get_meta(doc, "property", "og:image:height")
    src = local_src(og) if og else None
    if all((src, og_alt, width, height)) and (ROOT / src.lstrip('/')).is_file():
        return src, og_alt, width, height

    raise RuntimeError("no verified local primary floor-plan image")


def replace_hero(doc: str, src: str, alt: str, width: str, height: str) -> str:
    hero = re.search(r'<header class="article-hero tower-hero">.*?</header>', doc, re.I | re.S)
    if not hero:
        raise RuntimeError("missing tower hero")
    block = hero.group(0)
    replacement = (
        f'<img class="article-hero-media tower-serp-plan" src="{src}" width="{width}" height="{height}" '
        f'alt="{html.escape(alt, quote=True)}" loading="eager" fetchpriority="high" decoding="async">'
    )
    picture = re.search(r'<picture\b[^>]*>.*?article-hero-media.*?</picture>', block, re.I | re.S)
    if picture:
        block = block[:picture.start()] + replacement + block[picture.end():]
    else:
        image = re.search(r'<img\b[^>]*class="[^"]*article-hero-media[^"]*"[^>]*>', block, re.I)
        if not image:
            raise RuntimeError("missing hero media")
        block = block[:image.start()] + replacement + block[image.end():]
    return doc[:hero.start()] + block + doc[hero.end():]


def fix_page(relative: str) -> None:
    path = ROOT / relative
    doc = path.read_text(encoding="utf-8")
    src, alt, width, height = primary_image(doc)
    absolute = SITE + src
    old_og = get_meta(doc, "property", "og:image")

    # Align all explicit social/schema references with the exact floor-plan asset.
    if old_og and old_og != absolute:
        head, tail = doc.split('</head>', 1)
        doc = head.replace(old_og, absolute) + '</head>' + tail
    doc = set_meta(doc, "property", "og:image", absolute)
    doc = set_meta(doc, "property", "og:image:type", "image/webp")
    doc = set_meta(doc, "property", "og:image:width", width)
    doc = set_meta(doc, "property", "og:image:height", height)
    doc = set_meta(doc, "property", "og:image:alt", alt)
    doc = set_meta(doc, "name", "twitter:card", "summary_large_image")
    doc = set_meta(doc, "name", "twitter:image", absolute)
    doc = set_meta(doc, "name", "twitter:image:alt", alt)

    # Google can ignore OG and pick the most prominent page image. The first hero
    # therefore uses the same floor plan rather than a generic facade/landscape.
    doc = replace_hero(doc, src, alt, width, height)

    robots = get_meta(doc, "name", "robots")
    if robots and "max-image-preview:large" not in robots:
        doc = set_meta(doc, "name", "robots", robots + ",max-image-preview:large")

    path.write_text(doc, encoding="utf-8")
    print(f"fixed {relative} -> {src}")


def main() -> None:
    for page in TOWER_PAGES:
        fix_page(page)

    css_path = ROOT / "assets/css/floor-plan-hub.css"
    css = css_path.read_text(encoding="utf-8")
    marker = "/* TOWER-SERP-PLAN:START */"
    if marker not in css:
        css += """

/* TOWER-SERP-PLAN:START */
/* The first crawlable tower image is the exact floor plan used by OG/Twitter/schema. */
.tower-hero .tower-serp-plan{object-fit:contain;object-position:center;background:#f7f4ed;opacity:.42}
@media(max-width:700px){.tower-hero .tower-serp-plan{object-fit:contain;opacity:.38}}
/* TOWER-SERP-PLAN:END */
"""
        css_path.write_text(css, encoding="utf-8")


if __name__ == "__main__":
    main()
